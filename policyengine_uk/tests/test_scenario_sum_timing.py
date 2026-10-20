"""A sum of scenarios runs each part's modifier at the part's own time.

``Simulation`` applies a scenario before it builds its data
(``applied_before_data_load``) or after. A sum of scenarios applied at
different times, such as ``no_economic_assumptions + reform``, keeps which
modifiers belong to which time (``Scenario.parts_by_data_load``). The
simulation applies all of the sum's parameter changes, then the modifiers of
the parts applied before data load, then builds the data, and runs the other
modifiers at the end. Parameter changes rebuild the parameters, which would
discard a modifier's edits, so they come before every modifier.

Invariants:

1. Partition and order: every modifier runs exactly once, at its part's
   time. One applied before data load sees no populations; one applied after
   sees them. Within each time, modifiers run in the order added, however
   the sum is bracketed.
2. Parameter changes: a sum's parameter changes are applied once, as ``+``
   merged them (the precedence ``Scenario.apply`` gives them), before any
   modifier, so the timing of the parts changes when parameters are set but
   not their values, and a modifier applied before data load keeps its edits.
3. Backward compatibility: a sum's fields (parameter changes, dated reforms
   and the chained modifier) equal those the previous ``Scenario.__add__``
   made. A sum reads ``applied_before_data_load=True`` exactly when every part
   that changes something is applied before data load, and ``Scenario()``
   (which changes nothing) adds no part.
4. Freeze: ``no_economic_assumptions + reform``, in either order, gives the
   data and the economic assumption parameters of ``no_economic_assumptions``
   alone, and the reform's own changes, also for a URL dataset, whose cache
   it neither reads nor writes, so the baseline and later simulations keep
   current law's projection.
5. A sum is fixed when made: later edits to its operands do not reach it; a
   sum whose flag or modifier is changed is applied as one scenario, as its
   fields say; and its parts are copies.

All datasets here are MOCK data: synthetic households, not survey records.
"""

import copy
import functools
import operator

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform, set_parameter

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.model_api import YEAR, Enum, Household, Variable
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.utils.scenario import Scenario

AVERAGE_EARNINGS = "gov.economic_assumptions.yoy_growth.obr.average_earnings"
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
BASIC_RATE = "gov.hmrc.income_tax.rates.uk[0].rate"
REFORM = {PERSONAL_ALLOWANCE: {"2025.2099": 20_000}}
CURRENT_LAW_ALLOWANCE = 12_570
CURRENT_LAW_GROWTH_2027 = 0.024  # yoy_growth.obr.average_earnings for 2027
MACRO_GROWTH_2027 = 0.2
# Calendar-year growth series are keyed to 1 January.
MACRO = Scenario(
    parameter_changes={AVERAGE_EARNINGS: {"year:2027-01-01:1": MACRO_GROWTH_2027}},
    applied_before_data_load=True,
)
UPRATED_COLUMNS = {"person": ["employment_income"], "household": ["rent"]}
YEARS = range(2025, 2031)

SITUATION = {
    "people": {"person": {"age": {2025: 40}, "employment_income": {2025: 30_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

PROPERTY_SETTINGS = settings(
    max_examples=60,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
SIMULATION_PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def mock_dataset() -> UKSingleYearDataset:
    """MOCK data: two synthetic households with columns the uprating reads."""
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 2],
            "person_household_id": [1, 2],
            "age": [40, 70],
            "employment_income": [30_000.0, 0.0],
        }
    )
    benunit = pd.DataFrame({"benunit_id": [1, 2]})
    household = pd.DataFrame(
        {
            "household_id": [1, 2],
            "household_weight": [1.0, 1.0],
            "region": ["LONDON", "WALES"],
            "tenure_type": ["RENT_PRIVATELY", "OWNED_OUTRIGHT"],
            "rent": [12_000.0, 0.0],
            "council_tax": [1_500.0, 1_800.0],
        }
    )
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2025
    )


def mock_multi_year_dataset() -> UKMultiYearDataset:
    """MOCK data: one synthetic person, with 2026 already uprated."""
    person_2025 = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "employment_income": [30_000.0],
            "age": [40],
        }
    )
    person_2026 = person_2025.copy()
    person_2026["employment_income"] = [31_019.96875]
    person_2026["age"] = [41]
    benunit = pd.DataFrame({"benunit_id": [1]})
    household = pd.DataFrame({"household_id": [1]})
    return UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=person,
                benunit=benunit.copy(),
                household=household.copy(),
                fiscal_year=year,
            )
            for year, person in ((2025, person_2025), (2026, person_2026))
        ]
    )


def parameter(simulation, path, instant):
    return simulation.tax_benefit_system.parameters.get_child(path)(instant)


def growth(simulation, year=2027):
    """Employment income growth into ``year`` in the simulation's data."""
    data = simulation.dataset
    return (
        data[year].person.employment_income.iloc[0]
        / data[year - 1].person.employment_income.iloc[0]
        - 1
    )


def economic_assumptions(simulation) -> dict:
    """Every growth series and statutory uprating input, over the years."""
    node = simulation.tax_benefit_system.parameters.gov.economic_assumptions
    return {
        p.name: [p(f"{year}-01-01") for year in YEARS]
        for subtree in (node.yoy_growth, node.statutory_uprating_inputs)
        for p in subtree.get_descendants()
        if isinstance(p, Parameter)
    }


def assert_same_data(simulation, expected):
    assert list(simulation.dataset.years) == list(expected.dataset.years)
    for year in expected.dataset.years:
        for table in ("person", "benunit", "household"):
            pd.testing.assert_frame_equal(
                getattr(simulation.dataset[year], table),
                getattr(expected.dataset[year], table),
                obj=f"{table} {year}",
            )


# --- the freeze, on MOCK data ---------------------------------------------


@pytest.fixture(scope="module")
def frozen():
    return Simulation(dataset=mock_dataset(), scenario=no_economic_assumptions)


@pytest.fixture(scope="module", params=["freeze first", "reform first"])
def frozen_with_reform(request):
    reform = Scenario.from_reform(REFORM)
    scenario = (
        no_economic_assumptions + reform
        if request.param == "freeze first"
        else reform + no_economic_assumptions
    )
    return Simulation(dataset=mock_dataset(), scenario=scenario)


def test_no_economic_assumptions_plus_reform_freezes_the_data(
    frozen_with_reform, frozen
):
    simulation = frozen_with_reform
    assert simulation.disable_economic_assumptions
    # Every projected year holds the base year's uprated amounts.
    base = simulation.dataset[2025]
    for year in simulation.dataset.years:
        for table, columns in UPRATED_COLUMNS.items():
            for column in columns:
                np.testing.assert_array_equal(
                    getattr(simulation.dataset[year], table)[column],
                    getattr(base, table)[column],
                    err_msg=f"{table}.{column} {year}",
                )
    assert_same_data(simulation, frozen)
    # What the model calculates from the data, not only the stored dataset.
    for year in YEARS:
        income = simulation.calculate("employment_income_before_lsr", year)
        np.testing.assert_array_equal(income, [30_000, 0], err_msg=str(year))


def test_no_economic_assumptions_plus_reform_freezes_the_parameters(
    frozen_with_reform, frozen
):
    simulation = frozen_with_reform
    assert parameter(simulation, AVERAGE_EARNINGS, "2027-01-01") == 0
    # The freeze reloads the parameters after the reform changes them, and
    # reprocesses them with the reform's changes.
    assert economic_assumptions(simulation) == economic_assumptions(frozen)


def test_no_economic_assumptions_plus_reform_still_applies_the_reform(
    frozen_with_reform, frozen
):
    simulation = frozen_with_reform
    for year in YEARS:
        assert parameter(simulation, PERSONAL_ALLOWANCE, str(year)) == 20_000
        assert parameter(frozen, PERSONAL_ALLOWANCE, str(year)) == CURRENT_LAW_ALLOWANCE
    # Frozen income above the reformed allowance, at the basic rate: on main
    # the income had grown by 2027, so this was £2,352.90.
    income_tax = simulation.calculate("income_tax", 2027, map_to="person")
    assert income_tax[0] == pytest.approx((30_000 - 20_000) * 0.2)
    # The baseline is current law, with growth.
    baseline = simulation.baseline
    assert parameter(baseline, PERSONAL_ALLOWANCE, "2027") == CURRENT_LAW_ALLOWANCE
    assert growth(baseline) == pytest.approx(CURRENT_LAW_GROWTH_2027)


@pytest.mark.parametrize("freeze_first", [True, False])
def test_no_economic_assumptions_plus_reform_resets_a_multi_year_dataset(
    freeze_first,
):
    dataset = mock_multi_year_dataset()
    reform = Scenario.from_reform(REFORM)
    scenario = (
        no_economic_assumptions + reform
        if freeze_first
        else reform + no_economic_assumptions
    )
    simulation = Simulation(dataset=dataset, scenario=scenario)
    assert float(simulation.calculate("employment_income", 2026)[0]) == 30_000
    assert int(simulation.calculate("age", 2026)[0]) == 41
    assert parameter(simulation, PERSONAL_ALLOWANCE, "2026") == 20_000
    # The input dataset is left as it was.
    assert dataset[2026].person["employment_income"].iloc[0] == 31_019.96875


def test_no_economic_assumptions_plus_reform_freezes_a_situation():
    simulation = Simulation(
        situation=SITUATION,
        scenario=no_economic_assumptions + Scenario.from_reform(REFORM),
    )
    # Before the labour supply response, which compares with the baseline.
    income = [
        float(simulation.calculate("employment_income_before_lsr", year)[0])
        for year in YEARS
    ]
    assert income == [30_000.0] * len(income)
    assert parameter(simulation, PERSONAL_ALLOWANCE, "2027") == 20_000


# --- other parts applied before data load ---------------------------------


def test_before_load_parameter_changes_in_a_sum_reach_the_data():
    """The documented macro route keeps its timing when a reform is added."""
    macro = Simulation(dataset=mock_dataset(), scenario=MACRO)
    for scenario in (
        MACRO + Scenario.from_reform(REFORM),
        Scenario.from_reform(REFORM) + MACRO,
    ):
        simulation = Simulation(dataset=mock_dataset(), scenario=scenario)
        # On main the sum was applied after data load: 2.4%.
        assert growth(simulation) == pytest.approx(MACRO_GROWTH_2027)
        assert_same_data(simulation, macro)
        assert parameter(simulation, PERSONAL_ALLOWANCE, "2027") == 20_000


def test_a_sum_of_scenarios_applied_before_data_load_is_applied_before_it():
    seen = []

    def record(simulation):
        seen.append(getattr(simulation, "populations", None) is None)

    scenario = MACRO + Scenario(
        simulation_modifier=record, applied_before_data_load=True
    )
    assert scenario.applied_before_data_load
    assert scenario.parts_by_data_load() == (scenario, None)
    simulation = Simulation(dataset=mock_dataset(), scenario=scenario)
    assert seen == [True]
    assert growth(simulation) == pytest.approx(MACRO_GROWTH_2027)


# --- a modifier applied after data load still sees the data ---------------


def give_pensions(simulation):
    """A data-editing modifier: it reads the populations, so it can only run
    once the data is built."""
    income = simulation.calculate("employment_income_before_lsr", 2025)
    simulation.set_input("private_pension_income", 2027, income / 10)


@pytest.mark.parametrize("freeze_first", [True, False])
def test_an_after_load_data_editing_modifier_in_a_sum_sees_the_data(freeze_first):
    edit = Scenario(simulation_modifier=give_pensions)
    scenario = (
        no_economic_assumptions + edit
        if freeze_first
        else edit + no_economic_assumptions
    )
    before, after = scenario.parts_by_data_load()
    assert before.simulation_modifier is not None
    assert after.simulation_modifier is give_pensions
    simulation = Simulation(dataset=mock_dataset(), scenario=scenario)
    pensions = simulation.calculate("private_pension_income", 2027, map_to="person")
    np.testing.assert_array_equal(pensions, [3_000, 0])
    assert growth(simulation) == 0
    assert simulation.disable_economic_assumptions


def test_flagging_the_whole_sum_would_run_the_data_edit_without_data():
    """Why a sum keeps each part's timing rather than one flag: the edit
    needs populations that do not exist before data load."""
    scenario = no_economic_assumptions + Scenario(simulation_modifier=give_pensions)
    scenario.applied_before_data_load = True
    with pytest.raises(AttributeError, match="populations"):
        Simulation(dataset=mock_dataset(), scenario=scenario)


# --- a sum with a URL dataset ---------------------------------------------

HF_URL = "hf://policyengine/mock-repo/MOCK_frs_2025_26.h5"
GCS_URL = "gs://mock-bucket/MOCK_frs_2025_26.h5"


@pytest.fixture
def url_dataset(monkeypatch, tmp_path):
    """Serve both URL schemes from a MOCK file, with an empty cache."""
    path = str(tmp_path / "MOCK_frs_2025_26.h5")
    mock_dataset().save(path)
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    monkeypatch.setattr(
        simulation_module, "download_huggingface_dataset", lambda **_: path
    )
    monkeypatch.setattr(
        simulation_module, "materialize_gcs_dataset_url", lambda url, **_: path
    )


@pytest.mark.parametrize("url", [HF_URL, GCS_URL])
@pytest.mark.parametrize("scenario_first", [True, False])
def test_a_sum_with_a_before_load_part_keeps_out_of_the_url_dataset_cache(
    url_dataset, url, scenario_first
):
    if not scenario_first:
        assert growth(Simulation(dataset=url)) == pytest.approx(CURRENT_LAW_GROWTH_2027)
    frozen = Simulation(
        dataset=url, scenario=no_economic_assumptions + Scenario.from_reform(REFORM)
    )
    assert growth(frozen) == 0
    assert parameter(frozen, PERSONAL_ALLOWANCE, "2027") == 20_000
    # On main the frozen data was cached under the URL: the baseline and
    # every later simulation got it.
    for simulation in (frozen.baseline, Simulation(dataset=url)):
        assert growth(simulation) == pytest.approx(CURRENT_LAW_GROWTH_2027)


def test_a_macro_sum_with_a_url_dataset_projects_its_own_data(url_dataset):
    Simulation(dataset=GCS_URL)
    macro = Simulation(dataset=GCS_URL, scenario=MACRO + Scenario.from_reform(REFORM))
    assert growth(macro) == pytest.approx(MACRO_GROWTH_2027)
    assert growth(Simulation(dataset=GCS_URL)) == pytest.approx(CURRENT_LAW_GROWTH_2027)


class ReorderedTenure(Enum):
    """MOCK: tenure_type's members in another order."""

    OWNED_OUTRIGHT = "Owned outright"
    OWNED_WITH_MORTGAGE = "Owned with a mortgage"
    RENT_FROM_COUNCIL = "Rented from Council"
    RENT_FROM_HA = "Rented from a Housing Association"
    RENT_PRIVATELY = "Rented privately"


class tenure_type(Variable):
    value_type = Enum
    possible_values = ReorderedTenure
    default_value = ReorderedTenure.RENT_PRIVATELY
    entity = Household
    label = "Tenure type of the household"
    definition_period = YEAR


class reorder_tenure(Reform):
    """A MOCK structural reform that changes no parameter."""

    def apply(self):
        self.update_variable(tenure_type)


def test_a_before_load_structural_reform_keeps_out_of_the_url_dataset_cache(
    url_dataset,
):
    """The cached dataset's enum columns are encoded with the system that
    built it, so a part applied before data load keeps out of the cache even
    when it changes no parameter the projection reads."""
    part = Scenario.from_reform(reorder_tenure).model_copy(
        update={"applied_before_data_load": True}
    )
    reformed = Simulation(dataset=GCS_URL, scenario=part)
    assert reformed.calculate("tenure_type", 2025)[0] == "RENT_PRIVATELY"
    later = Simulation(dataset=GCS_URL)
    assert later.calculate("tenure_type", 2025)[0] == "RENT_PRIVATELY"


# --- parameter changes come before every modifier -------------------------


def zero_allowance_directly(simulation):
    """A modifier that edits the processed parameters directly, which a
    rebuild of the parameters would discard."""
    simulation.tax_benefit_system.parameters.get_child(PERSONAL_ALLOWANCE).update(
        period=period_("year:2026:1"), value=0
    )
    simulation.tax_benefit_system.reset_parameter_caches()


def zero_allowance(before):
    """MOCK reform parts that set the allowance to 0 in 2026 by editing the
    processed parameters: a modifier, and a structural Reform class."""
    return {
        "modifier": Scenario(
            simulation_modifier=zero_allowance_directly,
            applied_before_data_load=before,
        ),
        "reform class": Scenario.from_reform(
            set_parameter(PERSONAL_ALLOWANCE, 0, period="year:2026:1")
        ).model_copy(update={"applied_before_data_load": before}),
    }


@pytest.mark.parametrize("kind", ["modifier", "reform class"])
@pytest.mark.parametrize("before_first", [True, False])
def test_a_before_load_parts_edits_survive_an_after_load_reform(kind, before_first):
    rate = Scenario.from_reform({BASIC_RATE: {"2025.2099": 0.25}})
    part = zero_allowance(before=True)[kind]
    scenario = part + rate if before_first else rate + part
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, PERSONAL_ALLOWANCE, "2026-06-01") == 0
    assert parameter(simulation, BASIC_RATE, "2026-06-01") == 0.25
    # The same parts all applied after data load, as main applied any sum.
    after = zero_allowance(before=False)[kind]
    reference = Simulation(
        situation=SITUATION, scenario=after + rate if before_first else rate + after
    )
    assert simulation.calculate("income_tax", 2026)[0] == pytest.approx(
        reference.calculate("income_tax", 2026)[0]
    )


@pytest.mark.parametrize(
    "parts, expected",
    [
        ((True, {"2025": 15_000}), (False, {"2025": 20_000})),
        ((False, {"2025": 20_000}), (True, {"2025": 15_000})),
    ],
)
def test_a_sums_parameter_changes_keep_the_precedence_of_plus(parts, expected):
    """Timing changes when a sum's parameter changes are applied, not which
    of them holds: the later operand's, as ``+`` merges them."""
    (first_before, first), (second_before, second) = parts, expected
    timed = Scenario(
        parameter_changes={PERSONAL_ALLOWANCE: first},
        applied_before_data_load=first_before,
    ) + Scenario(
        parameter_changes={PERSONAL_ALLOWANCE: second},
        applied_before_data_load=second_before,
    )
    untimed = Scenario(parameter_changes={PERSONAL_ALLOWANCE: first}) + Scenario(
        parameter_changes={PERSONAL_ALLOWANCE: second}
    )
    for scenario in (timed, untimed):
        simulation = Simulation(situation=SITUATION, scenario=scenario)
        assert parameter(simulation, PERSONAL_ALLOWANCE, "2025") == second["2025"]


def test_a_mixed_sums_parameter_changes_all_reach_the_data():
    """Intended: with a part applied before data load, every parameter change
    of the sum comes before the data is built, an after-load part's growth
    change included."""
    record = Scenario(simulation_modifier=lambda s: None, applied_before_data_load=True)
    growth_change = Scenario(
        parameter_changes={AVERAGE_EARNINGS: {"year:2027-01-01:1": MACRO_GROWTH_2027}}
    )
    simulation = Simulation(dataset=mock_dataset(), scenario=record + growth_change)
    assert growth(simulation) == pytest.approx(MACRO_GROWTH_2027)


# --- the split, in a real simulation --------------------------------------


@st.composite
def timed_modifier_parts(draw):
    """Parts that each record, when their modifier runs, whether the data had
    been built and the allowance a parameter change of every part set."""
    timings = draw(st.lists(st.booleans(), min_size=1, max_size=5))
    events = []
    parts = []
    for index, before in enumerate(timings):

        def record(simulation, index=index):
            events.append(
                (
                    index,
                    getattr(simulation, "populations", None) is not None,
                    parameter(simulation, PERSONAL_ALLOWANCE, "2025"),
                )
            )

        parts.append(
            Scenario(
                parameter_changes={PERSONAL_ALLOWANCE: {"2025": 10_000 + index}},
                simulation_modifier=record,
                applied_before_data_load=before,
            )
        )
    return timings, parts, events


@SIMULATION_PROPERTY_SETTINGS
@given(timed_modifier_parts())
def test_a_simulation_runs_each_part_once_at_its_own_time(drawn):
    timings, parts, events = drawn
    Simulation(situation=SITUATION, scenario=functools.reduce(operator.add, parts))
    before = [i for i, b in enumerate(timings) if b]
    after = [i for i, b in enumerate(timings) if not b]
    # Every modifier sees every part's parameter change, the last one added
    # holding.
    allowance = 10_000 + len(timings) - 1
    assert events == [(i, False, allowance) for i in before] + [
        (i, True, allowance) for i in after
    ]


def test_scenario_apply_runs_every_part_of_a_sum_on_a_built_simulation():
    calls = []
    scenario = (
        Scenario(
            simulation_modifier=lambda s: calls.append("before"),
            applied_before_data_load=True,
        )
        + Scenario.from_reform({BASIC_RATE: 0.21})
        + Scenario(simulation_modifier=lambda s: calls.append("after"))
    )
    simulation = Simulation(situation=SITUATION)
    scenario.apply(simulation)
    assert calls == ["before", "after"]
    assert parameter(simulation, BASIC_RATE, "2027") == 0.21


# --- a sum is fixed when made ---------------------------------------------


def recorder(log, name):
    return lambda simulation: log.append(name)


def test_edits_to_an_operand_after_adding_do_not_reach_the_sum():
    log = []
    first = Scenario(simulation_modifier=recorder(log, "first"))
    second = Scenario(
        simulation_modifier=recorder(log, "second"), applied_before_data_load=True
    )
    scenario = first + second
    first.applied_before_data_load = True
    first.simulation_modifier = recorder(log, "replaced")
    before, after = scenario.parts_by_data_load()
    before.simulation_modifier(None)
    after.simulation_modifier(None)
    scenario.simulation_modifier(None)
    assert log == ["second", "first", "first", "second"]


def test_a_sum_flagged_before_data_load_is_applied_before_it_whole():
    scenario = Scenario.from_reform(REFORM) + no_economic_assumptions
    assert scenario.parts_by_data_load()[0] is not scenario
    scenario.applied_before_data_load = True
    assert scenario.parts_by_data_load() == (scenario, None)
    copied = (Scenario.from_reform(REFORM) + no_economic_assumptions).model_copy(
        update={"applied_before_data_load": True}
    )
    assert copied.parts_by_data_load() == (copied, None)


def test_a_sum_applies_its_current_parameter_changes():
    scenario = no_economic_assumptions + Scenario(
        parameter_changes={PERSONAL_ALLOWANCE: 20_000}
    )
    scenario.parameter_changes[BASIC_RATE] = 0.21
    before, after = scenario.parts_by_data_load()
    assert before.parameter_changes == {PERSONAL_ALLOWANCE: 20_000, BASIC_RATE: 0.21}
    assert before.simulation_modifier is not None
    assert after is None  # No part applied after data load has a modifier.
    # A sum whose modifier is replaced is applied as one scenario.
    scenario.simulation_modifier = recorder([], "replaced")
    assert scenario.parts_by_data_load() == (None, scenario)


def test_parts_by_data_load_returns_copies():
    scenario = no_economic_assumptions + Scenario.from_reform(
        {PERSONAL_ALLOWANCE: {"2026": 1}}
    )
    before, _ = scenario.parts_by_data_load()
    before.dated_reforms[0].changes[PERSONAL_ALLOWANCE]["2026"] = 999
    assert scenario.dated_reforms[0].changes[PERSONAL_ALLOWANCE]["2026"] == 1
    before, _ = scenario.parts_by_data_load()
    assert before.dated_reforms[0].changes[PERSONAL_ALLOWANCE]["2026"] == 1


def test_a_mixed_sum_survives_copying():
    log = []
    callable_object = functools.partial(lambda name, simulation: log.append(name), "x")
    sums = [
        no_economic_assumptions + Scenario.from_reform(REFORM),
        # The sum's own modifier is then a callable object, which a deep copy
        # copies.
        MACRO + Scenario(simulation_modifier=callable_object),
        Scenario(simulation_modifier=callable_object, applied_before_data_load=True)
        + Scenario(parameter_changes={PERSONAL_ALLOWANCE: 20_000}),
    ]
    for scenario in sums:
        expected = [part is not None for part in scenario.parts_by_data_load()]
        for copied in (
            scenario.model_copy(),
            scenario.model_copy(deep=True),
            copy.deepcopy(scenario),
        ):
            before, after = copied.parts_by_data_load()
            assert before is not None and before.applied_before_data_load
            assert [part is not None for part in (before, after)] == expected


# --- properties of the split, without a simulation ------------------------

PATHS = ["a.x", "a.y", "b.z"]


def reference_add(self: Scenario, other: Scenario) -> Scenario:
    """The fields ``Scenario.__add__`` made before parts kept their timing."""
    merged_params = {}
    if self.parameter_changes:
        merged_params.update(self.parameter_changes)
    if other.parameter_changes:
        for key, value in other.parameter_changes.items():
            if (
                key in merged_params
                and isinstance(merged_params[key], dict)
                and isinstance(value, dict)
            ):
                merged_params[key] = {**merged_params[key], **value}
            else:
                merged_params[key] = value
    combined_modifier = None
    if self.simulation_modifier and other.simulation_modifier:

        def combined_modifier(simulation):
            self.simulation_modifier(simulation)
            other.simulation_modifier(simulation)

    elif self.simulation_modifier:
        combined_modifier = self.simulation_modifier
    elif other.simulation_modifier:
        combined_modifier = other.simulation_modifier
    dated_reforms = (self.dated_reforms or []) + (other.dated_reforms or [])
    return Scenario(
        parameter_changes=merged_params if merged_params else None,
        dated_reforms=dated_reforms or None,
        simulation_modifier=combined_modifier,
    )


changes = st.one_of(
    st.none(),
    st.dictionaries(
        st.sampled_from(PATHS),
        st.one_of(
            st.integers(0, 9),
            st.dictionaries(st.sampled_from(["2025", "2026"]), st.integers(0, 9)),
        ),
        max_size=2,
    ),
)


@st.composite
def leaves(draw):
    """Scenarios that each record their label when their modifier runs, with
    some that change nothing."""
    specs = draw(
        st.lists(
            st.tuples(st.booleans(), st.booleans(), changes, st.booleans()),
            min_size=1,
            max_size=6,
        )
    )
    log = []
    scenarios = []
    for index, (before, has_modifier, parameter_changes, dated) in enumerate(specs):
        scenarios.append(
            Scenario(
                applied_before_data_load=before,
                parameter_changes=parameter_changes,
                dated_reforms=(
                    [{"reading": "reform_dict", "changes": {f"c.{index}": index}}]
                    if dated
                    else None
                ),
                simulation_modifier=recorder(log, index) if has_modifier else None,
            )
        )
    return scenarios, log


def changes_something(scenario):
    return bool(
        scenario.parameter_changes
        or scenario.dated_reforms
        or scenario.simulation_modifier
    )


def draw_tree(draw, low, high):
    """A random bracketing of the leaves numbered low to high - 1."""
    if high - low == 1:
        return low
    cut = draw(st.integers(low + 1, high - 1))
    return (draw_tree(draw, low, cut), draw_tree(draw, cut, high))


def evaluate(tree, leaf, add):
    """Add up a bracketing."""
    if isinstance(tree, int):
        return leaf(tree)
    first, second = (evaluate(branch, leaf, add) for branch in tree)
    return add(first, second)


def run(log, scenario):
    """The labels a scenario's modifier records."""
    del log[:]
    if scenario is not None and scenario.simulation_modifier is not None:
        scenario.simulation_modifier(None)
    return list(log)


def fields(scenario):
    """Parameter changes and dated reforms; empty and None alike mean none."""
    if scenario is None:
        return None, None
    return scenario.parameter_changes or None, scenario.dated_reforms or None


@PROPERTY_SETTINGS
@given(leaves(), st.data())
def test_a_sum_splits_its_modifiers_by_timing(drawn, data):
    scenarios, log = drawn
    count = len(scenarios)
    trees = [
        functools.reduce(lambda tree, i: (tree, i), range(1, count), 0),
        functools.reduce(
            lambda tree, i: (i, tree), range(count - 2, -1, -1), count - 1
        ),
        draw_tree(data.draw, 0, count),
    ]
    active = [changes_something(s) for s in scenarios]
    before_labels = [
        i
        for i, s in enumerate(scenarios)
        if active[i] and s.applied_before_data_load and s.simulation_modifier
    ]
    after_labels = [
        i
        for i, s in enumerate(scenarios)
        if active[i] and not s.applied_before_data_load and s.simulation_modifier
    ]
    has_before = any(
        a and s.applied_before_data_load for a, s in zip(active, scenarios)
    )
    has_after = any(
        a and not s.applied_before_data_load for a, s in zip(active, scenarios)
    )
    mixed = count > 1 and has_before and has_after

    for tree in trees:
        total = evaluate(tree, lambda i: scenarios[i], operator.add)
        before, after = total.parts_by_data_load()
        # 3. Backward compatibility: the fields hold the whole sum, as the
        # previous ``+`` made them, bracketed the same way.
        reference = evaluate(tree, lambda i: scenarios[i], reference_add)
        assert fields(total) == fields(reference)
        assert run(log, total) == run(log, reference)
        assert total.applied_before_data_load == (
            count > 1
            and has_before
            and not has_after
            or count == 1
            and scenarios[0].applied_before_data_load
        )
        if not mixed:
            # One timing: the scenario is applied whole, at that time.
            expected = (
                (total, None) if total.applied_before_data_load else (None, total)
            )
            assert (before, after) == expected
            continue
        # 1. Partition and order: each time runs exactly its parts'
        # modifiers, in the order added, however the sum is bracketed.
        assert run(log, before) == before_labels
        assert run(log, after) == after_labels
        assert before.applied_before_data_load
        assert after is None or not after.applied_before_data_load
        assert (after is None) == (not after_labels)
        # 2. Parameter changes: all of them, as ``+`` merged them, come with
        # the part applied before data load.
        assert fields(before) == fields(total)
        assert fields(after) == (None, None)
        # 3. Identity: Scenario() adds no part.
        for padded in (Scenario() + total, total + Scenario()):
            pad_before, pad_after = padded.parts_by_data_load()
            assert fields(pad_before) == fields(before)
            assert run(log, pad_before) == before_labels
            assert run(log, pad_after) == after_labels


@PROPERTY_SETTINGS
@given(leaves())
def test_a_sum_of_one_timing_is_unchanged_but_for_its_flag(drawn):
    scenarios, log = drawn
    for before in (True, False):
        same = [
            s.model_copy(update={"applied_before_data_load": before}) for s in scenarios
        ]
        total = functools.reduce(operator.add, same, Scenario())
        reference = functools.reduce(reference_add, same, Scenario())
        assert fields(total) == fields(reference)
        assert run(log, total) == run(log, reference)
        if any(changes_something(s) for s in same):
            assert total.applied_before_data_load == before
            expected = (total, None) if before else (None, total)
            assert total.parts_by_data_load() == expected

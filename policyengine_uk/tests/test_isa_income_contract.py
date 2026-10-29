"""Synthetic UK data preserve legacy ISA cash and exemption accounting.

The public v1 adapter contract is specified independently of its implementation
in issue-2584-evidence/data-contract/interface.json. No private data is used.
"""

from copy import deepcopy
import json

import h5py
import numpy as np
import pandas as pd
import pytest
from policyengine_core.data import Dataset
from policyengine_core.simulations import SimulationBuilder

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.data.filter_dataset import filter_dataset
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
KEY = "policyengine_uk.isa_income_contract"
LEGACY = {"version": 1, "representation": "legacy_gross", "projection": "legacy_gross"}
NORMALIZED = {"version": 1, "representation": "additive", "projection": "legacy_gross"}
ADDITIVE = {"version": 1, "representation": "additive", "projection": "additive"}
GDP_GROWTH = "gov.economic_assumptions.yoy_growth.obr.per_capita.gdp"
MACRO = Scenario(
    parameter_changes={
        GDP_GROWTH: {"year:2026-01-01:1": 0.1, "year:2027-01-01:1": 0.2}
    },
    applied_before_data_load=True,
)


def single(year=2025, contract=None, **income):
    person = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "age": [35],
            "employment_income": [30_000.0],
            **{name: [value] for name, value in income.items()},
        }
    )
    kwargs = {} if contract is None else {"isa_income_contract": deepcopy(contract)}
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["RENT_PRIVATELY"],
                "council_tax": [1_500.0],
                "rent": [12_000.0],
                "household_weight": [1.0],
            }
        ),
        fiscal_year=year,
        **kwargs,
    )


def input_frame(dataset):
    year = dataset.time_period
    return pd.DataFrame(
        {
            f"{name}__{year}": table[name].values
            for table in dataset.tables
            for name in table.columns
        }
    )


def core_file(dataset, path, marker=None):
    with h5py.File(path, "w") as output:
        for name, values in dataset.load().items():
            values = np.asarray(values)
            possible_values = getattr(system.variables[name], "possible_values", None)
            if possible_values is not None:
                values = np.asarray(possible_values.encode(values))
            output.create_dataset(f"{name}/{dataset.time_period}", data=values)
        if marker is not None:
            output.attrs[KEY] = json.dumps(marker)
    return Dataset.from_file(str(path))


def value(simulation, name, year=2025):
    return float(simulation.calculate(name, year)[0])


@pytest.mark.parametrize(
    "income, expected_n, expected_t, expected_taxable",
    [
        (
            {
                "savings_interest_income": 3_000,
                "individual_savings_account_interest_income": 500,
            },
            2_500,
            500,
            2_500,
        ),
        (
            {
                "savings_interest_income": 3_000,
                "individual_savings_account_interest_income": 500,
                "tax_free_savings_income": 0,
            },
            3_000,
            0,
            3_000,
        ),
        (
            {
                "savings_interest_income": 100,
                "individual_savings_account_interest_income": 500,
                "tax_free_savings_income": 300,
                "other_investment_income": 500,
            },
            -200,
            300,
            300,
        ),
        (
            {"savings_interest_income": 3_000, "tax_free_savings_income": 700},
            2_300,
            700,
            2_300,
        ),
    ],
    ids=["default-from-I", "explicit-zero-T", "signed-and-T-differs-from-I", "T-only"],
)
def test_unmarked_legacy_conversion_preserves_cash_and_supplied_exemptions(
    income, expected_n, expected_t, expected_taxable
):
    dataset = single(**income)
    original = dataset.person.copy(deep=True)
    simulation = Simulation(dataset=dataset)

    assert value(simulation, "savings_interest_income") == expected_n
    assert value(simulation, "tax_free_savings_income") == expected_t
    assert value(
        simulation, "individual_savings_account_interest_income"
    ) == income.get("individual_savings_account_interest_income", 0)
    # Capital income is the legacy gross interest plus other investment income.
    assert value(simulation, "capital_income") == (
        income["savings_interest_income"] + income.get("other_investment_income", 0)
    )
    assert value(simulation, "taxable_savings_interest_income") == expected_taxable
    pd.testing.assert_frame_equal(dataset.person, original)


@pytest.mark.parametrize(
    "route", ["single", "multi", "frame", "uk-h5", "core-h5", "core-object"]
)
def test_unmarked_supported_sources_share_the_same_legacy_interpretation(
    route, tmp_path
):
    dataset = single(
        savings_interest_income=3_000, individual_savings_account_interest_income=500
    )
    if route == "single":
        source = dataset
    elif route == "multi":
        source = UKMultiYearDataset(datasets=[dataset])
    elif route == "frame":
        source = input_frame(dataset)
    elif route == "uk-h5":
        source = tmp_path / "legacy-uk.h5"
        dataset.save(str(source))
        # Old files had no marker. Remove any default written by a new writer.
        with h5py.File(source, "a") as output:
            if KEY in output.attrs:
                del output.attrs[KEY]
    else:
        core = core_file(dataset, tmp_path / "legacy-core.h5")
        source = core if route == "core-object" else core.file_path
    simulation = Simulation(dataset=source)
    assert value(simulation, "savings_interest_income") == 2_500
    assert value(simulation, "capital_income") == 3_000
    assert value(simulation, "taxable_savings_interest_income") == 2_500


def test_marked_additive_data_and_direct_households_keep_nonisa_interest():
    income = {
        "savings_interest_income": 2_000,
        "individual_savings_account_interest_income": 500,
        "tax_free_savings_income": 700,
        "individual_savings_account_dividend_income": 300,
    }
    dataset = single(contract=ADDITIVE, **income)
    source_frame = input_frame(dataset)
    source_frame.attrs[KEY] = deepcopy(ADDITIVE)
    situation = {
        "people": {
            "person": {"age": {2025: 35}, **{k: {2025: v} for k, v in income.items()}}
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    for source in (dataset, source_frame):
        simulation = Simulation(dataset=source)
        assert value(simulation, "savings_interest_income") == 2_000
        assert value(simulation, "taxable_savings_interest_income") == 2_000
        assert value(simulation, "capital_income") == 3_000
    direct = Simulation(situation=situation)
    assert value(direct, "taxable_savings_interest_income") == 2_000
    assert value(direct, "capital_income") == 3_000


def test_normalized_legacy_survives_export_reload_copy_clone_and_reprojection(tmp_path):
    original = single(
        savings_interest_income=3_000, individual_savings_account_interest_income=500
    )
    simulation = Simulation(dataset=original, scenario=MACRO)
    assert value(simulation, "savings_interest_income", 2026) == pytest.approx(
        2_800, abs=0.01
    )
    exported = simulation.to_input_dataframe()
    assert exported.attrs[KEY]["years"]["2026"] == NORMALIZED
    reloaded = Simulation(dataset=exported, scenario=MACRO)
    for copied in (simulation.clone(), simulation.get_branch("isa-contract"), reloaded):
        assert value(copied, "savings_interest_income", 2026) == pytest.approx(
            2_800, abs=0.01
        )
        assert value(copied, "capital_income", 2026) == pytest.approx(3_300, abs=0.01)
    observed_2026 = UKSingleYearDataset.from_simulation(simulation, fiscal_year=2026)
    assert observed_2026.isa_income_contract == NORMALIZED
    copied = observed_2026.copy()
    assert copied.isa_income_contract == NORMALIZED
    copied.isa_income_contract["projection"] = "additive"
    assert observed_2026.isa_income_contract == NORMALIZED
    path = tmp_path / "normalized.h5"
    observed_2026.save(str(path))
    with h5py.File(path, "r") as stored:
        assert json.loads(stored.attrs[KEY]) == NORMALIZED
        assert KEY not in stored
    saved = UKSingleYearDataset(path)
    projected_again = Simulation(dataset=saved, scenario=MACRO)
    # Gross3300*1.2, then subtract unchanged legacy exemption500.
    assert value(projected_again, "savings_interest_income", 2027) == pytest.approx(
        3_460, abs=0.01
    )


def test_mixed_year_contracts_survive_multi_h5_and_dataframe_round_trips(tmp_path):
    legacy = single(
        savings_interest_income=3_000, individual_savings_account_interest_income=500
    )
    additive = single(
        2026,
        contract=ADDITIVE,
        savings_interest_income=4_000,
        individual_savings_account_interest_income=600,
    )
    dataset = UKMultiYearDataset(datasets=[legacy, additive])
    expected = {"version": 1, "years": {"2025": LEGACY, "2026": ADDITIVE}}
    assert dataset.isa_income_contract == expected
    path = tmp_path / "mixed.h5"
    dataset.save(str(path))
    with h5py.File(path, "r") as stored:
        assert json.loads(stored.attrs[KEY]) == expected
    simulation = Simulation(dataset=path)
    frame = simulation.to_input_dataframe()
    contracts = frame.attrs[KEY]
    assert set(contracts) == {"version", "years"}
    assert contracts["version"] == 1
    assert contracts["years"]["2025"] == NORMALIZED
    assert contracts["years"]["2026"] == ADDITIVE
    # Existing UC rebalancing records inputs beyond the two supplied years.
    # Every exported annual input year needs its own contract, including
    # those added years; later ones inherit the latest additive origin.
    exported_years = {
        column.rsplit("__", 1)[1]
        for column in frame.columns
        if column.rsplit("__", 1)[1].isdigit()
    }
    assert set(contracts["years"]) == exported_years
    for year in exported_years - {"2025", "2026"}:
        assert int(year) > 2026
        assert contracts["years"][year] == ADDITIVE
    reloaded = Simulation(dataset=frame)
    assert value(reloaded, "savings_interest_income", 2025) == 2_500
    assert value(reloaded, "savings_interest_income", 2026) == 4_000
    assert value(reloaded, "capital_income", 2026) == 4_600


def test_no_economic_assumptions_resets_legacy_gross_before_each_year_exemption():
    dataset = UKMultiYearDataset(
        datasets=[
            single(
                savings_interest_income=3_000,
                individual_savings_account_interest_income=500,
                tax_free_savings_income=700,
            ),
            single(
                2026,
                savings_interest_income=6_000,
                individual_savings_account_interest_income=900,
                tax_free_savings_income=1_200,
            ),
        ]
    )
    simulation = Simulation(dataset=dataset, scenario=no_economic_assumptions)
    # The old reset froze mapped gross interest but retained the explicit,
    # unindexed exemption for each supplied year:3000-1200=1800.
    assert value(simulation, "savings_interest_income", 2026) == 1_800
    assert value(simulation, "tax_free_savings_income", 2026) == 1_200
    assert value(simulation, "individual_savings_account_interest_income", 2026) == 900
    assert value(simulation, "capital_income", 2026) == 3_000
    assert dataset[2026].person["savings_interest_income"].iloc[0] == 6_000


@pytest.mark.parametrize(
    "contract",
    [
        {"version": 2, "representation": "additive", "projection": "additive"},
        {"version": True, "representation": "additive", "projection": "additive"},
        {"version": 1, "representation": "legacy_gross", "projection": "additive"},
        {"version": 1, "projection": "additive"},
        {**ADDITIVE, "extra": "unrecognized"},
    ],
)
def test_unknown_or_ambiguous_contracts_fail_closed(contract):
    with pytest.raises(ValueError, match="ISA income contract"):
        single(contract=contract, savings_interest_income=2_000)


@pytest.mark.parametrize(
    "marker", ["not JSON", "null", json.dumps({"version": 1, "years": {}})]
)
def test_present_invalid_h5_marker_is_not_treated_as_absent(marker, tmp_path):
    dataset = single(
        savings_interest_income=3_000, individual_savings_account_interest_income=500
    )
    path = tmp_path / "invalid.h5"
    dataset.save(str(path))
    with h5py.File(path, "a") as output:
        output.attrs[KEY] = marker
    with pytest.raises(ValueError, match="ISA income contract"):
        Simulation(dataset=path)


def test_explicit_object_and_file_markers_must_agree(tmp_path):
    dataset = single(
        savings_interest_income=2_000, individual_savings_account_interest_income=500
    )
    core = core_file(dataset, tmp_path / "conflict.h5", marker=ADDITIVE)
    core.isa_income_contract = deepcopy(LEGACY)
    with pytest.raises(ValueError, match="ISA income contract"):
        Simulation(dataset=core)


@pytest.mark.parametrize(
    "name",
    [
        "savings_interest_income",
        "individual_savings_account_interest_income",
        "tax_free_savings_income",
    ],
)
def test_nonfinite_legacy_conversion_inputs_are_rejected(name):
    income = {
        "savings_interest_income": 3_000,
        "individual_savings_account_interest_income": 500,
    }
    income[name] = np.inf
    with pytest.raises(ValueError, match="ISA income contract"):
        Simulation(dataset=single(**income))


@pytest.mark.parametrize(
    "explicit_t, expected_t, expected_cash", [(None, 550, 2_750), (700, 700, 2_900)]
)
def test_new_additive_projection_grows_nonisa_and_isa_interest_without_changing_explicit_T(
    explicit_t, expected_t, expected_cash
):
    income = {
        "savings_interest_income": 2_000,
        "individual_savings_account_interest_income": 500,
    }
    if explicit_t is not None:
        income["tax_free_savings_income"] = explicit_t
    simulation = Simulation(dataset=single(contract=ADDITIVE, **income), scenario=MACRO)
    assert value(simulation, "savings_interest_income", 2026) == pytest.approx(
        2_200, abs=0.01
    )
    assert value(
        simulation, "individual_savings_account_interest_income", 2026
    ) == pytest.approx(550, abs=0.01)
    assert value(simulation, "tax_free_savings_income", 2026) == pytest.approx(
        expected_t, abs=0.01
    )
    assert value(simulation, "capital_income", 2026) == pytest.approx(
        expected_cash, abs=0.01
    )


@pytest.mark.parametrize(
    "future_inputs, expected_n, expected_i, expected_t, expected_cash",
    [
        ({}, 5_500, 500, 500, 6_000),
        ({"individual_savings_account_interest_income": 700}, 5_300, 700, 700, 6_000),
        (
            {
                "individual_savings_account_interest_income": 700,
                "tax_free_savings_income": 800,
            },
            5_200,
            700,
            800,
            6_000,
        ),
        ({"savings_interest_income": 900}, 900, 500, 500, 1_400),
        ({"non_cash_isa_cash_interest": 700}, 5_300, 700, 700, 6_000),
    ],
    ids=[
        "old-default",
        "future-I",
        "explicit-T-over-I",
        "canonical-N-override",
        "future-detail",
    ],
)
def test_legacy_origin_core_fallback_after_projection_horizon_preserves_gross_and_overrides(
    future_inputs, expected_n, expected_i, expected_t, expected_cash
):
    # Dataset projection ends in2032. A supplied multi-year container avoids
    # extending the observation, so2033 exercises actual Core fallback.
    # Old gross G=2500+500=3000 doubles under the chosen ONS index ratio.
    # I had no old automatic index; future supplied I/T/detail still take priority.
    dataset = UKMultiYearDataset(
        datasets=[
            single(
                2032,
                contract=NORMALIZED,
                savings_interest_income=2_500,
                individual_savings_account_interest_income=500,
            )
        ]
    )
    index = "gov.economic_assumptions.indices.ons.household_interest_income"
    macro = Scenario(
        parameter_changes={index: {"year:2032-01-01:1": 100, "year:2033-01-01:1": 200}},
        applied_before_data_load=True,
    )
    simulation = Simulation(dataset=dataset, scenario=macro)
    for name, amount in future_inputs.items():
        simulation.set_input(name, 2033, [amount])
    for name, expected in (
        ("savings_interest_income", expected_n),
        ("individual_savings_account_interest_income", expected_i),
        ("tax_free_savings_income", expected_t),
        ("capital_income", expected_cash),
    ):
        assert value(simulation, name, 2033) == pytest.approx(expected, abs=0.01), name


@pytest.mark.parametrize(
    "contract, expected_i",
    [(NORMALIZED, 500), (ADDITIVE, 1_000)],
    ids=["legacy-origin-carry", "new-additive-ons-growth"],
)
def test_existing_isa_total_keeps_priority_over_its_same_period_of_which_detail(
    contract, expected_i
):
    # The explicit500 total already includes the100 detail. An earlier
    # component cannot replace that authoritative total in a later year.
    # Legacy I had no automatic index; new additive I follows the ONS ratio.
    dataset = UKMultiYearDataset(
        datasets=[
            single(
                2032,
                contract=contract,
                savings_interest_income=2_500,
                individual_savings_account_interest_income=500,
                non_cash_isa_cash_interest=100,
            )
        ]
    )
    index = "gov.economic_assumptions.indices.ons.household_interest_income"
    macro = Scenario(
        parameter_changes={index: {"year:2032-01-01:1": 100, "year:2033-01-01:1": 200}},
        applied_before_data_load=True,
    )
    simulation = Simulation(dataset=dataset, scenario=macro)
    assert value(simulation, "individual_savings_account_interest_income", 2032) == 500
    assert value(
        simulation, "individual_savings_account_interest_income", 2033
    ) == pytest.approx(expected_i, abs=0.01)
    assert value(simulation, "tax_free_savings_income", 2033) == pytest.approx(
        expected_i, abs=0.01
    )


# The reference below exercises Core's existing flow input protocol directly.
# It deliberately bypasses the UK dataset/ISA adapter and reads gross savings,
# rather than deriving expectations from the adapter being tested.
def gross_core_reference(savings_entries, exemptions, isa_interest):
    reference_system = system.clone()
    reference_system.parameters = deepcopy(system.parameters)
    reference_system.parameters.get_child(
        "gov.economic_assumptions.indices.ons.household_interest_income"
    ).update(period="year:2025:5", value=100)
    person = {
        "age": {2026: 35},
        "individual_savings_account_interest_income": dict(isa_interest),
    }
    if exemptions:
        person["tax_free_savings_income"] = dict(exemptions)
    reference = SimulationBuilder().build_from_dict(
        reference_system,
        {
            "people": {"person": person},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
    )
    # The dataset producer replays columns in declared order. Builder's
    # buffered input sorting would change Core's gross residual calculation.
    for period, amount in savings_entries:
        reference.set_input("savings_interest_income", period, [amount])
    return reference


def nonannual_frame(savings_entries, exemptions, isa_interest, contract=None):
    # Keep every financial column in the producer's declared order. A YEAR
    # variable may accept a MONTH input through Core's actual input handler.
    frame = pd.DataFrame(
        {
            "person_id__2026": [1],
            "person_benunit_id__2026": [1],
            "person_household_id__2026": [1],
            "age__2026": [35],
            **{
                f"individual_savings_account_interest_income__{period}": [amount]
                for period, amount in isa_interest
            },
            **{
                f"tax_free_savings_income__{period}": [amount]
                for period, amount in exemptions
            },
            **{
                f"savings_interest_income__{period}": [amount]
                for period, amount in savings_entries
            },
        }
    )
    if contract is not None:
        frame.attrs[KEY] = deepcopy(contract)
    return frame


@pytest.mark.parametrize(
    "contract, rolling_t, expected_n, expected_cash",
    [
        (None, None, 100, 600),
        (ADDITIVE, None, 600, 1_100),
        (None, 0, 600, 600),
        (None, 700, -100, 600),
    ],
    ids=["legacy", "additive-control", "explicit-zero-T", "explicit-T-differs-from-I"],
)
def test_nonannual_month_replay_normalizes_the_annual_period_core_stores(
    contract, rolling_t, expected_n, expected_cash
):
    # Core stores the July declaration as YEAR July2026--June2027 with value
    # 600. This is the accepted input protocol, not a new annualisation rule.
    rolling_year = "year:2026-07:1"
    entries = [("2026", 3_000), ("2026-07", 600)]
    exemptions = [] if rolling_t is None else [(rolling_year, rolling_t)]
    interest = [("2026", 500), ("2027", 500)]
    reference = gross_core_reference(entries, exemptions, interest)
    assert reference.get_array("savings_interest_income", rolling_year).tolist() == [
        600
    ]
    assert value(reference, "tax_free_savings_income", rolling_year) == (
        500 if rolling_t is None else rolling_t
    )
    simulation = Simulation(
        dataset=nonannual_frame(entries, exemptions, interest, contract),
        scenario=no_economic_assumptions,
    )
    assert value(simulation, "savings_interest_income", rolling_year) == pytest.approx(
        expected_n, abs=0.01
    )
    assert value(simulation, "capital_income", rolling_year) == pytest.approx(
        expected_cash, abs=0.01
    )
    assert value(
        simulation, "taxable_savings_interest_income", rolling_year
    ) == pytest.approx(max(expected_n, 0), abs=0.01)
    # Carry to a later query must preserve the original gross cash amount too.
    expected_later = value(reference, "savings_interest_income", 2027)
    if contract == ADDITIVE:
        expected_later += value(reference, "tax_free_savings_income", 2027)
    assert value(simulation, "capital_income", 2027) == pytest.approx(
        expected_later, abs=0.01
    )


@pytest.mark.parametrize(
    "entries, contract, expected_gross",
    [
        ([("month:2026-01:24", 6_000)], None, [3_000, 3_000]),
        ([("2026", 1_000), ("month:2026-01:24", 6_000)], None, [1_000, 5_000]),
        ([("month:2026-01:24", 6_000), ("2026", 3_000)], None, [3_000, 3_000]),
        ([("month:2026-01:24", 6_000)], ADDITIVE, [3_000, 3_000]),
    ],
    ids=["span-only", "prior-year-residual", "span-then-year", "additive-span-control"],
)
def test_long_month_span_replay_preserves_core_gross_order_before_year_specific_exemptions(
    entries, contract, expected_gross
):
    # MONTH24 invokes Core's YEAR-flow handler: it keeps existing annual
    # inputs and divides the gross residual over the remaining annual slots.
    # A YEAR(size2) input has different direct-storage semantics; tested below.
    exemptions = [("2026", 500), ("2027", 700)]
    interest = [("2026", 500), ("2027", 500)]
    reference = gross_core_reference(entries, exemptions, interest)
    assert [
        value(reference, "savings_interest_income", y) for y in (2026, 2027)
    ] == expected_gross
    simulation = Simulation(
        dataset=nonannual_frame(entries, exemptions, interest, contract),
        scenario=no_economic_assumptions,
    )
    for year, gross in zip((2026, 2027), expected_gross):
        exemption = value(reference, "tax_free_savings_income", year)
        expected_n = gross if contract == ADDITIVE else gross - exemption
        expected_cash = gross + exemption if contract == ADDITIVE else gross
        assert value(simulation, "savings_interest_income", year) == pytest.approx(
            expected_n, abs=0.01
        )
        assert value(simulation, "capital_income", year) == pytest.approx(
            expected_cash, abs=0.01
        )
        assert value(
            simulation, "taxable_savings_interest_income", year
        ) == pytest.approx(max(expected_n, 0), abs=0.01)


def test_mixed_annual_additive_input_is_gross_equivalent_during_a_legacy_span_replay():
    exemptions = [("2026", 500), ("2027", 700)]
    interest = [("2026", 500), ("2027", 500)]
    entries = [("2027", 2_000), ("month:2026-01:24", 6_000)]
    contract = {"version": 1, "years": {"2026": LEGACY, "2027": ADDITIVE}}
    # The known2027 ordinary2000 plus exemption700 consumes2700 of the
    # 6000 gross span, leaving3300 gross for2026. Core computes the residual.
    reference = gross_core_reference(
        [("2027", 2_700), ("month:2026-01:24", 6_000)], exemptions, interest
    )
    assert [value(reference, "savings_interest_income", y) for y in (2026, 2027)] == [
        3_300,
        2_700,
    ]
    simulation = Simulation(
        dataset=nonannual_frame(entries, exemptions, interest, contract),
        scenario=no_economic_assumptions,
    )
    for year, expected_n, gross in ((2026, 2_800, 3_300), (2027, 2_000, 2_700)):
        assert value(simulation, "savings_interest_income", year) == pytest.approx(
            expected_n, abs=0.01
        )
        assert value(simulation, "capital_income", year) == pytest.approx(
            gross, abs=0.01
        )


@pytest.mark.parametrize(
    "prior_gross",
    [None, 1_000],
    ids=["same-start-carry", "strict-earlier-uprating-first"],
)
def test_larger_year_input_preserves_core_same_start_fallback_and_earlier_priority(
    prior_gross,
):
    # Core stores YEAR(size2) directly, without dividing it into annual inputs.
    # For a one-year query it first tries a strictly earlier uprating source;
    # only absent that source does same-start carry apply. The gross control
    # below executes that exact base protocol rather than inventing a split.
    entries = [] if prior_gross is None else [("2025", prior_gross)]
    entries += [("year:2026:2", 6_000)]
    exemptions = [("2025", 400), ("2026", 500), ("2027", 700)]
    interest = [("2025", 500), ("2026", 500), ("2027", 500)]
    reference = gross_core_reference(entries, exemptions, interest)
    assert reference.get_array("savings_interest_income", "year:2026:2").tolist() == [
        6_000
    ]
    expected_gross = [6_000 if prior_gross is None else 1_000, 6_000]
    assert [
        value(reference, "savings_interest_income", y) for y in (2026, 2027)
    ] == expected_gross
    simulation = Simulation(
        dataset=nonannual_frame(entries, exemptions, interest),
        scenario=no_economic_assumptions,
    )
    for year, gross in zip((2026, 2027), expected_gross):
        exemption = value(reference, "tax_free_savings_income", year)
        assert value(simulation, "capital_income", year) == pytest.approx(
            gross, abs=0.01
        )
        assert value(simulation, "savings_interest_income", year) == pytest.approx(
            gross - exemption, abs=0.01
        )


@pytest.mark.parametrize(
    "complete_base_energy, expected_energy",
    [
        pytest.param(True, [150, 300, 450], id="complete-base-group"),
        pytest.param(False, [840, 960, 1_080], id="partial-base-different-basis"),
    ],
)
def test_isa_and_energy_contracts_compose_through_reset_export_and_projection(
    tmp_path, complete_base_energy, expected_energy
):
    """Both projection contracts survive the shared dataset boundaries.

    Resetting legacy interest gives gross3000 less the later exemption1200.
    Reprojection gives gross3000*1.2=3600, then ordinary2400 plus exempt1200.
    Energy grows by150/100 from the complete reset group's2025 basis, or by
    150/125 from the preserved later group's2026 basis. CPI levels and growth
    are controlled test inputs, not forecasts.
    """
    energy = (
        "domestic_energy_consumption",
        "electricity_consumption",
        "gas_consumption",
    )
    base = single(
        savings_interest_income=3_000,
        individual_savings_account_interest_income=500,
        tax_free_savings_income=700,
    )
    later = single(
        2026,
        savings_interest_income=6_000,
        individual_savings_account_interest_income=900,
        tax_free_savings_income=1_200,
    )
    base.energy_price_basis = {"period_type": "calendar_year", "period_value": 2025}
    later.energy_price_basis = {"period_type": "fiscal_year", "period_value": 2026}
    for observation in (base, later):
        observation.person["months_since_last_birthday"] = [0]
        observation.person["attends_private_school"] = [False]
    for variable, amount in zip(
        energy if complete_base_energy else energy[:1], [100, 200, 300]
    ):
        base.household[variable] = [amount]
    for variable, amount in zip(energy, [700, 800, 900]):
        later.household[variable] = [amount]
    original_base = base.copy()
    original_later = later.copy()

    simulation = Simulation(
        dataset=UKMultiYearDataset(datasets=[base, later]),
        scenario=no_economic_assumptions,
    )
    assert value(simulation, "savings_interest_income", 2026) == 1_800
    assert value(simulation, "tax_free_savings_income", 2026) == 1_200
    assert value(simulation, "individual_savings_account_interest_income", 2026) == 900
    assert value(simulation, "capital_income", 2026) == 3_000

    observed = UKSingleYearDataset.from_simulation(
        simulation,
        fiscal_year=2026,
        energy_price_basis=simulation.dataset[2026].energy_price_basis,
    )
    exported = Simulation(dataset=UKMultiYearDataset(datasets=[observed]))
    filtered = filter_dataset(exported, household_id=1, year=2026).copy()
    path = tmp_path / "joint-contracts.h5"
    filtered.save(path)
    reloaded = UKSingleYearDataset(file_path=path)
    assert reloaded.isa_income_contract == NORMALIZED
    assert (
        reloaded.energy_price_basis
        == (base if complete_base_energy else later).energy_price_basis
    )

    parameters = simulation.tax_benefit_system.parameters.clone()
    cpi = parameters.get_child(
        "gov.economic_assumptions.indices.obr.consumer_price_index"
    )
    for year, level in {2025: 100, 2026: 125, 2027: 150}.items():
        cpi.update(period=str(year), value=level)
    parameters.get_child(GDP_GROWTH).update(period="2027", value=0.2)
    projected = extend_single_year_dataset(reloaded, parameters, end_year=2027)
    projected_simulation = Simulation(dataset=projected)
    assert value(
        projected_simulation, "savings_interest_income", 2027
    ) == pytest.approx(2_400, abs=0.01)
    assert value(projected_simulation, "tax_free_savings_income", 2027) == 1_200
    assert value(projected_simulation, "capital_income", 2027) == pytest.approx(
        3_600, abs=0.01
    )
    for variable, expected in zip(energy, expected_energy):
        assert value(projected_simulation, variable, 2027) == pytest.approx(
            expected, abs=0.01
        )
    for actual, original in ((base, original_base), (later, original_later)):
        assert actual.energy_price_basis == original.energy_price_basis
        assert actual.isa_income_contract == original.isa_income_contract
        for name in ("person", "benunit", "household"):
            pd.testing.assert_frame_equal(
                getattr(actual, name), getattr(original, name), check_dtype=False
            )


def test_split_bsp_isa_and_energy_share_reset_and_projection_boundaries():
    """Reset preserves separate BSP, gross interest and the energy price basis.

    The later BSP observation stays777 while the separate CPI benefits reset
    to70/60. Legacy gross interest resets to3000, with later exemption1200.
    A controlled20% projection gives ordinary2400 plus exempt1200, while BSP
    stays777, the other benefits become84/72, and energy uses150/100 prices.
    """
    energy = (
        "domestic_energy_consumption",
        "electricity_consumption",
        "gas_consumption",
    )
    base = single(
        savings_interest_income=3_000,
        individual_savings_account_interest_income=500,
        tax_free_savings_income=700,
        bsp_reported=1_000,
        widowed_parents_allowance_reported=70,
        war_widows_pension_reported=60,
    )
    later = single(
        2026,
        savings_interest_income=6_000,
        individual_savings_account_interest_income=900,
        tax_free_savings_income=1_200,
        bsp_reported=777,
        widowed_parents_allowance_reported=140,
        war_widows_pension_reported=120,
    )
    base.energy_price_basis = {"period_type": "calendar_year", "period_value": 2025}
    later.energy_price_basis = {"period_type": "fiscal_year", "period_value": 2026}
    for dataset in (base, later):
        dataset.person["months_since_last_birthday"] = [0]
        dataset.person["attends_private_school"] = [False]
    for variable, first, second in zip(energy, [100, 200, 300], [700, 800, 900]):
        base.household[variable] = [first]
        later.household[variable] = [second]
    originals = [dataset.copy() for dataset in (base, later)]
    simulation = Simulation(
        dataset=UKMultiYearDataset(datasets=[base, later]),
        scenario=no_economic_assumptions,
    )
    reset_expected = {
        "bsp_reported": 777,
        "widowed_parents_allowance_reported": 70,
        "war_widows_pension_reported": 60,
        "savings_interest_income": 1_800,
        "tax_free_savings_income": 1_200,
        "capital_income": 3_000,
    }
    for variable, expected in reset_expected.items():
        assert value(simulation, variable, 2026) == pytest.approx(expected, abs=0.01)
    observed = UKSingleYearDataset.from_simulation(
        simulation,
        fiscal_year=2026,
        energy_price_basis=simulation.dataset[2026].energy_price_basis,
    )
    assert observed.isa_income_contract == NORMALIZED
    assert observed.energy_price_basis == base.energy_price_basis
    changes = {
        "gov.economic_assumptions.indices.obr.consumer_price_index": {
            str(year): level
            for year, level in {2025: 100, 2026: 125, 2027: 150, 2035: 300}.items()
        },
        "gov.economic_assumptions.yoy_growth.obr.consumer_price_index": {"2027": 0.2},
        GDP_GROWTH: {"2027": 0.2},
    }
    parameters = simulation.tax_benefit_system.parameters.clone()
    for name, periods in changes.items():
        for year, amount in periods.items():
            parameters.get_child(name).update(period=year, value=amount)
    projected = extend_single_year_dataset(observed, parameters, end_year=2027)
    result = Simulation(
        dataset=projected,
        scenario=Scenario(parameter_changes=changes, applied_before_data_load=True),
    )
    expected_2027 = {
        "bsp_reported": 777,
        "widowed_parents_allowance_reported": 84,
        "war_widows_pension_reported": 72,
        "savings_interest_income": 2_400,
        "tax_free_savings_income": 1_200,
        "capital_income": 3_600,
        **dict(zip(energy, [150, 300, 450])),
    }
    for reset in (False, True):
        if reset:
            result.reset_calculations()
        for variable, expected in expected_2027.items():
            assert value(result, variable, 2027) == pytest.approx(expected, abs=0.01)
        assert value(result, "bsp_reported", 2035) == 777
        assert value(
            result, "widowed_parents_allowance_reported", 2035
        ) == pytest.approx(168, abs=0.01)
        assert value(result, "bsp_reported", "2035-07") == pytest.approx(
            777 / 12, abs=0.01
        )
    for dataset, original in zip((base, later), originals):
        assert dataset.isa_income_contract == original.isa_income_contract
        assert dataset.energy_price_basis == original.energy_price_basis
        for table in ("person", "benunit", "household"):
            pd.testing.assert_frame_equal(
                getattr(dataset, table), getattr(original, table)
            )


@pytest.mark.parametrize(
    "contract", [LEGACY, ADDITIVE], ids=["legacy-gross", "additive"]
)
@pytest.mark.parametrize(
    "isa_column, ordinary_column, supplied",
    [
        ("individual_savings_account_dividend_income", "dividend_income", 300),
        ("non_cash_isa_cash_interest", "savings_interest_income", 100),
    ],
    ids=["isa-dividend", "noncash-interest"],
)
def test_new_isa_columns_follow_ordinary_dataset_projection_in_both_contracts(
    contract, isa_column, ordinary_column, supplied
):
    """Both sides of the 2030 map boundary use the ordinary dataset indices.

    Ordinary interest and ISA interest together start at 2000 on either
    contract. Legacy projection grows gross interest before subtracting the
    unchanged 500 exemption; additive projection grows ordinary 1500 and
    exempt 500 separately. The noncash 100 is already included in that 500.
    Ordinary dividends 200 and separate ISA dividends 300 complete the cash
    total 2500. A benchmark with only the ordinary counterpart independently
    checks the new columns without populating the projection map for them.
    """
    projection = Scenario(
        parameter_changes={
            GDP_GROWTH: {f"year:{year}-01-01:1": 0.1 for year in range(2026, 2033)}
        },
        applied_before_data_load=True,
    )
    source = single(
        contract=contract,
        savings_interest_income=2_000 if contract == LEGACY else 1_500,
        individual_savings_account_interest_income=500,
        dividend_income=200,
        individual_savings_account_dividend_income=300,
        non_cash_isa_cash_interest=100,
    )
    original = source.copy()
    benchmark_source = single(contract=ADDITIVE, **{ordinary_column: supplied})
    benchmark_original = benchmark_source.copy()
    simulation = Simulation(dataset=source, scenario=projection)
    benchmark = Simulation(dataset=benchmark_source, scenario=projection)

    for year in (2025, 2028, 2030, 2031, 2032):
        factor = 1.1 ** (year - 2025)
        ordinary = value(benchmark, ordinary_column, year)
        assert ordinary == pytest.approx(supplied * factor, abs=0.01)
        assert value(simulation, isa_column, year) == pytest.approx(ordinary, abs=0.01)
        if year > 2025:
            assert ordinary > supplied
        exempt = 500 if contract == LEGACY else 500 * factor
        ordinary_interest = (
            2_000 * factor - exempt if contract == LEGACY else 1_500 * factor
        )
        assert value(
            simulation, "individual_savings_account_interest_income", year
        ) == (pytest.approx(exempt, abs=0.01))
        assert value(simulation, "tax_free_savings_income", year) == pytest.approx(
            exempt, abs=0.01
        )
        assert value(simulation, "savings_interest_income", year) == pytest.approx(
            ordinary_interest, abs=0.01
        )
        assert value(simulation, "taxable_savings_interest_income", year) == (
            pytest.approx(ordinary_interest, abs=0.01)
        )
        assert value(simulation, "taxable_dividend_income", year) == pytest.approx(
            200 * factor, abs=0.01
        )
        assert value(simulation, "capital_income", year) == pytest.approx(
            2_500 * factor, abs=0.01
        )

    for actual, before in ((source, original), (benchmark_source, benchmark_original)):
        assert actual.isa_income_contract == before.isa_income_contract
        for table in ("person", "benunit", "household"):
            pd.testing.assert_frame_equal(
                getattr(actual, table), getattr(before, table)
            )

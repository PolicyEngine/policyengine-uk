"""Public geography inference, with ONS council oracles and sparse situations.

The ONS fixture was derived from the May 2026 and December 2020 UK lookups
before the implementation. It includes every current and historical council
in LocalAuthority. These tests never import the production geography helper.
"""

from copy import deepcopy
from itertools import permutations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import warnings
from policyengine_core.periods import period as core_period
from policyengine_core.holders.helpers import get_stored_input
from policyengine_core.reforms import Reform
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk import (
    CountryTaxBenefitSystem,
    Microsimulation,
    Scenario,
    Simulation,
)
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.utils.household_subset import household_subset
from policyengine_uk.variables.household.BRMA import brma as brma_variable
from policyengine_uk.variables.household.demographic.country import (
    Country,
    country as country_variable,
)
from policyengine_uk.variables.household.demographic.geography import Region
from policyengine_uk.variables.household.demographic.locations import (
    BRMAName,
    LocalAuthority,
)
from policyengine_uk.variables.household.region import region as region_variable


YEAR = 2026
ORACLE = json.loads(
    (
        Path(__file__).parent / "fixtures/geography/ons_local_authority_regions.json"
    ).read_text()
)["authorities"]


def situation(households, sizes=None, person_inputs=None):
    """Build small independent households without inserting geography defaults."""
    sizes = sizes or [1] * len(households)
    result = {"people": {}, "benunits": {}, "households": {}}
    for index, inputs in enumerate(households):
        members = []
        for member in range(sizes[index]):
            name = f"person{index}_{member}"
            result["people"][name] = {
                "age": {2024: 40 if member == 0 else 10},
                **deepcopy(person_inputs or {}),
            }
            members.append(name)
        result["benunits"][f"benunit{index}"] = {"members": members}
        result["households"][f"household{index}"] = {
            "members": members,
            **deepcopy(inputs),
        }
    return result


def labels(simulation, variable, year=YEAR, map_to=None):
    return [
        str(value)
        for value in simulation.calculate(
            variable, year, map_to=map_to, decode_enums=True
        )
    ]


class WelshRegion(Reform):
    def apply(self):
        class region(region_variable):
            def formula(household, period, parameters):
                return household.filled_array(Region.WALES)

        self.update_variable(region)


class WelshCountry(Reform):
    def apply(self):
        class country(country_variable):
            def formula(household, period, parameters):
                return household.filled_array(Country.WALES)

        self.update_variable(country)


class CardiffBrma(Reform):
    def apply(self):
        class brma(brma_variable):
            def formula(household, period, parameters):
                return household.filled_array(BRMAName.CARDIFF)

        self.update_variable(brma)


def test_every_council_has_its_ons_region_and_country():
    assert len(ORACLE) == 385
    assert {row["local_authority"] for row in ORACLE} == {
        value.name for value in LocalAuthority
    }
    # One test, 13 serial batches; never construct a population-sized model.
    for start in range(0, len(ORACLE), 32):
        batch = ORACLE[start : start + 32]
        simulation = Simulation(
            situation=situation(
                [{"local_authority": {YEAR: row["local_authority"]}} for row in batch]
            )
        )
        assert labels(simulation, "region") == [row["region"] for row in batch]
        assert labels(simulation, "country") == [row["country"] for row in batch]


@pytest.mark.parametrize("country", ["SCOTLAND", "WALES", "NORTHERN_IRELAND"])
def test_only_a_devolved_country_infers_the_same_region(country):
    simulation = Simulation(situation=situation([{"country": {YEAR: country}}]))
    assert labels(simulation, "region") == [country]
    assert labels(simulation, "country") == [country]


@pytest.mark.parametrize(
    ("council", "region"),
    [
        ("CITY_OF_EDINBURGH", "SCOTLAND"),
        ("CARDIFF", "WALES"),
        ("OXFORD", "SOUTH_EAST"),
    ],
)
def test_inferred_geography_matches_explicit_tax_and_benefit_routes(council, region):
    # ONS supplies the region oracle; the explicit-input world exercises the
    # existing tax/benefit rules independently of the new inference helper.
    def tax(inputs):
        sim = Simulation(
            situation=situation(
                [inputs], person_inputs={"employment_income": {YEAR: 50_000}}
            )
        )
        return float(sim.calculate("income_tax", YEAR)[0])

    derived_tax = tax({"local_authority": {YEAR: council}})
    explicit_tax = tax({"region": {YEAR: region}})
    assert explicit_tax > 0
    assert derived_tax == pytest.approx(explicit_tax, abs=0.01)

    def award(inputs):
        data = situation(
            [
                {
                    "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                    "rent": {YEAR: 25_000},
                    "council_tax": {YEAR: 0},
                    **inputs,
                }
            ],
            sizes=[2],
        )
        data["benunits"]["benunit0"]["claims_universal_credit"] = {YEAR: True}
        return float(Simulation(situation=data).calculate("universal_credit", YEAR)[0])

    explicit_award = award({"region": {YEAR: region}})
    assert explicit_award > 0
    assert award({"local_authority": {YEAR: council}}) == pytest.approx(
        explicit_award, abs=0.01
    )


def test_sparse_households_do_not_promote_filled_defaults_to_inputs():
    simulation = Simulation(
        situation=situation(
            [
                {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
                {"country": {YEAR: "WALES"}},
                {"region": {YEAR: "LONDON"}, "country": {YEAR: "ENGLAND"}},
                {"local_authority": {YEAR: "MAIDSTONE"}},
                {},
                {"country": {YEAR: "ENGLAND"}},
            ]
        )
    )
    expected = ["SCOTLAND", "WALES", "LONDON", "SOUTH_EAST", "LONDON", "LONDON"]
    assert labels(simulation, "country") == [
        "SCOTLAND",
        "WALES",
        "ENGLAND",
        "ENGLAND",
        "ENGLAND",
        "ENGLAND",
    ]
    assert labels(simulation, "region") == expected
    simulation.reset_calculations()
    assert labels(simulation.clone(), "region") == expected
    assert labels(simulation, "region") == expected


def test_region_carry_query_order_reset_clone_and_branch_are_independent():
    simulation = Simulation(situation=situation([{"region": {2024: "WALES"}}]))
    for year in [2026, 2024, 2025]:
        assert labels(simulation, "region", year) == ["WALES"]
        assert labels(simulation, "country", year) == ["WALES"]
    simulation.reset_calculations()
    clone = simulation.clone()
    assert labels(clone, "region") == ["WALES"]
    clone.set_input("region", YEAR, ["SCOTLAND"])
    clone.reset_calculations()
    assert labels(clone, "country") == ["SCOTLAND"]
    assert labels(simulation, "country") == ["WALES"]
    clone.delete_arrays("region")
    clone.reset_calculations()
    assert labels(clone, "region") == ["LONDON"]
    assert labels(clone, "country") == ["ENGLAND"]
    branch = simulation.get_branch("geography", clone_system=True)
    branch.set_input("region", 2025, ["SCOTLAND"])
    assert labels(branch, "region") == ["SCOTLAND"]
    assert labels(simulation, "region") == ["WALES"]


def test_later_council_input_for_another_household_does_not_replace_earlier_input():
    simulation = Simulation(
        situation=situation(
            [
                {"local_authority": {2024: "CITY_OF_EDINBURGH"}},
                {"local_authority": {2026: "CARDIFF"}},
            ]
        )
    )
    for year in [2027, 2024, 2026, 2025]:
        second = "WALES" if year >= 2026 else "LONDON"
        assert labels(simulation, "region", year) == ["SCOTLAND", second]
    assert labels(simulation, "country") == ["SCOTLAND", "WALES"]


@pytest.mark.parametrize("query", ["region", "country"])
@pytest.mark.parametrize(
    "inputs",
    [
        {"local_authority": {YEAR: "OXFORD"}, "region": {YEAR: "LONDON"}},
        {"local_authority": {YEAR: "MAIDSTONE"}, "region": {YEAR: "LONDON"}},
    ],
)
def test_same_nation_supplied_geography_warns_and_retains_facts(inputs, query):
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation = Simulation(situation=situation([inputs]))
        simulation.calculate(query, YEAR)
    for variable, values in inputs.items():
        assert labels(simulation, variable) == [values[YEAR]]
    expected_region = (
        inputs["region"][YEAR]
        if "region" in inputs
        else next(
            row["region"]
            for row in ORACLE
            if row["local_authority"] == inputs["local_authority"][YEAR]
        )
    )
    assert labels(simulation, "region") == [expected_region]


@pytest.mark.parametrize(
    "order", list(permutations(["local_authority", "region", "country"]))
)
def test_consistent_constructor_facts_are_checked_after_all_fields_load(order):
    values = {
        "local_authority": "CITY_OF_EDINBURGH",
        "region": "SCOTLAND",
        "country": "SCOTLAND",
    }
    inputs = {key: {YEAR: values[key]} for key in order}
    simulation = Simulation(situation=situation([inputs]))
    assert labels(simulation, "country") == ["SCOTLAND"]
    assert labels(simulation, "region") == ["SCOTLAND"]


def test_field_by_field_edits_keep_raw_facts_but_block_unresolved_public_reads():
    simulation = Simulation(situation=situation([{"country": {YEAR: "WALES"}}]))
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation.set_input("region", YEAR, ["LONDON"])
    exported = simulation.to_input_dataframe()
    assert _raw_geography_names(exported, "region__2026", Region) == ["LONDON"]
    assert _raw_geography_names(exported, "country__2026", Country) == ["WALES"]
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        simulation.calculate("country", YEAR)
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation.set_input("local_authority", YEAR, ["CARDIFF"])
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation.set_input("country", YEAR, ["SCOTLAND"])
    exported = simulation.to_input_dataframe()
    assert _raw_geography_names(exported, "region__2026", Region) == ["LONDON"]
    assert _raw_geography_names(exported, "country__2026", Country) == ["SCOTLAND"]
    assert _raw_geography_names(exported, "local_authority__2026", LocalAuthority) == [
        "CARDIFF"
    ]
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        simulation.calculate("region", YEAR)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.delete_arrays("region")
        simulation.set_input("country", YEAR, ["WALES"])
    assert labels(simulation, "region") == ["WALES"]
    assert labels(simulation, "country") == ["WALES"]
    assert labels(simulation, "local_authority") == ["CARDIFF"]


def test_single_household_scalar_enum_setters_and_invalid_multi_household_input():
    simulation = Simulation(situation=situation([{}]))
    for variable, value in [
        ("region", "SCOTLAND"),
        ("country", "SCOTLAND"),
        ("local_authority", "CITY_OF_EDINBURGH"),
        ("brma", "GREATER_GLASGOW"),
    ]:
        simulation.set_input(variable, YEAR, value)
        assert labels(simulation, variable) == [value]
    assert labels(simulation, "region") == ["SCOTLAND"]
    assert labels(simulation, "country") == ["SCOTLAND"]

    multiple = Simulation(situation=situation([{}, {}]))
    for variable, value in [
        ("region", "SCOTLAND"),
        ("country", "SCOTLAND"),
        ("local_authority", "CITY_OF_EDINBURGH"),
        ("brma", "GREATER_GLASGOW"),
    ]:
        with pytest.raises(ValueError):
            multiple.set_input(variable, YEAR, value)
    assert labels(multiple, "region") == ["LONDON", "LONDON"]
    assert labels(multiple, "brma") == ["INNER_SOUTH_EAST_LONDON"] * 2


@pytest.mark.parametrize(
    "override", ["MAIDSTONE", "INNER_SOUTH_EAST_LONDON", "GREATER_GLASGOW"]
)
@pytest.mark.parametrize("brma_first", [True, False])
def test_partial_brma_override_does_not_fix_its_neighbors_filled_default(
    override, brma_first
):
    simulation = Simulation(
        situation=situation(
            [
                {"country": {YEAR: "WALES"}, "brma": {YEAR: override}},
                {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
            ]
        )
    )
    if not brma_first:
        assert labels(simulation, "region") == ["WALES", "SCOTLAND"]
    assert labels(simulation, "brma") == [override, "LOTHIAN"]
    assert labels(simulation, "region") == ["WALES", "SCOTLAND"]
    simulation.reset_calculations()
    assert labels(simulation.clone(), "brma") == [override, "LOTHIAN"]


def test_brma_carries_per_cell_until_that_households_region_changes():
    simulation = Simulation(
        situation=situation(
            [
                {
                    "region": {2024: "SCOTLAND", 2027: "WALES"},
                    "brma": {2024: "GREATER_GLASGOW"},
                },
                {"region": {2024: "WALES"}, "brma": {2026: "CARDIFF"}},
            ]
        )
    )
    assert labels(simulation, "brma", 2026) == ["GREATER_GLASGOW", "CARDIFF"]
    assert labels(simulation, "brma", 2027) == ["CARDIFF", "CARDIFF"]
    assert labels(simulation, "brma", 2025) == ["GREATER_GLASGOW", "CARDIFF"]


@pytest.mark.parametrize("trace", [False, True])
@pytest.mark.parametrize("variable", ["region", "country", "brma"])
def test_partial_supplied_cells_respect_active_custom_formulas(variable, trace):
    if variable == "region":
        rows = [
            {"region": {YEAR: "LONDON"}, "local_authority": {YEAR: "WESTMINSTER"}},
            {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
        ]
        reform = WelshRegion
        expected = {
            "region": ["LONDON", "WALES"],
            "country": ["ENGLAND", "WALES"],
            "brma": ["INNER_SOUTH_EAST_LONDON", "CARDIFF"],
        }
    elif variable == "country":
        rows = [{"country": {YEAR: "SCOTLAND"}}, {}]
        reform = WelshCountry
        expected = {
            "region": ["SCOTLAND", "LONDON"],
            "country": ["SCOTLAND", "WALES"],
            "brma": ["LOTHIAN", "INNER_SOUTH_EAST_LONDON"],
        }
    else:
        rows = [
            {"country": {YEAR: "WALES"}, "brma": {YEAR: "MAIDSTONE"}},
            {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
        ]
        reform = CardiffBrma
        expected = {
            "region": ["WALES", "SCOTLAND"],
            "country": ["WALES", "SCOTLAND"],
            "brma": ["MAIDSTONE", "CARDIFF"],
        }
    simulation = Simulation(
        situation=situation(rows, sizes=[2, 1]), reform=reform, trace=trace
    )
    # Country first must use actual custom region, while native region must
    # never read a calculated custom country back as a supplied fact.
    for name in ["country", "region", "brma"]:
        assert labels(simulation, name) == expected[name]
    first, second = expected[variable]
    assert labels(simulation, variable, map_to="person") == [first, first, second]


@pytest.mark.parametrize(
    ("variable", "supplied", "default"),
    [
        ("region", "SCOTLAND", "LONDON"),
        ("country", "SCOTLAND", "ENGLAND"),
        ("brma", "GREATER_GLASGOW", "MAIDSTONE"),
    ],
)
def test_neutralization_keeps_core_priority_over_physically_stored_inputs(
    variable, supplied, default
):
    simulation = Simulation(situation=situation([{variable: {YEAR: supplied}}]))
    assert labels(simulation, variable) == [supplied]
    branch = simulation.get_branch("neutralized_geography", clone_system=True)
    stored = get_stored_input(
        branch.get_holder(variable), core_period(str(YEAR)), simulation.branch_name
    )
    assert stored is not None
    before = stored.copy()
    branch.tax_benefit_system.neutralize_variable(variable)
    branch.drop_computed_arrays()
    np.testing.assert_array_equal(
        get_stored_input(
            branch.get_holder(variable), core_period(str(YEAR)), simulation.branch_name
        ),
        before,
    )
    assert labels(branch, variable) == [default]
    assert labels(simulation, variable) == [supplied]
    if variable == "region":
        assert labels(branch, "country") == ["ENGLAND"]


@pytest.mark.parametrize("ignored", ["neutralized", "ended"])
def test_ignored_geography_setters_do_not_validate_or_promote_old_padding(ignored):
    parent = Simulation(
        situation=situation(
            [
                {"region": {YEAR: "LONDON"}, "country": {YEAR: "ENGLAND"}},
                {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
            ]
        )
    )
    simulation = parent.get_branch("ignored_geography", clone_system=True)
    assert labels(simulation, "region") == ["LONDON", "SCOTLAND"]
    if ignored == "neutralized":
        simulation.tax_benefit_system.neutralize_variable("region")
    else:

        class region(region_variable):
            end = "2025-12-31"

        simulation.tax_benefit_system.update_variable(region)
    # This would contradict the first household's actual England input if
    # it were accepted. Core ignores neutralized and post-end inputs.
    simulation.set_input("region", 2026, ["SCOTLAND", "WALES"])
    if ignored == "ended":
        simulation.tax_benefit_system.replace_variable(region_variable)
    else:
        simulation.tax_benefit_system.update_variable(region_variable)
    simulation.drop_computed_arrays()
    assert labels(simulation, "region", 2026) == ["LONDON", "SCOTLAND"]
    assert labels(simulation, "country", 2026) == ["ENGLAND", "SCOTLAND"]
    assert labels(parent, "region") == ["LONDON", "SCOTLAND"]


def test_sparse_uk_inputs_match_equivalent_fully_specified_native_core_inputs():
    sparse = situation(
        [
            {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
            {"local_authority": {YEAR: "WESTMINSTER"}, "region": {YEAR: "LONDON"}},
        ]
    )
    full = deepcopy(sparse)
    for index, (region, country, brma) in enumerate(
        [
            ("SCOTLAND", "SCOTLAND", "LOTHIAN"),
            ("LONDON", "ENGLAND", "INNER_SOUTH_EAST_LONDON"),
        ]
    ):
        full["households"][f"household{index}"].update(
            region={YEAR: region}, country={YEAR: country}, brma={YEAR: brma}
        )
    uk = Simulation(situation=sparse)
    core = SimulationBuilder().build_from_entities(CountryTaxBenefitSystem(), full)
    for name in ["region", "country", "brma"]:
        assert labels(uk, name) == labels(core, name)
    np.testing.assert_array_equal(
        uk.calculate("pays_scottish_income_tax", YEAR),
        core.calculate("pays_scottish_income_tax", YEAR),
    )


def sparse_transport_inputs():
    return [
        {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
        {
            "region": {YEAR: "LONDON"},
            "country": {YEAR: "ENGLAND"},
            "brma": {YEAR: "INNER_SOUTH_EAST_LONDON"},
        },
    ]


def transport_ready_situation(households):
    """Supply the existing dataset bridge's IDs and non-geography columns."""
    data = situation(households)
    for index in range(len(households)):
        person_id, benunit_id, household_id = index + 1, index + 101, index + 1001
        data["people"][f"person{index}_0"].update(
            person_id={2024: person_id},
            person_benunit_id={2024: benunit_id},
            person_household_id={2024: household_id},
        )
        data["benunits"][f"benunit{index}"]["benunit_id"] = {2024: benunit_id}
        data["households"][f"household{index}"].update(
            household_id={2024: household_id},
            council_tax={2024: 0},
            rent={2024: 0},
            tenure_type={2024: "OWNED_OUTRIGHT"},
        )
    return data


def assert_transport_geography(simulation):
    assert labels(simulation, "country") == ["SCOTLAND", "ENGLAND"]
    assert labels(simulation, "region") == ["SCOTLAND", "LONDON"]
    assert labels(simulation, "brma") == ["LOTHIAN", "INNER_SOUTH_EAST_LONDON"]


def test_population_rebuild_adopts_sparse_facts_without_the_old_targets_masks():
    donor = Simulation(situation=situation(sparse_transport_inputs()))
    assert_transport_geography(donor)
    target = Simulation(situation=situation([{"country": {YEAR: "WALES"}}]))
    target.build_from_populations(donor.populations)
    assert_transport_geography(target)
    target.set_input("brma", YEAR, ["MAIDSTONE", "CARDIFF"])
    assert labels(target, "brma") == ["MAIDSTONE", "CARDIFF"]
    assert_transport_geography(donor)


def test_named_branch_sparse_rebuild_uses_its_actual_new_inputs_and_isolates_parent():
    parent = Simulation(
        situation=situation(
            [{"region": {YEAR: "SCOTLAND"}}, {"region": {YEAR: "WALES"}}]
        )
    )
    child = parent.get_branch("sparse_rebuild", clone_system=True)
    child.build_from_situation(situation(sparse_transport_inputs()))
    assert_transport_geography(child)
    child.reset_calculations()
    assert_transport_geography(child.clone())
    assert labels(parent, "region") == ["SCOTLAND", "WALES"]
    assert labels(parent, "country") == ["SCOTLAND", "WALES"]


def test_sparse_input_dataframe_round_trip_keeps_missing_and_default_equal_facts():
    original = Simulation(
        situation=transport_ready_situation(sparse_transport_inputs())
    )
    assert_transport_geography(original)
    exported = original.to_input_dataframe()
    before = exported.copy(deep=True)
    reloaded = Simulation(dataset=exported, scenario=no_economic_assumptions)
    assert_transport_geography(reloaded)
    pd.testing.assert_frame_equal(exported, before)
    # A subsequent whole-array public input is genuine in both rows,
    # including the value equal to BRMA's variable default.
    reloaded.set_input("brma", YEAR, ["MAIDSTONE", "INNER_SOUTH_EAST_LONDON"])
    assert labels(reloaded, "brma") == ["MAIDSTONE", "INNER_SOUTH_EAST_LONDON"]
    assert_transport_geography(original)
    again = Simulation(
        dataset=reloaded.to_input_dataframe(), scenario=no_economic_assumptions
    )
    assert labels(again, "brma") == ["MAIDSTONE", "INNER_SOUTH_EAST_LONDON"]
    assert labels(again, "region") == ["SCOTLAND", "LONDON"]


def test_tiny_public_dataset_infers_geography_before_later_year_projection():
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [40, 40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "local_authority": ["CITY_OF_EDINBURGH", "CARDIFF"],
                "council_tax": [0, 0],
                "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
                "rent": [0, 0],
            }
        ),
        fiscal_year=2024,
    )
    simulation = Simulation(dataset=dataset, scenario=no_economic_assumptions)
    for year in [2026, 2024, 2025]:
        assert labels(simulation, "region", year) == ["SCOTLAND", "WALES"]
        assert labels(simulation, "country", year) == ["SCOTLAND", "WALES"]


def test_custom_brma_snapshot_does_not_promote_computed_results_to_supplied_facts():
    parent = Simulation(
        situation=transport_ready_situation(
            [{"region": {2024: "SCOTLAND"}, "brma": {2024: "GREATER_GLASGOW"}}]
        )
    )
    original = parent.get_branch("snapshot_custom_brma", clone_system=True)
    assert labels(original, "brma") == ["GREATER_GLASGOW"]

    class brma(brma_variable):
        def formula(household, period, parameters):
            return household.filled_array(BRMAName.CARDIFF)

    original.tax_benefit_system.update_variable(brma)
    original.drop_computed_arrays()
    assert labels(original, "brma") == ["CARDIFF"]
    snapshot = UKSingleYearDataset.from_simulation(original, fiscal_year=YEAR)
    assert snapshot.household.brma.tolist() == ["CARDIFF"]
    reloaded = Simulation(dataset=snapshot, scenario=no_economic_assumptions)
    assert labels(reloaded, "region") == ["SCOTLAND"]
    assert labels(reloaded, "brma") == ["LOTHIAN"]
    assert labels(original, "brma") == ["CARDIFF"]
    assert labels(parent, "brma") == ["GREATER_GLASGOW"]


def test_reordered_snapshot_presence_follows_household_ids_and_remains_inferable():
    original = Simulation(
        situation=transport_ready_situation(sparse_transport_inputs())
    )
    assert_transport_geography(original)
    snapshot = UKSingleYearDataset.from_simulation(original, fiscal_year=YEAR)
    first, second = snapshot.household.household_id.tolist()
    snapshot.household = snapshot.household.iloc[::-1].reset_index(drop=True)
    reloaded = Simulation(dataset=snapshot, scenario=no_economic_assumptions)

    def by_id(variable, year=YEAR):
        return dict(
            zip(
                reloaded.calculate("household_id", year).tolist(),
                labels(reloaded, variable, year),
            )
        )

    assert by_id("region") == {first: "SCOTLAND", second: "LONDON"}
    assert by_id("country") == {first: "SCOTLAND", second: "ENGLAND"}
    ids = reloaded.calculate("household_id", 2027).tolist()
    councils = {first: "CARDIFF", second: "WESTMINSTER"}
    reloaded.set_input(
        "local_authority", 2027, [councils[identifier] for identifier in ids]
    )
    assert by_id("region", 2027) == {first: "WALES", second: "LONDON"}
    assert by_id("country", 2027) == {first: "WALES", second: "ENGLAND"}
    assert by_id("brma", 2027) == {first: "CARDIFF", second: "INNER_SOUTH_EAST_LONDON"}
    assert_transport_geography(original)


def test_enabled_projection_matches_independently_explicit_ons_geography():
    ids = list(range(1, 7))
    derived = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [32] * 6,
                "student_loan_plan": ["NONE"] * 6,
                "student_loan_repayments": [0.0] * 6,
                "highest_education": ["TERTIARY"] * 6,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": [1.0] * 6,
                "local_authority": ["CITY_OF_EDINBURGH"] * 6,
                "tenure_type": ["RENT_PRIVATELY"] * 6,
                "rent": [10_000.0] * 6,
                "council_tax": [1_000.0] * 6,
                "water_and_sewerage_charges": [500.0] * 6,
            }
        ),
        fiscal_year=2024,
    )
    explicit = derived.copy()
    explicit.household["region"] = "SCOTLAND"
    inferred_simulation = Simulation(dataset=derived)
    explicit_simulation = Simulation(dataset=explicit)
    for variable, base_amount in [
        ("council_tax", 1_000.0),
        ("water_and_sewerage_charges", 500.0),
        ("rent", 10_000.0),
    ]:
        actual = inferred_simulation.calculate(variable, YEAR)
        expected = explicit_simulation.calculate(variable, YEAR)
        assert np.all(expected > 0)
        assert np.any(np.abs(expected - base_amount) > 0.01)
        np.testing.assert_allclose(actual, expected, atol=0.01, rtol=0)
    actual_plans = labels(inferred_simulation, "student_loan_plan")
    assert actual_plans == labels(explicit_simulation, "student_loan_plan")
    assert "PLAN_4" in actual_plans
    assert set(actual_plans) <= {"NONE", "PLAN_4"}
    assert "region" not in derived.household.columns


@pytest.mark.parametrize("years", [(2023, 2022), (2022, 2023)])
def test_country_inputs_are_year_specific_while_region_and_council_carry(years):
    simulation = Simulation(
        situation=situation(
            [
                {"country": {2022: "NORTHERN_IRELAND"}},
                {"region": {2022: "NORTHERN_IRELAND"}},
                {"local_authority": {2022: "BELFAST"}},
                {"country": {2023: "NORTHERN_IRELAND"}},
            ]
        )
    )
    expected = {
        2022: ["NORTHERN_IRELAND"] * 3 + ["ENGLAND"],
        2023: ["ENGLAND"] + ["NORTHERN_IRELAND"] * 3,
    }
    for year in years:
        assert labels(simulation, "country", year) == expected[year]
    assert labels(simulation, "region", 2023) == ["LONDON"] + ["NORTHERN_IRELAND"] * 3
    # Existing AFP cases distinguish a one-year country observation from
    # persistent geography. Preserve their actual final rebate oracles.
    np.testing.assert_allclose(
        simulation.calculate("ebr_alternative_fuel_payment", 2023),
        [0, 200, 200, 200],
        atol=0.01,
        rtol=0,
    )
    np.testing.assert_allclose(
        simulation.calculate("energy_bills_rebate", 2023),
        [201, 600, 600, 600],
        atol=0.01,
        rtol=0,
    )
    simulation.reset_calculations()
    assert labels(simulation.clone(), "country", 2023) == expected[2023]


def test_prior_country_input_does_not_mask_a_later_custom_country_formula():
    simulation = Simulation(
        situation=situation([{"country": {2024: "SCOTLAND"}}, {}]),
        reform=WelshCountry,
    )
    assert labels(simulation, "country", 2026) == ["WALES", "WALES"]
    assert labels(simulation, "region", 2026) == ["LONDON", "LONDON"]
    assert labels(simulation, "country", 2024) == ["SCOTLAND", "WALES"]
    assert labels(simulation, "region", 2024) == ["SCOTLAND", "LONDON"]


@pytest.mark.parametrize("reform", [None, WelshCountry], ids=["native", "custom"])
def test_snapshot_does_not_promote_a_past_country_input_into_a_new_year(reform):
    original = Simulation(
        situation=transport_ready_situation([{"country": {2024: "NORTHERN_IRELAND"}}]),
        reform=reform,
    )
    current_country = "WALES" if reform is WelshCountry else "ENGLAND"
    assert labels(original, "country", 2024) == ["NORTHERN_IRELAND"]
    assert labels(original, "country", YEAR) == [current_country]
    snapshot = UKSingleYearDataset.from_simulation(original, fiscal_year=YEAR)
    assert snapshot.household.country.tolist() == [current_country]
    reloaded = Simulation(dataset=snapshot, scenario=no_economic_assumptions)
    assert labels(reloaded, "country") == ["ENGLAND"]
    reloaded.set_input("local_authority", YEAR, ["CITY_OF_EDINBURGH"])
    assert labels(reloaded, "region") == ["SCOTLAND"]
    assert labels(reloaded, "country") == ["SCOTLAND"]
    assert labels(original, "country", YEAR) == [current_country]


def test_noncontiguous_and_nested_household_subsets_keep_geography_by_identity():
    simulation = Simulation(
        situation=transport_ready_situation(
            [
                {"local_authority": {YEAR: "CARDIFF"}},
                {"region": {YEAR: "LONDON"}},
                {"local_authority": {YEAR: "OXFORD"}},
                {"region": {YEAR: "UNKNOWN"}},
                {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
            ]
        ),
        scenario=no_economic_assumptions,
    )
    original = ["WALES", "LONDON", "SOUTH_EAST", "UNKNOWN", "SCOTLAND"]
    assert labels(simulation, "region") == original
    people = np.array([False, True, False, True, True])
    with household_subset(simulation, "geography_outer", people) as subset:
        branch = subset.simulation
        assert subset.person.tolist() == [1, 3, 4]
        assert labels(branch, "region") == ["LONDON", "UNKNOWN", "SCOTLAND"]
        np.testing.assert_array_equal(
            branch.calculate("household_id", YEAR), [1002, 1004, 1005]
        )
        # Newer councils supersede the genuine earlier region/UNKNOWN per ID;
        # the parent's historical UNKNOWN remains supplied and unchanged.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            branch.set_input(
                "local_authority", YEAR + 1, ["CITY_OF_LONDON", "MAIDSTONE", "CARDIFF"]
            )
            assert labels(branch, "region", YEAR + 1) == [
                "LONDON",
                "SOUTH_EAST",
                "WALES",
            ]
            assert labels(branch, "country", YEAR + 1) == [
                "ENGLAND",
                "ENGLAND",
                "WALES",
            ]
        assert not [
            item for item in caught if "Contradictory supplied" in str(item.message)
        ]
        with household_subset(
            branch, "geography_inner", np.array([True, False, True])
        ) as nested:
            assert nested.person.tolist() == [0, 2]
            assert labels(nested.simulation, "region", YEAR + 1) == ["LONDON", "WALES"]
            assert labels(nested.simulation, "country", YEAR + 1) == [
                "ENGLAND",
                "WALES",
            ]
            np.testing.assert_array_equal(
                nested.simulation.calculate("household_id", YEAR), [1002, 1005]
            )
        assert "geography_inner" not in branch.branches
    assert "geography_outer" not in simulation.branches
    assert labels(simulation, "region") == original
    assert labels(simulation, "region", YEAR + 1) == original


@pytest.mark.parametrize("crossed", [False, True], ids=["parallel", "crossed"])
def test_axis_replicas_preserve_sparse_and_default_equal_geography(crossed):
    data = situation(
        [
            {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}},
            {"region": {YEAR: "LONDON"}},
        ]
    )
    earnings = {
        "name": "employment_income",
        "index": 0,
        "period": YEAR,
        "min": 10_000,
        "max": 30_000,
        "count": 3,
    }
    pension = {
        "name": "private_pension_income",
        "index": 1,
        "period": YEAR,
        "min": 0,
        "max": 1_000 if crossed else 2_000,
        "count": 2 if crossed else 3,
    }
    data["axes"] = [[earnings], [pension]] if crossed else [[earnings, pension]]
    simulation = Simulation(situation=data, scenario=no_economic_assumptions)
    cells = 6 if crossed else 3
    assert simulation.populations["household"].count == 2 * cells
    np.testing.assert_allclose(
        np.asarray(simulation.calculate("employment_income", YEAR))[::2],
        [10_000, 20_000, 30_000] * (2 if crossed else 1),
    )
    np.testing.assert_allclose(
        np.asarray(simulation.calculate("private_pension_income", YEAR))[1::2],
        [0, 0, 0, 1_000, 1_000, 1_000] if crossed else [0, 1_000, 2_000],
    )
    assert labels(simulation, "brma") == ["LOTHIAN", "INNER_SOUTH_EAST_LONDON"] * cells
    assert labels(simulation, "region") == ["SCOTLAND", "LONDON"] * cells
    assert labels(simulation, "country") == ["SCOTLAND", "ENGLAND"] * cells
    # A generated Scottish region must move; genuine default-equal London
    # remains an override when a same-period council lies outside London.
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation.set_input("local_authority", YEAR, ["CARDIFF", "OXFORD"] * cells)
    assert labels(simulation, "region", YEAR + 1) == ["WALES", "LONDON"] * cells
    assert labels(simulation, "country", YEAR + 1) == ["WALES", "ENGLAND"] * cells


def test_calculate_all_export_does_not_turn_inferred_geography_into_input():
    data = transport_ready_situation(sparse_transport_inputs())
    for household in data["households"].values():
        household.update(
            council_tax={YEAR: 1_000},
            water_and_sewerage_charges={YEAR: 500},
            rent={YEAR: 10_000},
            tenure_type={YEAR: "RENT_PRIVATELY"},
        )
    donor = Simulation(situation=data, scenario=no_economic_assumptions)
    simulation = Microsimulation(
        dataset=UKSingleYearDataset.from_simulation(donor, YEAR),
        scenario=no_economic_assumptions,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exported = simulation.calculate_all(YEAR)
        # Default economic projection is deliberately enabled on this reload.
        restored = Simulation(dataset=exported)
        assert_transport_geography(restored)
        assert np.all(restored.calculate("council_tax", YEAR + 1) > 0)
        restored.set_input("local_authority", YEAR + 1, ["CARDIFF", "CITY_OF_LONDON"])
        assert labels(restored, "region", YEAR + 1) == ["WALES", "LONDON"]
        assert labels(restored, "country", YEAR + 1) == ["WALES", "ENGLAND"]
        assert labels(restored, "brma", YEAR + 1) == [
            "CARDIFF",
            "INNER_SOUTH_EAST_LONDON",
        ]
    assert not [
        item for item in caught if "Contradictory supplied" in str(item.message)
    ]
    assert_transport_geography(simulation)
    assert_transport_geography(donor)


def _raw_geography_names(frame, column, possible_values):
    """Decode the existing encoded export only for the literal test oracle."""
    from policyengine_core.enums import EnumArray

    values = frame[column].to_numpy()
    assert values.dtype.kind in "iu"
    return EnumArray(values.astype(np.int16), possible_values).decode_to_str().tolist()


def _input_presence(frame, column):
    return dict(frame.attrs["policyengine_uk.geography_input_masks"]["masks"])[column]


def _assert_not_genuine(frame, column):
    # A physical padded column is allowed; an invented supplied fact is not.
    if column in frame:
        assert not any(value for _, value in _input_presence(frame, column))


# Dated geography contracts R1-R18. ONS literals below use the sealed fixture
# at fixtures/geography/ons_local_authority_regions.json (May2026/Dec2020).
# No expected geography calls the production resolver.


@pytest.mark.parametrize("years", [(2024, 2025, 2026), (2026, 2025, 2024)])
def test_newer_council_wins_without_retiming_an_older_region(years):
    simulation = Simulation(
        situation=situation(
            [
                {
                    "region": {2024: "LONDON"},
                    "local_authority": {2026: "CITY_OF_EDINBURGH"},
                }
            ]
        )
    )
    for year in years:
        assert labels(simulation, "region", year) == [
            "SCOTLAND" if year == 2026 else "LONDON"
        ]
        assert labels(simulation, "country", year) == [
            "SCOTLAND" if year == 2026 else "ENGLAND"
        ]
    simulation.reset_calculations()
    for copied in [
        simulation.clone(),
        simulation.get_branch("dated_move", clone_system=True),
    ]:
        assert labels(copied, "region", 2026) == ["SCOTLAND"]
        assert labels(copied, "region", 2024) == ["LONDON"]
    assert _raw_geography_names(
        simulation.to_input_dataframe(), "region__2024", Region
    ) == ["LONDON"]
    assert "region__2026" not in simulation.to_input_dataframe()


@pytest.mark.parametrize("old_council", ["CITY_OF_EDINBURGH", "MAIDSTONE"])
def test_newer_region_makes_only_the_incompatible_historical_council_stale(old_council):
    simulation = Simulation(
        situation=situation(
            [{"local_authority": {2024: old_council}, "region": {2026: "LONDON"}}]
        )
    )
    assert labels(simulation, "region", 2026) == ["LONDON"]
    assert labels(simulation, "country", 2026) == ["ENGLAND"]
    assert labels(simulation, "brma", 2026) == ["INNER_SOUTH_EAST_LONDON"]
    with pytest.raises(ValueError, match="(?i)council|local_authority"):
        simulation.calculate("local_authority", 2026)
    # Explicit default-equal Maidstone is a source, unlike an omitted council.
    assert labels(simulation, "local_authority", 2024) == [old_council]
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation.set_input("local_authority", 2026, ["OXFORD"])
    assert labels(simulation, "local_authority", 2026) == ["OXFORD"]
    assert labels(simulation, "region", 2026) == ["LONDON"]
    assert labels(simulation, "country", 2026) == ["ENGLAND"]


def test_newer_agreeing_region_keeps_the_real_council_effective():
    simulation = Simulation(
        situation=situation(
            [
                {
                    "local_authority": {2024: "CITY_OF_EDINBURGH"},
                    "region": {2026: "SCOTLAND"},
                },
                {"region": {2026: "SCOTLAND"}},
            ]
        )
    )
    assert labels(simulation, "local_authority", 2026) == [
        "CITY_OF_EDINBURGH",
        "MAIDSTONE",
    ]
    assert labels(simulation, "region", 2026) == ["SCOTLAND", "SCOTLAND"]


@pytest.mark.parametrize(
    "region_year,council_year,expected,stale",
    [
        (2024, 2026, "SCOTLAND", False),
        (2026, 2024, "UNKNOWN", True),
        (2026, 2026, "UNKNOWN", False),
    ],
)
def test_unknown_is_a_dated_value_and_only_a_newer_unknown_stales_a_council(
    region_year, council_year, expected, stale
):
    simulation = Simulation(
        situation=situation(
            [
                {
                    "region": {region_year: "UNKNOWN"},
                    "local_authority": {council_year: "CITY_OF_EDINBURGH"},
                }
            ]
        )
    )
    assert labels(simulation, "region", 2026) == [expected]
    assert labels(simulation, "country", 2026) == [expected]
    if stale:
        with pytest.raises(ValueError, match="(?i)council|local_authority"):
            simulation.calculate("local_authority", 2026)
    else:
        assert labels(simulation, "local_authority", 2026) == ["CITY_OF_EDINBURGH"]


@pytest.mark.parametrize(
    "country,expected",
    [({2026: "UNKNOWN"}, "UNKNOWN"), ({}, "SCOTLAND"), ({2024: "ENGLAND"}, "SCOTLAND")],
)
def test_current_unknown_country_and_older_country_keep_their_distinct_contracts(
    country, expected
):
    row = {"local_authority": {2026: "CITY_OF_EDINBURGH"}}
    if country:
        row["country"] = country
    simulation = Simulation(situation=situation([row]))
    assert labels(simulation, "region", 2026) == ["SCOTLAND"]
    assert labels(simulation, "country", 2026) == [expected]


_EFFECTIVE_NATION_CONFLICTS = [
    (("local_authority", "CITY_OF_EDINBURGH"), ("country", "ENGLAND")),
    (("region", "WALES"), ("country", "SCOTLAND")),
    (("region", "LONDON"), ("local_authority", "CITY_OF_EDINBURGH")),
    (
        ("region", "UNKNOWN"),
        ("local_authority", "CITY_OF_EDINBURGH"),
        ("country", "ENGLAND"),
    ),
]


@pytest.mark.parametrize(
    "ordered",
    [order for pairs in _EFFECTIVE_NATION_CONFLICTS for order in permutations(pairs)],
)
def test_completed_build_rejects_every_effective_known_nation_conflict(ordered):
    inputs = {field: {YEAR: value} for field, value in ordered}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError, match="(?i)contradict|nation") as caught:
            Simulation(situation=situation([inputs]))
    text = str(caught.value)
    assert "household0" in text
    conflicting = [field for field, value in ordered if value != "UNKNOWN"]
    assert all(field in text for field in conflicting)
    assert "2026" in text


@pytest.mark.parametrize(
    "inputs,region,country",
    [
        ({"region": {YEAR: "UNKNOWN"}}, "UNKNOWN", "UNKNOWN"),
        (
            {
                "region": {YEAR: "UNKNOWN"},
                "local_authority": {YEAR: "CITY_OF_EDINBURGH"},
                "country": {YEAR: "UNKNOWN"},
            },
            "UNKNOWN",
            "UNKNOWN",
        ),
        (
            {
                "local_authority": {2024: "CITY_OF_EDINBURGH"},
                "region": {YEAR: "LONDON"},
                "country": {YEAR: "ENGLAND"},
            },
            "LONDON",
            "ENGLAND",
        ),
    ],
)
def test_unknown_and_stale_historical_councils_do_not_invent_known_nation_conflicts(
    inputs, region, country
):
    simulation = Simulation(situation=situation([inputs]))
    assert labels(simulation, "region") == [region]
    assert labels(simulation, "country") == [country]


def _earned_world(region="SCOTLAND", year=2028, benefit=False, reform=None):
    data = situation(
        [
            {
                "region": {2026: region},
                "rent": {2026: 25_000},
                "tenure_type": {2026: "RENT_FROM_COUNCIL"},
                "council_tax": {2026: 0},
            }
        ],
        sizes=[2] if benefit else [1],
    )
    data["people"]["person0_0"]["employment_income"] = {
        2026: 6_000 if benefit else 50_000,
        year: 6_000 if benefit else 50_000,
    }
    data["benunits"]["benunit0"]["claims_universal_credit"] = {2026: True, year: True}
    scenario = (
        no_economic_assumptions
        if reform is None
        else no_economic_assumptions + Scenario.from_reform(reform)
    )
    return Simulation(situation=data, scenario=scenario)


@pytest.mark.parametrize("variable", ["income_tax", "universal_credit"])
@pytest.mark.parametrize("period_order", [(2026, "2026-01"), ("2026-01", 2026)])
def test_future_conflict_blocks_recalculated_money_only_for_its_requested_year(
    variable, period_order
):
    parent = _earned_world(benefit=variable == "universal_credit")
    expected = float(parent.calculate(variable, 2028)[0])
    assert expected > 0
    branch = parent.get_branch("future_conflict", clone_system=True)
    branch.calculate(
        variable, 2028
    )  # A real prior result; the setter below invalidates it.
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        branch.set_input("country", 2028, ["ENGLAND"])
    for requested in period_order:
        np.testing.assert_allclose(
            branch.calculate(variable, requested), parent.calculate(variable, requested)
        )
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        branch.calculate(variable, 2028)
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        branch.calculate(variable, "2028-01")
    branch.set_input("country", 2028, ["SCOTLAND"])
    assert float(branch.calculate(variable, 2028)[0]) == pytest.approx(
        expected, abs=0.01
    )
    assert float(parent.calculate(variable, 2028)[0]) == pytest.approx(
        expected, abs=0.01
    )


@pytest.mark.parametrize(
    "variable,requested",
    [
        ("income_tax", "not-a-period"),
        ("income_tax", "2028-02-03"),
        ("income_tax", "year:2028:2"),
        ("not_a_policyengine_variable", 2028),
    ],
)
def test_core_request_errors_precede_an_unresolved_geography_error(variable, requested):
    healthy = _earned_world()
    with pytest.raises(Exception) as core_error:
        healthy.calculate(variable, requested)
    contradictory = _earned_world()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        contradictory.set_input("country", 2028, ["ENGLAND"])
    with pytest.raises(type(core_error.value)) as actual:
        contradictory.calculate(variable, requested)
    assert str(actual.value) == str(core_error.value)


def test_same_period_english_disagreement_warns_with_region_tie_authority():
    import re

    with pytest.warns(UserWarning, match="Contradictory supplied") as caught:
        simulation = Simulation(
            situation=situation(
                [
                    {
                        "region": {YEAR: "LONDON"},
                        "local_authority": {YEAR: "OXFORD"},
                    }
                ]
            )
        )
    assert labels(simulation, "region") == ["LONDON"]
    assert labels(simulation, "country") == ["ENGLAND"]
    assert labels(simulation, "local_authority") == ["OXFORD"]
    text = " ".join(str(item.message) for item in caught)
    assert all(
        token in text for token in ["household0", "region", "local_authority", "2026"]
    )
    assert re.search(
        r"(?i)(?:\bselected(?:\s+field)?\s*[:=]\s*region\b|"
        r"\bregion\s+(?:wins|is\s+selected)\b)",
        text,
    )


def test_sparse_dated_winners_do_not_use_a_neighbors_padding_or_default_as_fact():
    simulation = Simulation(
        situation=transport_ready_situation(
            [
                {
                    "region": {2024: "LONDON"},
                    "local_authority": {2026: "CITY_OF_EDINBURGH"},
                },
                {"local_authority": {2024: "MAIDSTONE"}, "region": {2026: "WALES"}},
                {
                    "local_authority": {2024: "CITY_OF_EDINBURGH"},
                    "region": {2026: "UNKNOWN"},
                },
                {},
            ]
        ),
        scenario=no_economic_assumptions,
    )
    assert labels(simulation, "region", 2026) == [
        "SCOTLAND",
        "WALES",
        "UNKNOWN",
        "LONDON",
    ]
    assert labels(simulation, "country", 2026) == [
        "SCOTLAND",
        "WALES",
        "UNKNOWN",
        "ENGLAND",
    ]
    frame = simulation.to_input_dataframe()
    assert _input_presence(frame, "local_authority__2024") == (
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    )
    assert _input_presence(frame, "region__2026") == (
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    )
    raw = _raw_geography_names(frame, "local_authority__2024", LocalAuthority)
    assert raw[1:3] == ["MAIDSTONE", "CITY_OF_EDINBURGH"]
    # Both truly supplied old councils are stale; the omitted fourth is not.
    for selected in [
        np.array([False, True, False, False]),
        np.array([False, False, True, False]),
    ]:
        with household_subset(simulation, "explicit_stale", selected) as subset:
            with pytest.raises(ValueError, match="(?i)council|local_authority"):
                subset.simulation.calculate("local_authority", 2026)
    with household_subset(
        simulation, "omitted_council", np.array([False, False, False, True])
    ) as subset:
        assert labels(subset.simulation, "local_authority", 2026) == ["MAIDSTONE"]


@pytest.mark.parametrize(
    "order",
    [
        ("region", "country", "local_authority", "brma"),
        ("brma", "local_authority", "country", "region"),
    ],
)
@pytest.mark.parametrize("precompute", [False, True])
@pytest.mark.parametrize("stale", [False, True])
def test_all_public_geography_reads_share_one_recency_decision(
    order, precompute, stale
):
    first = (
        {"local_authority": {2024: "CITY_OF_EDINBURGH"}, "region": {YEAR: "LONDON"}}
        if stale
        else {
            "region": {2024: "LONDON"},
            "local_authority": {YEAR: "CITY_OF_EDINBURGH"},
        }
    )
    simulation = Simulation(situation=situation([first, {"country": {YEAR: "WALES"}}]))
    if precompute:
        assert labels(simulation, "region", 2024) == [
            "SCOTLAND" if stale else "LONDON",
            "LONDON",
        ]
        assert labels(simulation, "local_authority", 2024) == [
            "CITY_OF_EDINBURGH" if stale else "MAIDSTONE",
            "MAIDSTONE",
        ]
    expected = {
        "region": ["LONDON" if stale else "SCOTLAND", "WALES"],
        "country": ["ENGLAND" if stale else "SCOTLAND", "WALES"],
        "local_authority": ["CITY_OF_EDINBURGH", "MAIDSTONE"],
        "brma": ["INNER_SOUTH_EAST_LONDON" if stale else "LOTHIAN", "CARDIFF"],
    }
    for variables in [order, tuple(reversed(order))]:
        for variable in variables:
            if stale and variable == "local_authority":
                with pytest.raises(ValueError, match="(?i)council|local_authority"):
                    simulation.calculate(variable, YEAR)
            else:
                assert labels(simulation, variable) == expected[variable]
        simulation.reset_calculations()


@pytest.mark.parametrize("repair", ["replace_region", "delete_country"])
def test_warning_callback_repair_reselects_the_financial_result_after_invalidation(
    monkeypatch, repair
):
    simulation = _earned_world(year=YEAR)
    scottish = float(simulation.calculate("income_tax", YEAR)[0])
    england = float(_earned_world("LONDON", year=YEAR).calculate("income_tax", YEAR)[0])
    assert not np.isclose(scottish, england)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.set_input("country", YEAR, ["ENGLAND"])
    calls = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        original = warnings.showwarning

        def repair_once(message, category, filename, lineno, file=None, line=None):
            if str(message).startswith("Contradictory supplied") and not calls:
                calls.append(str(message))
                if repair == "replace_region":
                    simulation.set_input("region", YEAR, ["LONDON"])
                else:
                    simulation.delete_arrays("country")
            return original(message, category, filename, lineno, file, line)

        with monkeypatch.context() as patch:
            patch.setattr(warnings, "showwarning", repair_once)
            result = float(simulation.calculate("income_tax", YEAR)[0])
    assert len(calls) == 1
    assert (
        len(
            [
                item
                for item in caught
                if str(item.message).startswith("Contradictory supplied")
            ]
        )
        == 1
    )
    assert result == pytest.approx(
        england if repair == "replace_region" else scottish, abs=0.01
    )


def test_warning_callback_exception_identity_and_next_call_guard_cleanup(monkeypatch):
    simulation = _earned_world(year=YEAR)
    expected = float(simulation.calculate("income_tax", YEAR)[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.set_input("country", YEAR, ["ENGLAND"])
    marker = RuntimeError("caller warning failure")

    def fail_warning(*args, **kwargs):
        raise marker

    with warnings.catch_warnings():
        warnings.simplefilter("always", UserWarning)
        with monkeypatch.context() as patch:
            patch.setattr(warnings, "showwarning", fail_warning)
            with pytest.raises(RuntimeError) as caught:
                simulation.calculate("income_tax", YEAR)
    assert caught.value is marker
    simulation.set_input("country", YEAR, ["SCOTLAND"])
    assert float(simulation.calculate("income_tax", YEAR)[0]) == pytest.approx(
        expected, abs=0.01
    )
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        simulation.set_input("country", YEAR, ["ENGLAND"])
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        simulation.calculate("income_tax", YEAR)


@pytest.mark.parametrize("layout", ["original", "reordered", "subset"])
def test_warning_ids_are_bounded_real_population_ids_in_population_order(layout):
    import re

    # Applicable 2024 Welsh facts disagree with a genuinely current 2026 country.
    data = transport_ready_situation(
        [
            {
                "region": {2024: "WALES"},
                "local_authority": {2024: "CARDIFF"},
                "country": {YEAR: "WALES"},
            }
            for _ in range(6)
        ]
    )
    simulation = Simulation(situation=data, scenario=no_economic_assumptions)
    if layout == "reordered":
        snapshot = UKSingleYearDataset.from_simulation(simulation, fiscal_year=YEAR)
        snapshot.household = snapshot.household.iloc[[5, 3, 1, 4, 0, 2]].reset_index(
            drop=True
        )
        simulation = Simulation(dataset=snapshot, scenario=no_economic_assumptions)

    def check(target):
        ids = target.calculate("household_id", YEAR).tolist()
        with pytest.warns(UserWarning, match="Contradictory supplied") as caught:
            target.set_input("country", YEAR, ["ENGLAND"] * len(ids))
        text = " ".join(str(item.message) for item in caught)
        assert re.search(r"\b" + str(len(ids)) + r"\b", text)
        positions = []
        for identifier in ids[:3]:
            match = re.search(r"\b" + str(int(identifier)) + r"\b", text)
            assert match is not None
            positions.append(match.start())
        assert positions == sorted(positions)
        assert all(
            re.search(r"\b" + str(int(identifier)) + r"\b", text) is None
            for identifier in ids[3:]
        )
        assert re.search("(?i)omitted|more|additional", text)
        assert all(
            token in text
            for token in ["region", "country", "local_authority", "2024", "2026"]
        )
        assert re.search("(?i)unresolved", text) and re.search(
            "(?i)nation|country", text
        )

    if layout == "subset":
        with household_subset(
            simulation, "warning_ids", np.array([True, False, True, True, False, True])
        ) as subset:
            check(subset.simulation)
    else:
        check(simulation)


def test_lossless_dated_input_frame_neither_calculates_nor_promotes_a_winner(
    monkeypatch,
):
    simulation = Simulation(
        situation=transport_ready_situation(
            [
                {
                    "region": {2024: "LONDON"},
                    "local_authority": {2026: "CITY_OF_EDINBURGH"},
                },
                {"region": {2024: "WALES"}},
            ]
        ),
        scenario=no_economic_assumptions,
    )

    def forbidden(*args, **kwargs):
        pytest.fail("lossless input export must not calculate geography")

    with monkeypatch.context() as patch:
        patch.setattr(simulation, "calculate", forbidden)
        before = simulation.to_input_dataframe()
    assert _raw_geography_names(before, "region__2024", Region) == ["LONDON", "WALES"]
    assert (
        _raw_geography_names(before, "local_authority__2026", LocalAuthority)[0]
        == "CITY_OF_EDINBURGH"
    )
    assert _input_presence(before, "local_authority__2026") == ((1, True), (2, False))
    assert "region__2026" not in before
    assert labels(simulation, "region") == ["SCOTLAND", "WALES"]
    pd.testing.assert_frame_equal(simulation.to_input_dataframe(), before)
    reloaded = Simulation(dataset=before, scenario=no_economic_assumptions)
    assert labels(reloaded, "region") == ["SCOTLAND", "WALES"]
    pd.testing.assert_frame_equal(reloaded.to_input_dataframe(), before)


@pytest.mark.parametrize("layout", ["reordered", "subset_before_reload"])
def test_snapshot_horizon_keeps_dated_moves_without_replaying_future_sources(layout):
    simulation = Simulation(
        situation=transport_ready_situation(
            [
                {
                    "region": {2024: "LONDON"},
                    "local_authority": {2026: "CITY_OF_EDINBURGH", 2028: "CARDIFF"},
                },
                {"region": {2024: "WALES"}, "local_authority": {2026: "CARDIFF"}},
            ]
        ),
        scenario=no_economic_assumptions,
    )
    original = UKSingleYearDataset.from_simulation(simulation, fiscal_year=2026)
    originals = {
        name: getattr(original, name).copy(deep=True)
        for name in ["person", "benunit", "household"]
    }
    metadata = {name: deepcopy(frame.attrs) for name, frame in originals.items()}
    snapshot = deepcopy(original)
    if layout == "reordered":
        snapshot.household = snapshot.household.iloc[::-1].reset_index(drop=True)
        expected_old = {1001: "LONDON", 1002: "WALES"}
        expected_now = {1001: "SCOTLAND", 1002: "WALES"}
    else:
        snapshot.household = snapshot.household.loc[
            snapshot.household.household_id == 1001
        ].reset_index(drop=True)
        snapshot.person = snapshot.person.loc[
            snapshot.person.person_household_id == 1001
        ].reset_index(drop=True)
        benunits = set(snapshot.person.person_benunit_id)
        snapshot.benunit = snapshot.benunit.loc[
            snapshot.benunit.benunit_id.isin(benunits)
        ].reset_index(drop=True)
        expected_old, expected_now = {1001: "LONDON"}, {1001: "SCOTLAND"}
    before_reload_attrs = {
        name: deepcopy(getattr(snapshot, name).attrs) for name in originals
    }
    restored = Simulation(dataset=snapshot, scenario=no_economic_assumptions)

    def by_id(variable, year):
        return dict(
            zip(
                restored.calculate("household_id", year).tolist(),
                labels(restored, variable, year),
            )
        )

    assert by_id("region", 2024) == expected_old
    for year in [2026, 2028]:
        assert by_id("region", year) == expected_now
        assert by_id("country", year) == expected_now
    frame = restored.to_input_dataframe()
    _assert_not_genuine(frame, "region__2026")
    _assert_not_genuine(frame, "local_authority__2028")
    assert (
        dict(
            zip(
                frame["person_household_id__2024"],
                _raw_geography_names(frame, "region__2024", Region),
            )
        )
        == expected_old
    )
    expected_ids = tuple((identifier - 1000, True) for identifier in expected_now)
    assert tuple(sorted(_input_presence(frame, "local_authority__2026"))) == tuple(
        sorted(expected_ids)
    )
    for name, original_frame in originals.items():
        pd.testing.assert_frame_equal(getattr(original, name), original_frame)
        assert getattr(original, name).attrs == metadata[name]
        assert getattr(snapshot, name).attrs == before_reload_attrs[name]
    assert labels(simulation, "region", 2028) == ["WALES", "WALES"]


@pytest.mark.parametrize("via_councils", [False, True])
def test_snapshot_replays_intermediate_moves_before_brma_carry_expiry(via_councils):
    inputs = {"brma": {2024: "GREATER_GLASGOW"}}
    if via_councils:
        inputs["local_authority"] = {
            2024: "CITY_OF_EDINBURGH",
            2025: "CARDIFF",
            2026: "CITY_OF_EDINBURGH",
        }
    else:
        inputs["region"] = {2024: "SCOTLAND", 2025: "WALES", 2026: "SCOTLAND"}
    simulation = Simulation(
        situation=transport_ready_situation([inputs]), scenario=no_economic_assumptions
    )
    assert labels(simulation, "brma", 2026) == ["LOTHIAN"]
    snapshot = UKSingleYearDataset.from_simulation(simulation, fiscal_year=2026)
    restored = Simulation(dataset=snapshot, scenario=no_economic_assumptions)
    assert labels(restored, "region", 2025) == ["WALES"]
    assert labels(restored, "country", 2025) == ["WALES"]
    assert labels(restored, "brma", 2025) == ["CARDIFF"]
    history = restored.to_input_dataframe()
    field, possible = (
        ("local_authority", LocalAuthority) if via_councils else ("region", Region)
    )
    assert _raw_geography_names(history, field + "__2025", possible) == [
        "CARDIFF" if via_councils else "WALES"
    ]
    assert _input_presence(history, field + "__2025") == ((1, True),)
    assert labels(restored, "brma", 2026) == ["LOTHIAN"]
    assert labels(restored, "brma", 2027) == ["LOTHIAN"]
    restored.set_input("brma", 2027, ["GREATER_GLASGOW"])
    assert labels(restored, "brma", 2027) == ["GREATER_GLASGOW"]


@pytest.mark.parametrize("operation", ["calculate_all", "snapshot"])
def test_stale_council_export_is_lossless_but_actual_council_consumers_reject(
    operation,
):
    simulation = Simulation(
        situation=transport_ready_situation(
            [
                {
                    "local_authority": {2024: "CITY_OF_EDINBURGH"},
                    "region": {2026: "LONDON"},
                }
            ]
        ),
        scenario=no_economic_assumptions,
    )
    frame = simulation.to_input_dataframe()
    assert _raw_geography_names(frame, "local_authority__2024", LocalAuthority) == [
        "CITY_OF_EDINBURGH"
    ]
    assert _raw_geography_names(frame, "region__2026", Region) == ["LONDON"]
    assert labels(simulation, "region", 2026) == ["LONDON"]
    assert "local_authority" in simulation.input_variables
    with pytest.raises(ValueError, match="(?i)council|local_authority"):
        if operation == "calculate_all":
            simulation.calculate_all(2026)
        else:
            UKSingleYearDataset.from_simulation(simulation, fiscal_year=2026)
    pd.testing.assert_frame_equal(simulation.to_input_dataframe(), frame)


@pytest.mark.parametrize("variable", ["income_tax", "universal_credit"])
def test_dated_earned_income_move_matches_independent_explicit_ons_financial_world(
    variable,
):
    # ONS literal: CITY_OF_EDINBURGH -> SCOTLAND -> SCOTLAND. Both worlds
    # retain a real current council; no eligibility/rate intermediate is supplied.
    data = situation(
        [
            {
                "region": {2024: "LONDON"},
                "local_authority": {2026: "CITY_OF_EDINBURGH"},
                "rent": {2026: 25_000},
                "tenure_type": {2026: "RENT_FROM_COUNCIL"},
                "council_tax": {2026: 0},
            }
        ],
        sizes=[2] if variable == "universal_credit" else [1],
    )
    data["people"]["person0_0"]["employment_income"] = {
        2026: 6_000 if variable == "universal_credit" else 50_000
    }
    data["benunits"]["benunit0"]["claims_universal_credit"] = {2026: True}
    explicit = deepcopy(data)
    explicit["households"]["household0"]["region"] = {2026: "SCOTLAND"}
    explicit["households"]["household0"]["country"] = {2026: "SCOTLAND"}
    moved, known = Simulation(situation=data), Simulation(situation=explicit)
    expected = known.calculate(variable, 2026)
    assert float(expected[0]) > 0
    np.testing.assert_allclose(
        moved.calculate(variable, 2026), expected, atol=0.01, rtol=0
    )
    np.testing.assert_array_equal(
        moved.calculate("pays_scottish_income_tax", 2026),
        known.calculate("pays_scottish_income_tax", 2026),
    )
    assert bool(moved.calculate("pays_scottish_income_tax", 2026)[0])


@pytest.mark.parametrize("reform", [None, WelshRegion, WelshCountry])
@pytest.mark.parametrize("current_region", [False, True])
def test_recency_removes_only_superseded_input_overlay_and_preserves_custom_authority(
    reform, current_region
):
    inputs = {
        "region": {2024: "LONDON"},
        "local_authority": {2026: "CITY_OF_EDINBURGH"},
    }
    if current_region:
        inputs["region"][2026] = "SCOTLAND"
    simulation = Simulation(situation=situation([inputs]), reform=reform)
    assert labels(simulation, "region", 2026) == [
        "WALES" if reform is WelshRegion and not current_region else "SCOTLAND"
    ]
    assert labels(simulation, "country", 2026) == [
        "WALES"
        if reform is WelshCountry or (reform is WelshRegion and not current_region)
        else "SCOTLAND"
    ]
    assert labels(simulation, "local_authority", 2026) == ["CITY_OF_EDINBURGH"]
    raw = simulation.to_input_dataframe()
    assert _raw_geography_names(raw, "region__2024", Region) == ["LONDON"]
    assert ("region__2026" in raw) is current_region


@pytest.mark.parametrize(
    "entry", ["frame_constructor", "frame_rebuild", "situation_rebuild"]
)
def test_completed_public_reload_rejects_the_known_council_country_conflict_under_unknown(
    entry,
):
    row = {
        "region": {YEAR: "UNKNOWN"},
        "local_authority": {YEAR: "CITY_OF_EDINBURGH"},
        "country": {YEAR: "ENGLAND"},
    }
    frame = pd.DataFrame(
        {
            "person_id__2026": [1],
            "person_benunit_id__2026": [101],
            "person_household_id__2026": [1001],
            "age__2026": [40],
            "region__2026": ["UNKNOWN"],
            "country__2026": ["ENGLAND"],
            "local_authority__2026": ["CITY_OF_EDINBURGH"],
        }
    )
    target = (
        Simulation(situation=situation([{}])) if entry != "frame_constructor" else None
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError, match="(?i)contradict|nation") as caught:
            if entry == "frame_constructor":
                Simulation(dataset=frame, scenario=no_economic_assumptions)
            elif entry == "frame_rebuild":
                target.build_from_dataframe(frame)
            else:
                target.build_from_situation(situation([row]))
    text = str(caught.value)
    assert "household0" in text if entry == "situation_rebuild" else "1001" in text
    assert all(token in text for token in ["local_authority", "country", "2026"])


def test_public_multi_year_sum_checks_only_contributing_years_and_rechecks_after_repair():
    parent = _earned_world()
    first_two = parent.calculate_add("income_tax", "year:2026:2")
    all_three = parent.calculate_add("income_tax", "year:2026:3")
    branch = parent.get_branch("summed_future_conflict", clone_system=True)
    with pytest.warns(UserWarning, match="Contradictory supplied"):
        branch.set_input("country", 2028, ["ENGLAND"])
    np.testing.assert_allclose(
        branch.calculate_add("income_tax", "year:2026:2"), first_two
    )
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        branch.calculate_add("income_tax", "year:2026:3")
    branch.set_input("country", 2028, ["SCOTLAND"])
    np.testing.assert_allclose(
        branch.calculate_add("income_tax", "year:2026:3"), all_three
    )
    np.testing.assert_allclose(
        parent.calculate_add("income_tax", "year:2026:3"), all_three
    )


def test_real_financial_top_level_return_observes_the_existing_holder_route(
    monkeypatch,
):
    from policyengine_core.simulations import Simulation as CoreSimulation

    simulation = _earned_world(year=YEAR)
    first = simulation.calculate("income_tax", YEAR)
    assert float(first[0]) > 0
    stored = simulation.get_holder("income_tax").get_array(
        core_period(YEAR), simulation.branch_name
    )
    assert stored is first
    original = CoreSimulation._calculate
    entries = []

    def observe(target, name, requested=None):
        if target is simulation and name == "income_tax":
            cached = target.get_holder(name).get_array(requested, target.branch_name)
            result = original(target, name, requested)
            entries.append((cached, result))
            return result
        return original(target, name, requested)

    with monkeypatch.context() as patch:
        patch.setattr(CoreSimulation, "_calculate", observe)
        second = simulation.calculate("income_tax", YEAR)
    # UK forces decode=True at the outer boundary: this is the real holder
    # route, not Core's decode=False fast shortcut or a seeded cache result.
    assert len(entries) == 1
    assert entries[0][0] is stored and entries[0][1] is stored and second is stored
    np.testing.assert_array_equal(second, first)


def test_real_financial_nested_read_observes_the_existing_core_fast_route(monkeypatch):
    from policyengine_core.simulations import Simulation as CoreSimulation
    from policyengine_uk.model_api import Person, Variable, YEAR as ANNUAL

    entries, observed = [], []

    class Probe(Reform):
        def apply(self):
            class geography_cache_route_probe(Variable):
                label = "Geography nested financial cache route probe"
                value_type = float
                entity = Person
                definition_period = ANNUAL

                def formula(person, requested, parameters):
                    target = person.simulation
                    assert target.tracer.stack and not target.trace
                    first = target.calculate(
                        "income_tax", requested, decode_enums=False
                    )
                    assert float(first[0]) > 0
                    assert target._fast_cache.get(("income_tax", requested)) is first
                    calls = len(entries)
                    second = target.calculate(
                        "income_tax", requested, decode_enums=False
                    )
                    observed.append((first, second, calls, len(entries)))
                    return second

            self.add_variable(geography_cache_route_probe)

    simulation = _earned_world(year=YEAR, reform=Probe)
    original = CoreSimulation._calculate

    def observe(target, name, requested=None):
        if target is simulation and name == "income_tax":
            entries.append((name, requested))
        return original(target, name, requested)

    with monkeypatch.context() as patch:
        patch.setattr(CoreSimulation, "_calculate", observe)
        actual = simulation.calculate("geography_cache_route_probe", YEAR)
    assert len(observed) == 1
    first, second, before, after = observed[0]
    assert first is second and before == after and before >= 1
    np.testing.assert_array_equal(actual, first)
    # No setter intervened: this proves a reachable healthy cache route only.


@pytest.mark.parametrize("mode", ["different_year", "same_stack_mutation"])
def test_nested_public_financial_read_rechecks_other_year_and_intervening_input(mode):
    from policyengine_uk.model_api import Person, Variable, YEAR as ANNUAL

    changed, entered = [], []

    class Probe(Reform):
        def apply(self):
            class geography_nested_read_probe(Variable):
                label = "Geography nested public financial read probe"
                value_type = float
                entity = Person
                definition_period = ANNUAL

                def formula(person, requested, parameters):
                    target = person.simulation
                    entered.append(bool(target.tracer.stack))
                    target.calculate("income_tax", requested)
                    if mode == "different_year":
                        return target.calculate("income_tax", requested.offset(2))
                    if not changed:
                        changed.append(True)
                        with pytest.warns(UserWarning, match="Contradictory supplied"):
                            target.set_input("country", requested, ["ENGLAND"])
                    # This same-year request follows a real setter/invalidation
                    # inside the outer formula; inherited guard coverage expires.
                    return target.calculate("income_tax", requested)

            self.add_variable(geography_nested_read_probe)

    simulation = _earned_world(reform=Probe)
    conflict_year = 2028 if mode == "different_year" else YEAR
    if mode == "different_year":
        with pytest.warns(UserWarning, match="Contradictory supplied"):
            simulation.set_input("country", conflict_year, ["ENGLAND"])
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        simulation.calculate("geography_nested_read_probe", YEAR)
    assert entered and all(entered)
    simulation.set_input("country", conflict_year, ["SCOTLAND"])
    repaired = simulation.calculate("geography_nested_read_probe", YEAR)
    expected = _earned_world().calculate("income_tax", conflict_year)
    assert float(expected[0]) > 0
    np.testing.assert_allclose(repaired, expected, atol=0.01, rtol=0)


def test_cross_field_recency_expires_old_brma_but_compatible_council_keeps_new_override():
    simulation = Simulation(
        situation=transport_ready_situation(
            [
                {
                    "region": {2024: "LONDON"},
                    "brma": {2024: "INNER_NORTH_LONDON"},
                    "local_authority": {2026: "CITY_OF_EDINBURGH"},
                }
            ]
        ),
        scenario=no_economic_assumptions,
    )
    assert labels(simulation, "brma", 2024) == ["INNER_NORTH_LONDON"]
    assert labels(simulation, "region", 2026) == ["SCOTLAND"]
    assert labels(simulation, "brma", 2026) == ["LOTHIAN"]
    simulation.set_input("brma", 2027, ["GREATER_GLASGOW"])
    simulation.set_input("local_authority", 2028, ["ABERDEEN_CITY"])
    assert labels(simulation, "region", 2028) == ["SCOTLAND"]
    assert labels(simulation, "local_authority", 2028) == ["ABERDEEN_CITY"]
    assert labels(simulation, "brma", 2028) == ["GREATER_GLASGOW"]
    restored = Simulation(
        dataset=UKSingleYearDataset.from_simulation(simulation, fiscal_year=2028),
        scenario=no_economic_assumptions,
    )
    assert labels(restored, "brma", 2028) == ["GREATER_GLASGOW"]


def _snapshot_for_requested_year_projection(geography):
    """Real public base inputs; no policy rates or eligibility intermediates."""
    data = transport_ready_situation(
        [
            {
                **deepcopy(geography),
                "household_weight": {2024: 1.0},
                "tenure_type": {2024: "RENT_PRIVATELY"},
                "rent": {2024: 10_000.0},
                "council_tax": {2024: 1_000.0},
                "water_and_sewerage_charges": {2024: 500.0},
            }
            for _ in range(6)
        ]
    )
    for household in data["households"].values():
        household.update(
            council_tax={2024: 1_000.0},
            rent={2024: 10_000.0},
            tenure_type={2024: "RENT_PRIVATELY"},
        )
    for person in data["people"].values():
        person.update(
            age={2024: 32},
            student_loan_plan={2024: "NONE"},
            student_loan_repayments={2024: 0.0},
            highest_education={2024: "TERTIARY"},
        )
    donor = Simulation(situation=data, scenario=no_economic_assumptions)
    return UKSingleYearDataset.from_simulation(donor, fiscal_year=2024)


def test_enabled_projection_does_not_carry_a_snapshot_country_beyond_its_year():
    country_only = _snapshot_for_requested_year_projection(
        {"country": {2024: "SCOTLAND"}}
    )
    england = _snapshot_for_requested_year_projection(
        {"region": {2024: "LONDON"}, "country": {2024: "ENGLAND"}}
    )
    scotland = _snapshot_for_requested_year_projection({"region": {2024: "SCOTLAND"}})
    saved = {
        name: getattr(country_only, name).copy(deep=True)
        for name in ["person", "benunit", "household"]
    }
    attrs = {name: deepcopy(frame.attrs) for name, frame in saved.items()}
    actual, explicit, persistent = (
        Simulation(dataset=snapshot) for snapshot in [country_only, england, scotland]
    )
    assert labels(actual, "country", 2024) == ["SCOTLAND"] * 6
    assert labels(actual, "region", 2026) == ["LONDON"] * 6
    assert labels(actual, "country", 2026) == ["ENGLAND"] * 6
    assert labels(persistent, "region", 2026) == ["SCOTLAND"] * 6
    differences = []
    for variable in ["council_tax", "water_and_sewerage_charges", "rent"]:
        expected = explicit.calculate(variable, 2026)
        assert np.all(expected > 0)
        np.testing.assert_allclose(
            actual.calculate(variable, 2026), expected, atol=0.01, rtol=0
        )
        differences.append(
            np.any(np.abs(persistent.calculate(variable, 2026) - expected) > 0.01)
        )
    assert any(differences)
    plans = labels(actual, "student_loan_plan", 2026)
    assert plans == labels(explicit, "student_loan_plan", 2026)
    assert "PLAN_2" in plans and "PLAN_4" not in plans
    assert "PLAN_4" in labels(persistent, "student_loan_plan", 2026)
    for name, frame in saved.items():
        pd.testing.assert_frame_equal(getattr(country_only, name), frame)
        assert getattr(country_only, name).attrs == attrs[name]


def test_enabled_projection_uses_dated_snapshot_history_for_the_newer_ons_council():
    # ONS literal: Edinburgh is Scotland. The 2022 London fact is older.
    moved = _snapshot_for_requested_year_projection(
        {
            "region": {2022: "LONDON"},
            "local_authority": {2024: "CITY_OF_EDINBURGH"},
        }
    )
    explicit = _snapshot_for_requested_year_projection(
        {
            "region": {2024: "SCOTLAND"},
            "country": {2024: "SCOTLAND"},
            "local_authority": {2024: "CITY_OF_EDINBURGH"},
        }
    )
    before = {
        name: getattr(moved, name).copy(deep=True)
        for name in ["person", "benunit", "household"]
    }
    metadata = {name: deepcopy(frame.attrs) for name, frame in before.items()}
    actual, known = Simulation(dataset=moved), Simulation(dataset=explicit)
    assert labels(actual, "region", 2026) == ["SCOTLAND"] * 6
    assert labels(actual, "country", 2026) == ["SCOTLAND"] * 6
    for variable, base in [
        ("council_tax", 1_000.0),
        ("water_and_sewerage_charges", 500.0),
        ("rent", 10_000.0),
    ]:
        expected = known.calculate(variable, 2026)
        assert np.all(expected > 0) and np.any(np.abs(expected - base) > 0.01)
        np.testing.assert_allclose(
            actual.calculate(variable, 2026), expected, atol=0.01, rtol=0
        )
    assert labels(actual, "student_loan_plan", 2026) == labels(
        known, "student_loan_plan", 2026
    )
    assert "PLAN_4" in labels(actual, "student_loan_plan", 2026)
    raw = actual.to_input_dataframe()
    assert _raw_geography_names(raw, "region__2022", Region) == ["LONDON"] * 6
    assert (
        _raw_geography_names(raw, "local_authority__2024", LocalAuthority)
        == ["CITY_OF_EDINBURGH"] * 6
    )
    for name, frame in before.items():
        pd.testing.assert_frame_equal(getattr(moved, name), frame)
        assert getattr(moved, name).attrs == metadata[name]


@pytest.mark.parametrize("entry", ["situation", "core_dataset"])
def test_stale_move_at_actual_default_year_keeps_complete_public_source_across_copy_and_two_reloads(
    monkeypatch, tmp_path, entry
):
    from copy import copy, deepcopy
    from policyengine_core.data import Dataset
    from policyengine_uk.data import UKMultiYearDataset
    from policyengine_uk.variables.gov.dwp.state_pension_age_addition import (
        state_pension_data_year,
    )
    import policyengine_uk.simulation as simulation_module

    assert Simulation.default_input_period == 2025
    identifiers = {
        "person_id": [1, 2],
        "person_benunit_id": [101, 102],
        "person_household_id": [1001, 1002],
        "benunit_id": [101, 102],
        "household_id": [1001, 1002],
    }
    data = transport_ready_situation(
        [
            {
                "local_authority": {2024: "CITY_OF_EDINBURGH"},
                "region": {2025: "LONDON"},
            },
            {"local_authority": {2024: "CARDIFF"}, "region": {2024: "WALES"}},
        ]
    )
    # The helper seeds rent/tenure defaults; apply these intended inputs after it.
    for index, (rent, tenure) in enumerate(
        [
            (12_345, "RENT_PRIVATELY"),
            (6_789, "RENT_FROM_COUNCIL"),
        ]
    ):
        data["households"][f"household{index}"].update(
            rent={2024: rent},
            tenure_type={2024: tenure},
        )
    for index, (person, age) in enumerate(zip(data["people"].values(), [70, 44])):
        person["age"] = {2024: age}
        person["person_id"][2023] = index + 1
        person["person_benunit_id"][2023] = index + 101
        person["person_household_id"][2023] = index + 1001
        person["state_pension_reported"] = {2024: 5_200 if index == 0 else 0, 2025: 0}
        person["state_pension_type"] = {2025: "BASIC" if index == 0 else "NONE"}
    for index in range(2):
        data["benunits"][f"benunit{index}"]["benunit_id"][2023] = index + 101
        data["households"][f"household{index}"]["household_id"][2023] = index + 1001

    class EarlierCoreDataset(Dataset):
        def __init__(self):
            self.arrays = {
                name: {
                    2025: np.array(values),
                    2024: np.array(values),
                    2023: np.array(values),
                }
                for name, values in identifiers.items()
            }
            self.arrays.update(
                {
                    "age": {2024: np.array([70, 44])},
                    "rent": {2024: np.array([12_345, 6_789])},
                    "tenure_type": {
                        2024: np.array(["RENT_PRIVATELY", "RENT_FROM_COUNCIL"])
                    },
                    "local_authority": {
                        "year:2024:2": np.array(["CITY_OF_EDINBURGH", "CARDIFF"])
                    },
                    "region": {2025: np.array(["LONDON", "WALES"])},
                    "state_pension_reported": {
                        2024: np.array([5_200, 0]),
                        2025: np.array([0, 0]),
                    },
                    "state_pension_type": {2025: np.array(["BASIC", "NONE"])},
                }
            )
            self.energy_price_basis = {
                "period_type": "calendar_year",
                "period_value": 2024,
            }
            self.savings_income_projection = "obr_savings_income_2022_2025"

        def load_dataset(self):
            return self.arrays

    original_core = EarlierCoreDataset() if entry == "core_dataset" else None
    original_core_arrays = (
        deepcopy(original_core.arrays) if original_core is not None else None
    )
    expected_basis = (
        original_core.energy_price_basis if original_core is not None else None
    )

    def no_eager_snapshot(*args, **kwargs):
        pytest.fail(
            "A stale-world internal load must not evaluate a dependent annual snapshot."
        )

    with monkeypatch.context() as patch:
        patch.setattr(
            UKSingleYearDataset, "from_simulation", staticmethod(no_eager_snapshot)
        )
        original = (
            Simulation(dataset=original_core, scenario=no_economic_assumptions)
            if original_core is not None
            else Simulation(situation=data, scenario=no_economic_assumptions)
        )
    assert isinstance(original.dataset, UKMultiYearDataset)
    # Identifier-only 2023 is replayed, but cannot become the pension data year.
    assert tuple(original.dataset.years) == (2024, 2025)
    before = original.to_input_dataframe()
    public_copy = original.dataset.copy()
    shallow_copy = copy(public_copy)
    deep_copy = deepcopy(public_copy)
    # Copies own their annual views; a caller edit must not mutate the source.
    public_copy[2024].person.loc[:, "age"] = [-1, -1]
    np.testing.assert_array_equal(original.dataset[2024].person.age, [70, 44])
    np.testing.assert_array_equal(shallow_copy[2024].person.age, [70, 44])
    np.testing.assert_array_equal(deep_copy[2024].person.age, [70, 44])

    set_input = Simulation.set_input
    reset = simulation_module.reset_growthfactor_uprating
    replayed_spans, price_observations = [], []

    def observe_input(target, name, requested, values, *args, **kwargs):
        if name == "local_authority" and str(core_period(requested)) == "year:2024:2":
            replayed_spans.append(np.array(values, copy=True))
        return set_input(target, name, requested, values, *args, **kwargs)

    def observe_reset(dataset):
        price_observations.append(
            [dataset[year].energy_price_basis for year in dataset.years]
        )
        assert all(
            dataset[year].energy_price_basis == expected_basis for year in dataset.years
        )
        return reset(dataset)

    with monkeypatch.context() as patch:
        patch.setattr(
            UKSingleYearDataset, "from_simulation", staticmethod(no_eager_snapshot)
        )
        patch.setattr(Simulation, "set_input", observe_input)
        patch.setattr(simulation_module, "reset_growthfactor_uprating", observe_reset)
        # Loading a modified annual view still uses the canonical input source.
        restored_once = Simulation(
            dataset=public_copy, scenario=no_economic_assumptions
        )
        restored_twice = Simulation(
            dataset=restored_once.dataset.copy(), scenario=no_economic_assumptions
        )
    assert price_observations
    if entry == "core_dataset":
        assert len(replayed_spans) >= 2
        for values in replayed_spans:
            np.testing.assert_array_equal(values, ["CITY_OF_EDINBURGH", "CARDIFF"])
        for name, entries in original_core_arrays.items():
            for requested, values in entries.items():
                np.testing.assert_array_equal(
                    original_core.arrays[name][requested], values
                )
        assert original_core.energy_price_basis == expected_basis

    for target in [original, restored_once, restored_twice]:
        assert tuple(target.dataset.years) == (2024, 2025)
        assert state_pension_data_year(target.persons, core_period(2025)) == 2024
        # The reported 2025 amount is deliberately zero: a query-year fallback
        # would pay zero. The 2024 share uprates at the statutory 2025/2024 ratio.
        np.testing.assert_allclose(
            target.calculate("basic_state_pension", 2025),
            [5_200 * 176.45 / 169.50, 0],
            atol=0.01,
        )
        for year in [2023, 2024]:
            for name, values in identifiers.items():
                np.testing.assert_array_equal(target.calculate(name, year), values)
        np.testing.assert_array_equal(target.calculate("age", 2024), [70, 44])
        np.testing.assert_array_equal(target.calculate("rent", 2024), [12_345, 6_789])
        assert labels(target, "region", 2025) == ["LONDON", "WALES"]
        assert labels(target, "local_authority", 2024) == [
            "CITY_OF_EDINBURGH",
            "CARDIFF",
        ]
        for year in target.dataset.years:
            assert target.dataset[year].energy_price_basis == expected_basis
        assert target.dataset.savings_income_projection == (
            "obr_savings_income_2022_2025"
            if entry == "core_dataset"
            else "gdp_per_head"
        )
        with pytest.raises(ValueError, match="(?i)council|local_authority"):
            target.calculate("local_authority", 2025)
        with pytest.raises(ValueError, match="(?i)council|local_authority"):
            UKSingleYearDataset.from_simulation(target, fiscal_year=2025)
    pd.testing.assert_frame_equal(restored_once.to_input_dataframe(), before)
    pd.testing.assert_frame_equal(restored_twice.to_input_dataframe(), before)
    # Unsupported annual persistence must not unlink an existing target or
    # create a new one before rejecting the lossy operation.
    existing = tmp_path / "existing.h5"
    existing.write_bytes(b"keep existing bytes")
    absent = tmp_path / "absent.h5"
    for destination in [existing, absent]:
        with pytest.raises(NotImplementedError, match="Input-backed|input-backed"):
            restored_twice.dataset.save(destination)
    assert existing.read_bytes() == b"keep existing bytes"
    assert not absent.exists()


@pytest.mark.parametrize(
    "field, child, older_other",
    [
        ("region", False, False),
        ("region", False, True),
        ("local_authority", False, True),
        ("region", True, False),
        ("local_authority", True, True),
    ],
)
def test_newer_opaque_geography_does_not_revive_older_or_parent_facts(
    monkeypatch, field, child, older_other
):
    from policyengine_core.enums import EnumArray

    if field == "region":
        first = {
            "region": {2023: "LONDON", 2025: "SCOTLAND"},
            "country": {2025: "SCOTLAND"},
        }
        if older_other:
            first["local_authority"] = {2024: "CITY_OF_EDINBURGH"}
        expected = ["SCOTLAND", "WALES"]
    else:
        first = {
            "local_authority": {2023: "MAIDSTONE", 2025: "CITY_OF_EDINBURGH"},
            "country": {2025: "SCOTLAND"},
        }
        if older_other:
            first["region"] = {2024: "LONDON"}
        expected = ["CITY_OF_EDINBURGH", "CARDIFF"]
    second = {
        "region": {2025: "WALES"},
        "local_authority": {2025: "CARDIFF"},
        "country": {2025: "WALES"},
    }
    if child:
        # A native same-period parent fact must not leak through an opaque
        # child tier; the child's actual supplied value is deliberately newer
        # in branch precedence rather than in calendar time.
        parent_first = {
            **first,
            field: {2025: "LONDON" if field == "region" else "MAIDSTONE"},
            "country": {2025: "ENGLAND"},
        }
        if field == "local_authority":
            parent_first["region"] = {2024: "LONDON"}
        parent = Simulation(situation=situation([parent_first, second]))
        simulation = parent.get_branch("opaque_child", clone_system=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            simulation.set_input(field, 2025, expected)
            simulation.set_input("country", 2025, ["SCOTLAND", "WALES"])
    else:
        simulation = Simulation(situation=situation([first, second]))
    holder = simulation.get_holder(field)
    stored = get_stored_input(holder, core_period(2025), simulation.branch_name)

    class CustomView(EnumArray):
        pass

    holder._set(
        core_period(2025),
        stored.view(CustomView),
        branch_name=simulation.branch_name,
        is_input=True,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        assert labels(simulation, "country", 2025) == ["SCOTLAND", "WALES"]
        assert labels(simulation, field, 2025) == expected
        if older_other and field == "region":
            assert labels(simulation, "local_authority", 2025) == [
                "CITY_OF_EDINBURGH",
                "CARDIFF",
            ]


def test_opaque_region_still_rejects_an_adjacent_proven_council_country_conflict():
    from policyengine_core.enums import EnumArray

    simulation = Simulation(
        situation=situation(
            [
                {
                    "region": {2024: "LONDON", 2025: "SCOTLAND"},
                    "country": {2025: "SCOTLAND"},
                },
                {
                    "region": {2025: "WALES"},
                    "local_authority": {2025: "CARDIFF"},
                    "country": {2025: "WALES"},
                },
            ]
        )
    )
    holder = simulation.get_holder("region")
    stored = get_stored_input(holder, core_period(2025), simulation.branch_name)

    class CustomView(EnumArray):
        pass

    holder._set(
        core_period(2025),
        stored.view(CustomView),
        branch_name=simulation.branch_name,
        is_input=True,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.set_input("country", 2025, ["SCOTLAND", "ENGLAND"])
    with pytest.raises(ValueError, match="(?i)contradict|nation"):
        simulation.calculate("country", 2025)


def test_ordinary_stale_situation_source_preserves_real_structure_and_absent_numeric_ids_across_two_reloads(
    monkeypatch,
):
    from copy import deepcopy
    from policyengine_uk.utils.entity_ids import ENTITY_ID_VARIABLES

    data = situation(
        [
            {
                "local_authority": {2024: "CITY_OF_EDINBURGH"},
                "region": {2026: "LONDON"},
            },
            {"region": {2024: "WALES"}},
        ],
        sizes=[2, 1],
    )
    before_data = deepcopy(data)

    def no_eager_snapshot(*args, **kwargs):
        pytest.fail("An ordinary stale situation must not evaluate an annual snapshot.")

    with monkeypatch.context() as patch:
        patch.setattr(
            UKSingleYearDataset, "from_simulation", staticmethod(no_eager_snapshot)
        )
        original = Simulation(situation=data)
        before = original.to_input_dataframe()
        restored_once = Simulation(dataset=original.dataset.copy())
        restored_twice = Simulation(dataset=restored_once.dataset.copy())
    assert data == before_data
    for target in [original, restored_once, restored_twice]:
        assert tuple(target.dataset.years) == (2024, 2026)
        for entity in ["person", "benunit", "household"]:
            np.testing.assert_array_equal(
                target.populations[entity].ids, original.populations[entity].ids
            )
            if entity != "person":
                np.testing.assert_array_equal(
                    target.populations[entity].members_entity_id,
                    original.populations[entity].members_entity_id,
                )
        assert all(
            not target.get_holder(name).get_input_periods(target.branch_name)
            for name in ENTITY_ID_VARIABLES
        )
        assert not any(
            str(column).startswith(tuple(name + "__" for name in ENTITY_ID_VARIABLES))
            for column in target.to_input_dataframe()
        )
        pd.testing.assert_frame_equal(target.to_input_dataframe(), before)
        assert labels(target, "local_authority", 2024) == [
            "CITY_OF_EDINBURGH",
            "MAIDSTONE",
        ]
        assert labels(target, "region", 2026) == ["LONDON", "WALES"]
        assert labels(target, "country", 2026) == ["ENGLAND", "WALES"]
        with pytest.raises(ValueError, match="(?i)council|local_authority"):
            target.calculate("local_authority", 2026)


def test_partial_person_id_situation_source_keeps_shared_builder_groups_across_copy_and_two_reloads(
    monkeypatch,
):
    from policyengine_uk.utils.entity_ids import ENTITY_ID_VARIABLES

    data = situation(
        [
            {
                "local_authority": {2024: "CITY_OF_EDINBURGH"},
                "region": {2026: "LONDON"},
            },
            {"region": {2024: "WALES"}},
        ],
        sizes=[2, 1],
    )
    person_ids = [70, 10, 90]
    for person, identifier in zip(data["people"].values(), person_ids):
        person["person_id"] = {2024: identifier}
    before_data = deepcopy(data)
    absent_ids = set(ENTITY_ID_VARIABLES) - {"person_id"}

    def no_eager_snapshot(*args, **kwargs):
        pytest.fail("A partial-ID situation must not evaluate an annual snapshot.")

    with monkeypatch.context() as patch:
        patch.setattr(
            UKSingleYearDataset, "from_simulation", staticmethod(no_eager_snapshot)
        )
        original = Simulation(situation=data)
        before = original.to_input_dataframe()
        source_copy = original.dataset.copy()
        restored_once = Simulation(dataset=source_copy)
        restored_twice = Simulation(dataset=restored_once.dataset.copy())
    assert data == before_data
    for target in [original, restored_once, restored_twice]:
        assert tuple(target.dataset.years) == (2024, 2026)
        np.testing.assert_array_equal(
            target.populations["person"].ids, ["person0_0", "person0_1", "person1_0"]
        )
        np.testing.assert_array_equal(target.calculate("person_id", 2024), person_ids)
        for entity in ["benunit", "household"]:
            population = target.populations[entity]
            np.testing.assert_array_equal(population.ids, [f"{entity}0", f"{entity}1"])
            np.testing.assert_array_equal(population.members_entity_id, [0, 0, 1])
            np.testing.assert_array_equal(population.nb_persons(), [2, 1])
            assert [role.key for role in population.members_role] == ["member"] * 3
        assert all(
            not target.get_holder(name).get_input_periods(target.branch_name)
            for name in absent_ids
        )
        frame = target.to_input_dataframe()
        assert not any(
            str(column).startswith(tuple(name + "__" for name in absent_ids))
            for column in frame
        )
        pd.testing.assert_frame_equal(frame, before)
        assert labels(target, "local_authority", 2024) == [
            "CITY_OF_EDINBURGH",
            "MAIDSTONE",
        ]
        assert labels(target, "region", 2026) == ["LONDON", "WALES"]
        assert labels(target, "country", 2026) == ["ENGLAND", "WALES"]
        with pytest.raises(ValueError, match="(?i)council|local_authority"):
            target.calculate("local_authority", 2026)

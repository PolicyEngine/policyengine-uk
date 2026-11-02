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
from policyengine_core.periods import period as core_period
from policyengine_core.holders.helpers import get_stored_input
from policyengine_core.reforms import Reform
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.scenarios import no_economic_assumptions
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
        {"local_authority": {YEAR: "CITY_OF_EDINBURGH"}, "country": {YEAR: "ENGLAND"}},
        {"region": {YEAR: "WALES"}, "country": {YEAR: "SCOTLAND"}},
        {"local_authority": {YEAR: "MAIDSTONE"}, "region": {YEAR: "LONDON"}},
    ],
)
def test_conflicting_genuinely_supplied_geography_is_rejected(inputs, query):
    with pytest.raises(ValueError):
        simulation = Simulation(situation=situation([inputs]))
        simulation.calculate(query, YEAR)


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


def test_failed_geography_input_change_does_not_mutate_the_simulation():
    simulation = Simulation(situation=situation([{"country": {YEAR: "WALES"}}]))
    assert labels(simulation, "region") == ["WALES"]
    with pytest.raises(ValueError):
        simulation.set_input("region", YEAR, ["LONDON"])
    assert labels(simulation, "region") == ["WALES"]
    assert labels(simulation, "country") == ["WALES"]
    simulation.set_input("local_authority", YEAR, ["CARDIFF"])
    with pytest.raises(ValueError):
        simulation.set_input("country", YEAR, ["SCOTLAND"])
    assert labels(simulation, "country") == ["WALES"]
    assert labels(simulation, "region") == ["WALES"]


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

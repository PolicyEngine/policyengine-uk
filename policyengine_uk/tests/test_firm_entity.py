"""The firm entity: a root population of its own, beside people, benefit
units and households.

A simulation built from a household situation or dataset has no firms, and
its household results are those of a simulation without the entity. A
situation's ``firms`` entry, or a dataset's firm table, gives it firms, and
reforms, branches and clones keep them.
"""

import numpy as np
import pandas as pd
import pytest
from policyengine_core.reforms import Reform
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.model_api import YEAR as YEAR_PERIOD, Firm, Variable

YEAR = 2025
HOUSEHOLD = {
    "people": {
        "adult": {"age": {YEAR: 40}, "employment_income": {YEAR: 45_000}},
        "child": {"age": {YEAR: 5}},
    },
    "benunits": {"benunit": {"members": ["adult", "child"]}},
    "households": {"household": {"members": ["adult", "child"]}},
}
FIRMS = {
    "acme": {
        "firm_paybill": {YEAR: 1_000_000},
        "firm_input_costs": {YEAR: 250_000},
        "firm_is_bank": {YEAR: True},
    },
    "corner_shop": {
        "firm_paybill": 40_000,
        "firm_legal_form": "SOLE_TRADER",
    },
}
HOUSEHOLD_OUTPUTS = [
    "income_tax",
    "national_insurance",
    "child_benefit",
    "household_tax",
    "household_benefits",
    "household_net_income",
]


class firm_test_costs(Variable):
    """A firm aggregate (``adds``) that only the test reform adds."""

    value_type = float
    entity = Firm
    label = "Firm paybill and input costs (test only)"
    definition_period = YEAR_PERIOD
    adds = ["firm_paybill", "firm_input_costs"]


class add_firm_test_costs(Reform):
    def apply(self):
        self.add_variable(firm_test_costs)


@pytest.fixture(scope="module")
def with_firms():
    return Simulation(situation={**HOUSEHOLD, "firms": FIRMS})


def test_a_household_situation_has_no_firms():
    simulation = Simulation(situation=HOUSEHOLD)
    assert simulation.populations["firm"].count == 0
    assert simulation.firm is simulation.populations["firm"]
    assert len(simulation.calculate("firm_paybill", YEAR)) == 0


def test_firms_leave_household_results_unchanged(with_firms):
    without = Simulation(situation=HOUSEHOLD)
    for variable in HOUSEHOLD_OUTPUTS:
        assert np.array_equal(
            without.calculate(variable, YEAR), with_firms.calculate(variable, YEAR)
        ), variable


def test_a_situation_gives_firms_their_inputs(with_firms):
    firm = with_firms.populations["firm"]
    assert firm.count == 2
    assert list(firm.ids) == ["acme", "corner_shop"]
    assert with_firms.calculate("firm_paybill", YEAR).tolist() == [
        1_000_000,
        40_000,
    ]
    assert with_firms.calculate("firm_is_bank", YEAR).tolist() == [True, False]
    assert with_firms.calculate("firm_legal_form", YEAR).tolist() == [
        "COMPANY",
        "SOLE_TRADER",
    ]
    assert with_firms.calculate("firm_weight", YEAR).tolist() == [1, 1]
    assert "firm_paybill" in with_firms.input_variables


def test_the_callers_situation_is_not_changed():
    situation = {**HOUSEHOLD, "firms": FIRMS}
    Simulation(situation=situation)
    assert situation["firms"] is FIRMS


def test_a_situation_of_firms_alone_has_no_people():
    simulation = Simulation(situation={"firms": FIRMS})
    assert simulation.populations["person"].count == 0
    assert simulation.populations["household"].count == 0
    assert simulation.calculate("firm_paybill", YEAR).tolist() == [1_000_000, 40_000]


def test_a_reform_simulation_and_its_baseline_keep_firms():
    simulation = Simulation(
        situation={**HOUSEHOLD, "firms": FIRMS},
        reform={"gov.hmrc.income_tax.rates.uk[0].rate": {"2025": 0.25}},
    )
    for each in (simulation, simulation.baseline):
        assert each.populations["firm"].count == 2
        assert each.calculate("firm_paybill", YEAR).tolist() == [1_000_000, 40_000]
    assert (
        simulation.calculate("income_tax", YEAR).sum()
        > simulation.baseline.calculate("income_tax", YEAR).sum()
    )


def test_a_structural_reform_keeps_firms_and_adds_a_firm_aggregate():
    simulation = Simulation(situation={**HOUSEHOLD, "firms": FIRMS})
    simulation.apply_reform(add_firm_test_costs)
    assert simulation.populations["firm"].count == 2
    assert simulation.firm.entity is next(
        entity
        for entity in simulation.tax_benefit_system.entities
        if entity.key == "firm"
    )
    assert simulation.calculate("firm_test_costs", YEAR).tolist() == [
        1_250_000,
        40_000,
    ]
    branch = simulation.get_branch("firm_branch")
    assert branch.calculate("firm_test_costs", YEAR).tolist() == [1_250_000, 40_000]
    clone = simulation.clone()
    assert clone.calculate("firm_test_costs", YEAR).tolist() == [1_250_000, 40_000]


def test_a_branch_keeps_firms_and_its_inputs_stay_its_own(with_firms):
    branch = with_firms.get_branch("firm_inputs")
    assert branch.firm is branch.populations["firm"]
    assert branch.firm is not with_firms.firm
    branch.set_input("firm_paybill", YEAR, np.array([0.0, 0.0]))
    assert branch.calculate("firm_paybill", YEAR).tolist() == [0, 0]
    assert with_firms.calculate("firm_paybill", YEAR).tolist() == [
        1_000_000,
        40_000,
    ]


def test_a_clone_has_its_own_firms():
    simulation = Simulation(situation={**HOUSEHOLD, "firms": FIRMS})
    clone = simulation.clone()
    assert clone.firm is clone.populations["firm"]
    assert clone.firm is not simulation.firm
    assert clone.firm.simulation is clone
    clone.set_input("firm_paybill", YEAR, np.array([1.0, 2.0]))
    assert clone.calculate("firm_paybill", YEAR).tolist() == [1, 2]
    assert simulation.calculate("firm_paybill", YEAR).tolist() == [
        1_000_000,
        40_000,
    ]


def test_firm_values_do_not_map_to_people(with_firms):
    with pytest.raises(ValueError, match="firms have no members"):
        with_firms.calculate("firm_paybill", YEAR, map_to="person")


def test_input_export_leaves_firms_out(with_firms):
    frame = with_firms.to_input_dataframe()
    assert not any(str(column).startswith("firm_") for column in frame.columns)
    assert len(frame) == 2


def tables(firm: pd.DataFrame = None) -> UKSingleYearDataset:
    """Two single-person households, and optionally firms."""
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [30, 50],
                "employment_income": [20_000.0, 60_000.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        # With the columns that extending a dataset to later years reads.
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "household_weight": [100.0, 200.0],
                "region": "LONDON",
                "rent": 0.0,
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": 0.0,
            }
        ),
        firm=firm,
        fiscal_year=YEAR,
    )


FIRM_TABLE = pd.DataFrame(
    {
        # Not in identifier order: firms keep the order the table gives.
        "firm_id": [30, 10, 20],
        "firm_weight": [5.0, 7.0, 11.0],
        "firm_paybill": [3e6, 1e5, 2e5],
        "firm_legal_form": ["PARTNERSHIP", "COMPANY", "SOLE_TRADER"],
    }
)


def test_a_dataset_without_a_firm_table_loads_with_no_firms():
    simulation = Microsimulation(dataset=tables())
    assert simulation.populations["firm"].count == 0
    assert simulation.calculate("employment_income", YEAR).sum() == (
        100 * 20_000 + 200 * 60_000
    )


def test_a_dataset_firm_table_loads_in_its_own_order():
    simulation = Microsimulation(dataset=tables(FIRM_TABLE.copy()))
    assert simulation.populations["firm"].count == 3
    assert simulation.calculate("firm_id", YEAR).tolist() == [30, 10, 20]
    paybill = simulation.calculate("firm_paybill", YEAR)
    # Weighted by firm_weight, never by a household or person weight.
    assert paybill.weights.tolist() == [5, 7, 11]
    assert paybill.sum() == 5 * 3e6 + 7 * 1e5 + 11 * 2e5
    assert simulation.calculate("firm_legal_form", YEAR).tolist() == [
        "PARTNERSHIP",
        "COMPANY",
        "SOLE_TRADER",
    ]
    # Later years carry the firms forward.
    assert simulation.calculate("firm_paybill", YEAR + 1).tolist() == [
        3e6,
        1e5,
        2e5,
    ]


def test_a_firm_table_survives_saving(tmp_path):
    path = str(tmp_path / "with_firms.h5")
    tables(FIRM_TABLE.copy()).save(path)
    loaded = UKSingleYearDataset(file_path=path)
    pd.testing.assert_frame_equal(
        loaded.firm.reset_index(drop=True), FIRM_TABLE, check_dtype=False
    )
    without = str(tmp_path / "without_firms.h5")
    tables().save(without)
    assert UKSingleYearDataset(file_path=without).firm is None


def test_a_dataset_keeps_three_household_tables():
    dataset = tables(FIRM_TABLE.copy())
    assert dataset.table_names == ("person", "benunit", "household")
    assert len(dataset.tables) == 3
    assert dataset.copy().firm.equals(dataset.firm)


def test_a_simulation_with_firms_is_not_subsampled():
    simulation = Microsimulation(dataset=tables(FIRM_TABLE.copy()))
    with pytest.raises(NotImplementedError, match="firms"):
        simulation.subsample(n=1)


def test_yaml_variable_inputs_give_one_firm_per_value():
    """The YAML test runner builds with core's builder: variable-only input
    gives every population, the firm's included, one record per value."""
    system = CountryTaxBenefitSystem()
    builder = SimulationBuilder()
    builder.set_default_period(YEAR)
    simulation = builder.build_from_dict(system, {"firm_paybill": [1.0, 2.0, 3.0]})
    assert simulation.populations["firm"].count == 3
    assert simulation.calculate("firm_paybill", YEAR).tolist() == [1, 2, 3]


def test_yaml_firms_block_is_ignored():
    """Core's builder ignores a ``firms:`` block (it knows only people and
    their groups), so YAML firm tests must give firm variables directly."""
    system = CountryTaxBenefitSystem()
    builder = SimulationBuilder()
    builder.set_default_period(YEAR)
    simulation = builder.build_from_dict(
        system,
        {
            "people": {"adult": {"age": 40}},
            "firms": {"acme": {"firm_paybill": 1.0}},
        },
    )
    assert simulation.populations["firm"].count == 0


def test_a_firm_cannot_read_household_values_through_a_shortcut(with_firms):
    """Core treats a non-group population as people, so ``firm.household``
    would project household values onto people. Firms refuse it, in
    branches and clones too."""
    for simulation in (with_firms, with_firms.clone(), with_firms.get_branch("x")):
        with pytest.raises(AttributeError, match="no members"):
            simulation.populations["firm"].household


def test_a_multi_year_dataset_keeps_its_firm_tables(tmp_path):
    path = str(tmp_path / "multi_year.h5")
    single = tables(FIRM_TABLE.copy())
    later = tables(FIRM_TABLE.iloc[[2, 0, 1]].copy())
    later.time_period = str(YEAR + 1)
    UKMultiYearDataset(datasets=[single, later]).save(path)
    loaded = UKMultiYearDataset(file_path=path)
    assert loaded[YEAR + 1].firm["firm_id"].tolist() == [20, 30, 10]
    simulation = Microsimulation(dataset=loaded)
    # Each year's rows follow the first year's order of firms.
    assert simulation.calculate("firm_weight", YEAR + 1).tolist() == [5, 7, 11]
    without = str(tmp_path / "multi_year_without_firms.h5")
    UKMultiYearDataset(datasets=[tables()]).save(without)
    assert UKMultiYearDataset(file_path=without)[YEAR].firm is None


def test_every_export_leaves_firms_out(with_firms):
    frame = with_firms.to_input_dataframe(include_computed_variables=True)
    assert not any(str(column).startswith("firm_") for column in frame.columns)
    exported = with_firms.to_input_dict()
    assert not any(name.startswith("firm_") for name in exported)
    assert "age" in exported


def test_a_variable_only_situation_cannot_give_firm_inputs():
    with pytest.raises(ValueError, match="'firms' entry"):
        Simulation(situation={"firm_paybill": [1.0, 2.0]})

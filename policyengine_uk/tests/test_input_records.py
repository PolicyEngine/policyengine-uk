"""A simulation exports as inputs only the values supplied to it.

policyengine-core records each (variable, branch, period) that ``set_input``
stores, and ``to_input_dict`` exports the recorded values. Rebuilding the
populations keeps the record of inputs the rebuild drops
(policyengine-core#605). ``Simulation.delete_arrays`` forgets such a record,
so a value the engine later carries into that period is not exported as an
input.
"""

import numpy as np
import pandas as pd
import pytest
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.utils.supplied_inputs import (
    is_model_value,
    set_model_value,
    stored_supplied_value,
    supplied_input,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def situation(hours):
    return {
        "people": {"person": {"age": {2025: 40}, "hours_worked": hours}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def test_deleting_after_a_rebuild_does_not_export_a_carried_over_input():
    sim = Simulation(situation=situation({2025: 1_000, 2026: 500}))
    sim.build_from_situation(situation({2025: 1_000}))
    sim.delete_arrays("hours_worked", 2026)
    # The engine carries 2025's hours into 2026; they are not an input.
    assert sim.calculate("hours_worked", 2026).tolist() == [1_000]
    assert sim.to_input_dict()["hours_worked"] == {"2025": [1_000]}


@pytest.mark.parametrize("model", [False, True], ids=["supplied", "model"])
@pytest.mark.parametrize(
    "subsampled",
    [
        pytest.param(False, id="direct"),
        pytest.param(
            True,
            id="subsampled",
            marks=pytest.mark.xfail(
                strict=True,
                raises=AssertionError,
                reason="needs policyengine-core holder resync",
            ),
        ),
    ],
)
def test_restoring_reform_can_replace_a_neutralized_input(model, subsampled):
    """A write after restoration replaces the hidden value and its ownership."""
    if subsampled:
        dataset = UKSingleYearDataset(
            person=pd.DataFrame(
                {
                    "person_id": [1],
                    "person_benunit_id": [1],
                    "person_household_id": [1],
                    "age": [40],
                    "employment_income": [30_000.0],
                }
            ),
            benunit=pd.DataFrame({"benunit_id": [1]}),
            household=pd.DataFrame(
                {
                    "household_id": [1],
                    "household_weight": [1.0],
                    "region": ["LONDON"],
                    "tenure_type": ["OWNED_OUTRIGHT"],
                    "rent": [0.0],
                    "council_tax": [0.0],
                }
            ),
            fiscal_year=2025,
        )
        simulation = Microsimulation(dataset=dataset)
    else:
        simulation = Simulation(situation={"age": 40, "employment_income": 30_000})
    name = "adjusted_net_income"
    period = period_(2025)
    original_variable = simulation.tax_benefit_system.get_variable(name).__class__
    if model:
        set_model_value(simulation, name, period, [10_000])
    else:
        simulation.set_input(name, period, [10_000])

    class NeutralizeIncome(Reform):
        def apply(self):
            self.neutralize_variable(name)

    class RestoreAndReplaceIncome(Reform):
        def apply(self):
            self.replace_variable(original_variable)
            assert not self.get_variable(name).is_neutralized
            assert self.get_variable(name).__class__ is original_variable
            self.simulation.set_input(name, period, [20_000])
            stored = stored_supplied_value(
                self.simulation.get_holder(name), period, self.simulation.branch_name
            )
            np.testing.assert_array_equal(stored, [20_000])
            np.testing.assert_array_equal(
                self.simulation.calculate(name, period), [20_000]
            )
            assert not is_model_value(self.simulation, name, period, stored)
            np.testing.assert_array_equal(
                supplied_input(self.simulation.populations["person"], name, period),
                [20_000],
            )

    simulation.apply_reform(NeutralizeIncome)
    if subsampled:
        simulation.subsample(n=1, seed=0, time_period=2025)
    simulation.apply_reform(RestoreAndReplaceIncome)

    stored = stored_supplied_value(
        simulation.get_holder(name), period, simulation.branch_name
    )
    np.testing.assert_array_equal(stored, [20_000])
    np.testing.assert_array_equal(simulation.calculate(name, period), [20_000])
    assert not is_model_value(simulation, name, period, stored)
    np.testing.assert_array_equal(
        supplied_input(simulation.populations["person"], name, period), [20_000]
    )

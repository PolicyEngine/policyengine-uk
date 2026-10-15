"""A measurement branch measures from inputs alone.

A branch starts from every value its simulation holds. A measurement branch
drops what the simulation calculated, so a result the simulation calculated
with a behavioural response is recalculated without it, at the branch's
inputs, rather than read from the simulation.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.utils.measurement_branches import measurement_branch

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
ELASTICITIES = {
    "gov.simulation.labour_supply_responses.substitution_elasticity": {str(YEAR): 0.25},
    "gov.simulation.labour_supply_responses.income_elasticity": {str(YEAR): -0.05},
}
BASIC_RATE_RISE = {"gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}}
STATIC_CAPITAL_GAINS = {
    "gov.simulation.capital_gains_responses.elasticity": {str(YEAR): 0},
    "gov.simulation.capital_gains_responses.mtr_elasticity": {str(YEAR): 0},
}
SITUATION = {
    "people": {"person": {"age": {YEAR: 45}, "employment_income": {YEAR: 40_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def value(simulation, variable):
    return float(np.asarray(simulation.calculate(variable, YEAR), dtype=float)[0])


def test_a_measurement_branch_drops_what_its_simulation_calculated():
    reform = {**BASIC_RATE_RISE, **STATIC_CAPITAL_GAINS}
    responding = Simulation(
        situation=SITUATION,
        scenario=Scenario(parameter_changes={**reform, **ELASTICITIES}),
    )
    assert value(responding, "employment_income_behavioral_response") < 0
    with_response = value(responding, "household_net_income")

    branch = measurement_branch(responding, "probe", YEAR, {})

    without_response = Simulation(
        situation=SITUATION, scenario=Scenario(parameter_changes=reform)
    )
    measured = value(branch, "household_net_income")
    assert measured == value(without_response, "household_net_income")
    assert measured != with_response
    # The branch is not kept, and the simulation's own results are untouched.
    assert "probe" not in responding.branches
    assert value(responding, "household_net_income") == with_response

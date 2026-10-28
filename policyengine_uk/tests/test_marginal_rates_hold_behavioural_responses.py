"""Marginal rates hold the behavioural responses at the simulation's values.

marginal_tax_rate, marginal_tax_rate_wrt_employer_cost and
marginal_tax_rate_on_capital_gains step an input in a branch of the
simulation, which shares its tax-benefit system, and recalculate every
variable with a formula there. A response recalculated in that branch was
measured again: at the stepped input, against a baseline without the step,
and with the step itself undone inside the measurement's own marginal rate
branches, which recalculate the stepped variable from its formula. The rate is
the change in net income at fixed behaviour, so it must equal the rate of a
simulation without the response whose inputs sit where the response put them.

For the labour supply response, two things now keep these branches from
measuring it again: the hold, and response_source, which gives a branch that
shares its parent's rules the parent's response. So the labour supply cases
fail only with both removed, and the capital gains cases isolate the hold in
these variables. test_measurement_branches.py isolates the hold for every
response with a branch that has its own copy of the rules.

Every simulation here sets the capital gains response explicitly, so the
tests hold whatever its default is.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
LABOUR_SUPPLY_RESPONSE = "employment_income_behavioral_response"
CAPITAL_GAINS_RESPONSE = "capital_gains_behavioural_response"
ELASTICITIES = {
    "gov.simulation.labour_supply_responses.substitution_elasticity": {str(YEAR): 0.25},
    "gov.simulation.labour_supply_responses.income_elasticity": {str(YEAR): -0.05},
}
BASIC_RATE_RISE = {"gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}}
# Employers bear half of employer NI, and pass it on to prices: the price
# incidence reads baseline_employer_cost, which reads the labour supply
# response directly.
EMPLOYER_NI_INCIDENCE = {
    "gov.contrib.policyengine.employer_ni.employee_incidence": {str(YEAR): 0.5}
}
CAPITAL_GAINS_REFORM = {
    "gov.hmrc.cgt.basic_rate": {str(YEAR): 0.20},
    "gov.hmrc.cgt.higher_rate": {str(YEAR): 0.40},
    "gov.hmrc.cgt.additional_rate": {str(YEAR): 0.45},
}
CAPITAL_GAINS_RESPONSES = "gov.simulation.capital_gains_responses"
STATIC_CAPITAL_GAINS = {
    f"{CAPITAL_GAINS_RESPONSES}.elasticity": {str(YEAR): 0},
    f"{CAPITAL_GAINS_RESPONSES}.mtr_elasticity": {str(YEAR): 0},
}
CAPITAL_GAINS_ELASTICITY = {
    f"{CAPITAL_GAINS_RESPONSES}.elasticity": {str(YEAR): 1.0},
    f"{CAPITAL_GAINS_RESPONSES}.mtr_elasticity": {str(YEAR): 0},
}


def situation(earnings, gains=0.0, food=0.0):
    person = {"age": {YEAR: 45}, "employment_income": {YEAR: earnings}}
    if gains:
        person["capital_gains"] = {YEAR: gains}
    household = {"members": ["person"]}
    if food:
        household["food_and_non_alcoholic_beverages_consumption"] = {YEAR: food}
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": household},
    }


def value(simulation, variable):
    return float(np.asarray(simulation.calculate(variable, YEAR), dtype=float)[0])


@pytest.mark.parametrize(
    "variable, gains, food, changes",
    [
        # Gains of £22,000 on £40,000 of earnings straddle the basic rate
        # limit. Measured again at £1,000 more gains, the response reached the
        # wage change bound (-£9,921 against -£1,406), and the capital gains
        # rate came out at 502% instead of 24%.
        ("marginal_tax_rate_on_capital_gains", 22_000, 0, {}),
        # With employer NI price incidence on, the pay rise branches measured
        # the response again at the reform's earnings after the response plus
        # the step: 94.2% instead of 95.5%, and 94.9% instead of 96.1%.
        ("marginal_tax_rate", 0, 10_000, EMPLOYER_NI_INCIDENCE),
        ("marginal_tax_rate_wrt_employer_cost", 0, 10_000, EMPLOYER_NI_INCIDENCE),
    ],
)
def test_marginal_rates_hold_the_labour_supply_response(variable, gains, food, changes):
    reform = {**BASIC_RATE_RISE, **STATIC_CAPITAL_GAINS, **changes}
    responding = Simulation(
        situation=situation(40_000, gains, food),
        scenario=Scenario(parameter_changes={**reform, **ELASTICITIES}),
    )
    response = value(responding, LABOUR_SUPPLY_RESPONSE)
    held = Simulation(
        situation=situation(40_000 + response, gains, food),
        scenario=Scenario(parameter_changes=reform),
    )

    assert response < 0
    assert value(responding, variable) == pytest.approx(value(held, variable), abs=1e-4)


@pytest.mark.parametrize("gains", [13_000, 22_000])
def test_marginal_tax_rate_holds_the_capital_gains_response(gains):
    """A pay rise moves gains near the basic rate limit into the higher rate.

    The pay rise branch measured the realisation response again at the higher
    earnings, and the capital gains marginal rate inside that measurement
    recalculated earnings without the pay rise: the marginal tax rate came out
    at 830% (gains of £13,000) and 1,164% (£22,000), against 28% and 48%.
    """
    responding = Simulation(
        situation=situation(40_000, gains),
        scenario=Scenario(
            parameter_changes={**CAPITAL_GAINS_REFORM, **CAPITAL_GAINS_ELASTICITY}
        ),
    )
    response = value(responding, CAPITAL_GAINS_RESPONSE)
    held = Simulation(
        situation=situation(40_000, gains + response),
        scenario=Scenario(
            parameter_changes={**CAPITAL_GAINS_REFORM, **STATIC_CAPITAL_GAINS}
        ),
    )

    assert response < 0
    assert value(responding, "marginal_tax_rate") == pytest.approx(
        value(held, "marginal_tax_rate"), abs=1e-4
    )

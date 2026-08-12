"""Tests for the capital gains realisation response to CGT rate changes."""

import pytest

from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario

YEAR = 2026

SITUATION = {
    "people": {
        "person": {
            "age": {YEAR: 45},
            "employment_income": {YEAR: 100_000},
            "capital_gains": {YEAR: 200_000},
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

EQUALISED_RATES = {
    "gov.hmrc.cgt.basic_rate": {str(YEAR): 0.20},
    "gov.hmrc.cgt.higher_rate": {str(YEAR): 0.40},
    "gov.hmrc.cgt.additional_rate": {str(YEAR): 0.45},
}


def simulate(elasticity: float | None = None, rates: bool = True) -> Microsimulation:
    changes = dict(EQUALISED_RATES) if rates else {}
    if elasticity is not None:
        changes["gov.simulation.capital_gains_responses.elasticity"] = {
            str(YEAR): elasticity
        }
    if not changes:
        return Microsimulation(situation=SITUATION)
    return Microsimulation(
        situation=SITUATION, scenario=Scenario(parameter_changes=changes)
    )


def test_rate_rise_registers_against_the_baseline():
    """A CGT rate rise registers as a higher rate and a lower retention rate.

    Regression test for measuring the baseline against a branch of the reform
    simulation, which reported no rate change for any reform (issue #1319).
    """
    sim = simulate(elasticity=1.0)
    mtr_change = sim.calculate("relative_capital_gains_mtr_change", YEAR).values[0]
    retention_change = sim.calculate(
        "relative_capital_gains_retention_rate_change", YEAR
    ).values[0]

    assert mtr_change > 0, f"expected a positive log rate change, got {mtr_change}"
    assert retention_change < 0, (
        f"expected a negative log retention change, got {retention_change}"
    )


def test_realisations_fall_when_rates_rise():
    """Gains fall under a rate rise, by more at a larger elasticity."""
    baseline_gains = simulate(rates=False).calculate("capital_gains", YEAR).sum()

    modest = simulate(elasticity=0.5).calculate("capital_gains", YEAR).sum()
    large = simulate(elasticity=1.0).calculate("capital_gains", YEAR).sum()

    assert modest < baseline_gains
    assert large < modest


def test_revenue_falls_short_of_the_static_estimate():
    """The behavioural response costs revenue relative to a static costing."""
    static = simulate(elasticity=0).calculate("capital_gains_tax", YEAR).sum()
    dynamic = simulate(elasticity=1.0).calculate("capital_gains_tax", YEAR).sum()

    assert dynamic < static
    assert dynamic > 0


def test_zero_elasticity_leaves_gains_unchanged():
    """The default elasticity of zero keeps costings static."""
    sim = simulate(elasticity=0)
    response = sim.calculate("capital_gains_behavioural_response", YEAR).sum()

    assert response == 0


def test_no_reform_produces_no_response():
    """A simulation with no reform reports no realisation response."""
    sim = Microsimulation(
        situation=SITUATION,
        scenario=Scenario(
            parameter_changes={
                "gov.simulation.capital_gains_responses.elasticity": {str(YEAR): 1.0}
            }
        ),
    )
    response = sim.calculate("capital_gains_behavioural_response", YEAR).sum()

    assert response == 0


def test_measurement_leaves_the_response_variable_active():
    """Measuring the rate change does not neutralise the response itself.

    Object identity, not formula presence: a neutralised wrapper still
    carries a formula, so the old assertion could not see the damage.
    """
    sim = simulate(elasticity=1.0)
    before = sim.tax_benefit_system.variables["capital_gains_behavioural_response"]
    sim.calculate("relative_capital_gains_mtr_change", YEAR)
    after = sim.tax_benefit_system.variables["capital_gains_behavioural_response"]

    assert after is before


def test_pre_created_measurement_branch_cannot_poison_the_system():
    """A branch pre-created under the measurement's name shares the parent
    system, and get_branch returns it without honouring clone_system — so
    neutralising there would disable the response for every later
    recalculation. The measurement must sidestep the name instead."""
    sim = simulate(elasticity=1.0)
    sim.get_branch("cgr_measurement")
    before = sim.tax_benefit_system.variables["capital_gains_behavioural_response"]

    response = sim.calculate("capital_gains_behavioural_response", YEAR).sum()
    after = sim.tax_benefit_system.variables["capital_gains_behavioural_response"]

    assert response < 0
    assert after is before


def test_two_gainers_in_one_household_respond_symmetrically():
    """Equal gainers get equal responses; the second adult is not dropped."""
    situation = {
        "people": {
            "first": {
                "age": {YEAR: 45},
                "employment_income": {YEAR: 100_000},
                "capital_gains": {YEAR: 200_000},
            },
            "second": {
                "age": {YEAR: 44},
                "employment_income": {YEAR: 100_000},
                "capital_gains": {YEAR: 200_000},
            },
        },
        "benunits": {"benunit": {"members": ["first", "second"]}},
        "households": {"household": {"members": ["first", "second"]}},
    }
    sim = Microsimulation(
        situation=situation,
        scenario=Scenario(
            parameter_changes={
                **EQUALISED_RATES,
                "gov.simulation.capital_gains_responses.elasticity": {str(YEAR): 1.0},
            }
        ),
    )

    responses = sim.calculate("capital_gains_behavioural_response", YEAR).values

    assert responses[0] < 0
    assert responses[0] == pytest.approx(responses[1])

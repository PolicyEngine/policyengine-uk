"""Tests for the capital gains realisation response to CGT rate changes."""

import math

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


def simulate(
    elasticity: float | None = None,
    mtr_elasticity: float | None = None,
    rates: bool = True,
    rate_changes: dict | None = None,
) -> Microsimulation:
    reform_rates = EQUALISED_RATES if rate_changes is None else rate_changes
    changes = dict(reform_rates) if rates else {}
    if elasticity is not None:
        changes["gov.simulation.capital_gains_responses.elasticity"] = {
            str(YEAR): elasticity
        }
    if mtr_elasticity is not None:
        changes["gov.simulation.capital_gains_responses.mtr_elasticity"] = {
            str(YEAR): mtr_elasticity
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


def test_default_elasticities_leave_gains_unchanged():
    """Both elasticity conventions default to zero, keeping costings static."""
    sim = simulate()
    response = sim.calculate("capital_gains_behavioural_response", YEAR).sum()

    assert response == 0


def test_mtr_response_matches_hand_calculated_factor():
    """The MTR elasticity applies the exact marginal-rate log change."""
    mtr_elasticity = -0.5
    sim = simulate(mtr_elasticity=mtr_elasticity)

    gains = sim.calculate("capital_gains_before_response", YEAR).values[0]
    response = sim.calculate("capital_gains_behavioural_response", YEAR).values[0]
    actual_factor = response / gains
    expected_factor = math.exp(mtr_elasticity * (math.log(0.45) - math.log(0.24))) - 1

    assert actual_factor == pytest.approx(expected_factor, abs=1e-6)


def test_mtr_change_clamps_zero_marginal_rate():
    """A zero MTR uses the 0.001 floor instead of taking log(0)."""
    zero_rates = {parameter: {str(YEAR): 0.0} for parameter in EQUALISED_RATES}
    sim = simulate(mtr_elasticity=-0.5, rate_changes=zero_rates)

    mtr_change = sim.calculate("relative_capital_gains_mtr_change", YEAR).values[0]
    expected_change = math.log(0.001) - math.log(0.24)

    assert math.isfinite(mtr_change)
    assert mtr_change == pytest.approx(expected_change, abs=1e-6)


def test_both_elasticities_raise():
    """The retention-rate and MTR conventions cannot both be activated."""
    sim = simulate(elasticity=1.0, mtr_elasticity=-0.5)

    with pytest.raises(
        ValueError,
        match=(
            r"gov\.simulation\.capital_gains_responses\.elasticity and "
            r"gov\.simulation\.capital_gains_responses\.mtr_elasticity"
        ),
    ):
        sim.calculate("capital_gains_behavioural_response", YEAR)


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


def test_mtr_response_is_deterministic_across_recalculation():
    """Repeated MTR measurement is idempotent and leaves the response live."""
    sim = simulate(mtr_elasticity=-0.5)
    live_variable = sim.tax_benefit_system.variables[
        "capital_gains_behavioural_response"
    ]

    first = sim.calculate("capital_gains_behavioural_response", YEAR).values.copy()
    sim.delete_arrays("capital_gains_behavioural_response", YEAR)
    sim.delete_arrays("relative_capital_gains_mtr_change", YEAR)
    second = sim.calculate("capital_gains_behavioural_response", YEAR).values.copy()
    response_variable = sim.tax_benefit_system.variables[
        "capital_gains_behavioural_response"
    ]

    assert second == pytest.approx(first)
    assert response_variable is live_variable
    assert not response_variable.is_neutralized


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

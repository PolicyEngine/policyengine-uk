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


# Business Asset Disposal Relief elasticity (issue #1979). Three people on
# £200k of earnings with £500k of gains each in 2026: a claimant whose gains
# all qualify for the relief, an investor with none, and a mixed case with
# half. The reform charges every schedule at income tax rates and withdraws
# the relief, so the claimant's marginal rate goes from 18% to 45%, the
# investor's from 24% and the mixed case's from the share-weighted 21%.
# Qualifying gains respond at the BADR elasticity and the rest at the main
# one, both to the person's share-weighted rate change.

BADR_GAINS = {"claimant": 500_000, "investor": 0, "mixed": 250_000}

EQUALISATION = {
    f"gov.hmrc.cgt.{schedule}{band}": {str(YEAR): rate}
    for schedule in ("", "residential_property.", "carried_interest.")
    for band, rate in (
        ("basic_rate", 0.20),
        ("higher_rate", 0.40),
        ("additional_rate", 0.45),
    )
}
EQUALISATION["gov.hmrc.cgt.badr.lifetime_limit"] = {str(YEAR): 0}


def simulate_badr(**responses) -> Microsimulation:
    people = {}
    for name, badr_gains in BADR_GAINS.items():
        person = {
            "age": {YEAR: 50},
            "employment_income": {YEAR: 200_000},
            "capital_gains": {YEAR: 500_000},
        }
        if badr_gains:
            person["capital_gains_badr"] = {YEAR: badr_gains}
        people[name] = person
    situation = {
        "people": people,
        "benunits": {f"{name}_benunit": {"members": [name]} for name in people},
        "households": {f"{name}_household": {"members": [name]} for name in people},
    }
    changes = dict(EQUALISATION)
    for name, value in responses.items():
        changes[f"gov.simulation.capital_gains_responses.{name}"] = {str(YEAR): value}
    return Microsimulation(
        situation=situation, scenario=Scenario(parameter_changes=changes)
    )


def realisation_factors(sim) -> list:
    """Realised over pre-response gains, for each person."""
    gains = sim.calculate("capital_gains_before_response", YEAR).values
    response = sim.calculate("capital_gains_behavioural_response", YEAR).values
    return list(1 + response / gains)


def factor(elasticity: float, baseline_rate: float) -> float:
    """exp(e x log change in the retention rate) for a move to 45%."""
    return math.exp(elasticity * math.log(0.55 / (1 - baseline_rate)))


def test_badr_claimants_take_the_main_elasticity_by_default():
    """With the switch off, existing results don't move: everyone responds
    at the main elasticity."""
    sim = simulate_badr(elasticity=3.6)

    assert realisation_factors(sim) == pytest.approx(
        [factor(3.6, 0.18), factor(3.6, 0.24), factor(3.6, 0.21)], abs=1e-4
    )


def test_badr_elasticity_applies_to_qualifying_gains():
    """The OBR's assumptions: 1.4 for BADR gains and 3.6 for main-rate gains.

    The mixed case's qualifying half responds at 1.4 and its other half at
    3.6. The relief is withdrawn in the reform, so this also checks that
    qualifying gains keep the BADR elasticity when none of them is charged
    at the BADR rate any more.
    """
    sim = simulate_badr(elasticity=3.6, separate_badr_elasticity=True)

    assert list(sim.calculate("capital_gains_elasticity", YEAR).values) == (
        pytest.approx([3.6, 3.6, 3.6])
    )
    assert list(sim.calculate("capital_gains_badr_elasticity", YEAR).values) == (
        pytest.approx([1.4, 1.4, 1.4])
    )
    mixed = 0.5 * factor(1.4, 0.21) + 0.5 * factor(3.6, 0.21)
    assert realisation_factors(sim) == pytest.approx(
        [factor(1.4, 0.18), factor(3.6, 0.24), mixed], abs=1e-4
    )


def test_badr_elasticity_alone_moves_only_qualifying_gains():
    """A BADR elasticity with the main elasticity left at zero still responds,
    on the qualifying gains alone."""
    sim = simulate_badr(separate_badr_elasticity=True)

    mixed = 0.5 * factor(1.4, 0.21) + 0.5
    assert realisation_factors(sim) == pytest.approx(
        [factor(1.4, 0.18), 1.0, mixed], abs=1e-4
    )


def test_relief_gains_keep_their_own_response_in_the_tax():
    """Where the relief survives the reform, the qualifying gains are charged
    after their own response, not a pooled share of everyone's.

    The mixed case under main rates of 28%: its share-weighted rate goes from
    21% to 23%. £3,000 of exempt amount goes against the main-rate gains.
    """
    year = YEAR
    sim = Microsimulation(
        situation={
            "people": {
                "mixed": {
                    "age": {year: 50},
                    "employment_income": {year: 200_000},
                    "capital_gains": {year: 500_000},
                    "capital_gains_badr": {year: 250_000},
                }
            },
            "benunits": {"benunit": {"members": ["mixed"]}},
            "households": {"household": {"members": ["mixed"]}},
        },
        scenario=Scenario(
            parameter_changes={
                "gov.hmrc.cgt.higher_rate": {str(year): 0.28},
                "gov.hmrc.cgt.additional_rate": {str(year): 0.28},
                "gov.simulation.capital_gains_responses.elasticity": {str(year): 3.6},
                "gov.simulation.capital_gains_responses.separate_badr_elasticity": {
                    str(year): True
                },
            }
        ),
    )
    change = math.log(0.77 / 0.79)
    badr_after = 250_000 * math.exp(1.4 * change)
    main_after = 250_000 * math.exp(3.6 * change)
    expected = 0.28 * (main_after - 3_000) + 0.18 * badr_after

    tax = sim.calculate("capital_gains_tax", year).values[0]
    assert tax == pytest.approx(expected, abs=1)


def test_badr_and_mtr_elasticities_raise():
    """The BADR elasticity is a retention-rate elasticity, so it cannot be
    combined with the MTR convention."""
    sim = simulate_badr(separate_badr_elasticity=True, mtr_elasticity=-0.5)

    with pytest.raises(ValueError, match=r"badr_elasticity"):
        sim.calculate("capital_gains_behavioural_response", YEAR)

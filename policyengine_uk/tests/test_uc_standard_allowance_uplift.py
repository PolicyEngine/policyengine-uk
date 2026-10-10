"""Universal Credit standard allowance uplifts, Universal Credit Act 2025 s. 1
(issue #2239).

The Act sets each year's minimum standard allowance for 2026-27 to 2029-30
by three steps: take the previous year's CPI-uprated (Step 2) amount, or the
2025-26 amount for 2026-27; increase it by CPI (never below 0%); then by that
year's uplift (2.3%, 3.1%, 4.0%, 4.8%). The 2026-27 amounts are legislated
in amount.yaml; later years are uprated by CPI times the change in uplift.

Invariants:

1. Growth: in every year, each amount grows by the benefit CPI index ratio
   times (1 + this year's uplift) / (1 + last year's uplift), and by CPI
   alone after 2029-30.
2. Differential: the amounts equal an independent step-by-step
   implementation of s. 1(2), started from the 2026-27 Step 2 amounts (the
   legislated amounts less the 2.3% uplift).
3. The uplift in force: a reform to any year's uplift, or switching
   rebalancing off (no uplift), scales that year's amount by
   (1 + uplift) / (1 + statutory uplift), including the legislated 2026-27
   amounts, and leaves the CPI path alone.
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario

CLAIMANT_TYPES = ["SINGLE_YOUNG", "SINGLE_OLD", "COUPLE_YOUNG", "COUPLE_OLD"]
# Universal Credit Act 2025 s. 1(4).
ACT_UPLIFT = {2026: 0.023, 2027: 0.031, 2028: 0.040, 2029: 0.048}
YEARS = range(2026, 2033)
UPLIFT = "gov.dwp.universal_credit.rebalancing.standard_allowance_uplift"
ACTIVE = "gov.dwp.universal_credit.rebalancing.active"
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def _amounts(scenario=None):
    """Monthly standard allowance by claimant type and year, and the benefit
    CPI index, read through processed parameters."""
    sim = Simulation(
        situation={
            "people": {"p": {"age": {2026: 30}}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        },
        scenario=scenario,
    )
    parameters = sim.tax_benefit_system.parameters
    amounts = {
        year: {
            t: float(
                parameters(
                    f"{year}-06-01"
                ).gov.dwp.universal_credit.standard_allowance.amount[t]
            )
            for t in CLAIMANT_TYPES
        }
        for year in [2025, *YEARS]
    }
    cpi = {
        year: float(parameters(f"{year}-06-01").gov.benefit_uprating_cpi)
        for year in [2025, *YEARS]
    }
    return sim, amounts, cpi


def _uplift(year, schedule=ACT_UPLIFT):
    return schedule[min(year, 2029)] if year >= 2026 else 0.0


def test_single_claimant_aged_30_matches_the_act():
    """The issue's reproducer: annual uc_standard_allowance for a single
    claimant aged 30 now carries the 2027-28 to 2029-30 uplifts."""
    sim, amounts, cpi = _amounts()
    annual = {
        year: float(sim.calculate("uc_standard_allowance", year)[0])
        for year in range(2025, 2031)
    }
    assert annual[2025] == pytest.approx(400.14 * 12)
    assert annual[2026] == pytest.approx(424.90 * 12)
    for year in range(2027, 2031):
        cpi_growth = cpi[year] / cpi[year - 1]
        uplift_change = (1 + _uplift(year)) / (1 + _uplift(year - 1))
        # Simulated values are float32, so compare to the penny.
        assert annual[year] == pytest.approx(
            annual[year - 1] * cpi_growth * uplift_change, abs=0.01
        )
    # Before the fix 2027 grew by CPI alone (+2.3%); the 3.1% uplift adds a
    # further (1.031 / 1.023 - 1) = 0.78%.
    assert annual[2027] / annual[2026] == pytest.approx(
        cpi[2027] / cpi[2026] * 1.031 / 1.023, rel=1e-6
    )


def test_amounts_match_the_act_step_by_step():
    _, amounts, cpi = _amounts()
    for t in CLAIMANT_TYPES:
        # Step 2 amount for 2026-27: the legislated amount less its uplift.
        step_2 = amounts[2026][t] / (1 + ACT_UPLIFT[2026])
        for year in range(2027, 2030):
            step_2 *= max(1.0, cpi[year] / cpi[year - 1])  # Steps 1 and 2
            minimum = step_2 * (1 + ACT_UPLIFT[year])  # Step 3
            assert amounts[year][t] == pytest.approx(minimum, rel=1e-9)
        # After 2029-30 the Act no longer applies: CPI uprating alone.
        for year in range(2030, 2033):
            assert amounts[year][t] == pytest.approx(
                amounts[year - 1][t] * cpi[year] / cpi[year - 1], rel=1e-9
            )


uplift_schedule = st.fixed_dictionaries(
    {year: st.floats(0, 0.15) for year in range(2026, 2030)}
)


@PROPERTY_SETTINGS
@given(uplift_schedule)
def test_growth_is_cpi_times_the_change_in_uplift(schedule):
    scenario = Scenario(
        parameter_changes={UPLIFT: {str(y): u for y, u in schedule.items()}}
    )
    _, amounts, cpi = _amounts(scenario)
    _, baseline, _ = _amounts()
    for t in CLAIMANT_TYPES:
        # The legislated 2026-27 amounts carry the uplift in force.
        assert amounts[2026][t] == pytest.approx(
            baseline[2026][t] * (1 + schedule[2026]) / (1 + ACT_UPLIFT[2026]),
            rel=1e-9,
        )
        for year in range(2027, 2030):
            assert amounts[year][t] == pytest.approx(
                amounts[year - 1][t]
                * max(1.0, cpi[year] / cpi[year - 1])
                * (1 + schedule[year])
                / (1 + schedule[year - 1]),
                rel=1e-9,
            )
        # Keyed to fiscal years, the reform ends with 2029-30, when the
        # statutory 4.8% applies again.
        assert amounts[2030][t] == pytest.approx(
            amounts[2029][t]
            * cpi[2030]
            / cpi[2029]
            * (1 + ACT_UPLIFT[2029])
            / (1 + schedule[2029]),
            rel=1e-9,
        )
        assert amounts[2030][t] == pytest.approx(baseline[2030][t], rel=1e-9)


@PROPERTY_SETTINGS
@given(st.integers(2026, 2030))
def test_switching_rebalancing_off_removes_the_uplift_from_that_year(first_off):
    scenario = Scenario(parameter_changes={ACTIVE: {str(first_off): False}})
    _, amounts, cpi = _amounts(scenario)
    _, baseline, _ = _amounts()
    for t in CLAIMANT_TYPES:
        for year in YEARS:
            in_force = 0.0 if year == first_off else _uplift(year)
            assert amounts[year][t] == pytest.approx(
                baseline[year][t] * (1 + in_force) / (1 + _uplift(year)),
                rel=1e-9,
            )


def test_rebalancing_off_throughout_is_cpi_only_from_2025_26():
    scenario = Scenario(parameter_changes={ACTIVE: False})
    _, amounts, cpi = _amounts(scenario)
    for t in CLAIMANT_TYPES:
        # The legislated 2026-27 rates less their 2.3% uplift are the 2025-26
        # rates uprated by September 2025 CPI (3.8%) and rounded to the
        # penny, as the rates were set at each step. The single under-25 rate
        # was set above the Act's minimum, so is left out.
        if t != "SINGLE_YOUNG":
            assert amounts[2026][t] == pytest.approx(
                round(amounts[2025][t] * 1.038, 2), abs=0.01
            )
        for year in range(2027, 2033):
            assert amounts[year][t] == pytest.approx(
                amounts[year - 1][t] * cpi[year] / cpi[year - 1], rel=1e-9
            )


def test_amount_reforms_override_the_uplift():
    """A reform to the amount itself, as the fiscal-event replay's CPI-only
    counterfactual sets, is used as given."""
    reformed = Simulation(
        situation={
            "people": {"p": {"age": {2028: 30}}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        },
        reform={
            "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
                "2028": 430.0
            }
        },
    )
    assert reformed.calculate("uc_standard_allowance", 2028)[0] == pytest.approx(
        430.0 * 12
    )


def test_scalar_activation_matches_baseline():
    """Switching rebalancing on for all years (a scalar change from 2000)
    leaves the uplift nil before it starts and matches the baseline."""
    _, amounts, _ = _amounts(Scenario(parameter_changes={ACTIVE: True}))
    _, baseline, _ = _amounts()
    for year in YEARS:
        for t in CLAIMANT_TYPES:
            assert amounts[year][t] == pytest.approx(baseline[year][t], rel=1e-9)


@pytest.mark.parametrize(
    "other_change",
    [{ACTIVE: False}, {UPLIFT: {"2026": 0.10, "2027": 0.10}}],
)
def test_amount_set_by_a_reform_is_not_rescaled(other_change):
    """An amount a reform sets is used as given, whatever the uplift."""
    scenario = Scenario(
        parameter_changes={
            "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
                "2026": 500.0
            },
            **other_change,
        }
    )
    _, amounts, _ = _amounts(scenario)
    assert amounts[2026]["SINGLE_OLD"] == pytest.approx(500.0, rel=1e-9)


def test_reform_to_the_benefit_index_is_followed():
    """With the benefit uprating index held flat, the allowance moves only
    with the change in uplift."""
    scenario = Scenario(parameter_changes={"gov.benefit_uprating_cpi": 300.0})
    _, amounts, cpi = _amounts(scenario)
    assert all(cpi[year] == pytest.approx(300.0) for year in YEARS)
    for t in CLAIMANT_TYPES:
        for year in range(2027, 2033):
            assert amounts[year][t] == pytest.approx(
                amounts[year - 1][t] * (1 + _uplift(year)) / (1 + _uplift(year - 1)),
                rel=1e-9,
            )

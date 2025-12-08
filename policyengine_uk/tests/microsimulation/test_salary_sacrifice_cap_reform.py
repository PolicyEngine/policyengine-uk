"""
Test suite for salary sacrifice pension cap reform fiscal impacts.

This tests the £2,000 salary sacrifice cap policy announced in Autumn Budget 2025,
which takes effect from April 2029.

Methodology (matching blog at https://policyengine.org/uk/research/uk-salary-sacrifice-cap):
- Employees redirect excess above £2,000 to regular pension contributions
- Regular pension contributions get income tax relief but NOT NI relief
- Broad-base haircut: employers spread NI costs across ALL workers (~0.16% of employment income)
- Revenue comes from NI on the redirected excess

Expected revenue: ~£3.3 billion in 2029-30

Reference: https://policyengine.org/uk/research/uk-salary-sacrifice-cap
"""

import pytest
import numpy as np
import pandas as pd
from policyengine_uk import Microsimulation


# Policy year when the salary sacrifice cap takes effect
POLICY_YEAR = 2030  # Use 2030 to ensure cap is active (cap starts 2029-04-06)

# Expected revenue impact in billions (from blog)
# PolicyEngine baseline estimate: £3.3 billion
# OBR static estimate: £4.9 billion
# OBR post-behavioural: £4.7 billion
EXPECTED_REVENUE_BILLION = 3.3
TOLERANCE_BILLION = (
    1.5  # Allow reasonable tolerance for year/methodology differences
)


def _create_no_cap_baseline():
    """Create baseline simulation without the salary sacrifice cap."""
    return {
        "gov.hmrc.national_insurance.salary_sacrifice_pension_cap": {
            "2029": float("inf"),
            "2030": float("inf"),
        }
    }


@pytest.fixture(scope="module")
def baseline_simulation():
    """Create baseline simulation without the salary sacrifice cap."""
    return Microsimulation(reform=_create_no_cap_baseline())


@pytest.fixture(scope="module")
def reform_simulation():
    """Create reform simulation with the £2,000 salary sacrifice cap.

    Current law already has the cap from 2029-04-06, so we use
    a plain Microsimulation without additional reform parameters.
    """
    return Microsimulation()


def test_salary_sacrifice_cap_revenue_impact(
    baseline_simulation, reform_simulation
):
    """
    Test that the £2,000 salary sacrifice cap raises ~£3.3 billion.

    This matches the PolicyEngine blog methodology:
    - Employees redirect excess to regular pension contributions
    - Full excess subject to NI (broad-base haircut reduces all workers' income)
    - Income tax relief preserved via regular pension contributions
    """
    baseline_gov_balance = baseline_simulation.calculate(
        "gov_balance", POLICY_YEAR
    ).sum()
    reform_gov_balance = reform_simulation.calculate(
        "gov_balance", POLICY_YEAR
    ).sum()

    revenue_impact_billion = (reform_gov_balance - baseline_gov_balance) / 1e9

    print(f"\nBaseline gov_balance: £{baseline_gov_balance/1e9:.3f} billion")
    print(f"Reform gov_balance: £{reform_gov_balance/1e9:.3f} billion")
    print(f"Revenue impact: £{revenue_impact_billion:.3f} billion")

    # The reform should raise revenue (positive impact)
    assert revenue_impact_billion > 0, (
        f"Salary sacrifice cap should raise revenue, "
        f"but impact is {revenue_impact_billion:.2f} billion"
    )

    # Revenue should be approximately £3.3 billion
    assert (
        abs(revenue_impact_billion - EXPECTED_REVENUE_BILLION)
        < TOLERANCE_BILLION
    ), (
        f"Salary sacrifice cap revenue is {revenue_impact_billion:.2f} billion, "
        f"expected ~{EXPECTED_REVENUE_BILLION:.1f} billion "
        f"(±{TOLERANCE_BILLION:.1f} billion tolerance)"
    )


def test_ni_increases_with_reform(baseline_simulation, reform_simulation):
    """
    Test that total NI increases when the cap is applied.

    The reform adds excess salary sacrifice back to employment income,
    which is then subject to NI through the normal Class 1 calculation.
    """
    baseline_ni = baseline_simulation.calculate(
        "total_national_insurance", POLICY_YEAR
    ).sum()
    reform_ni = reform_simulation.calculate(
        "total_national_insurance", POLICY_YEAR
    ).sum()

    ni_increase = reform_ni - baseline_ni

    print(f"\nBaseline NI: £{baseline_ni/1e9:.3f}bn")
    print(f"Reform NI: £{reform_ni/1e9:.3f}bn")
    print(f"NI increase: £{ni_increase/1e9:.3f}bn")

    # NI should increase with the reform
    assert (
        ni_increase > 0
    ), f"NI should increase with cap, but change is £{ni_increase/1e9:.3f}bn"

    # NI increase should be significant (at least £1bn)
    assert (
        ni_increase > 1e9
    ), f"NI increase should be >£1bn, got £{ni_increase/1e9:.3f}bn"


def test_income_tax_impact(baseline_simulation, reform_simulation):
    """
    Test the income tax impact of the reform.

    The excess is added to employment income and to employee pension
    contributions for relief. Due to pension relief caps, some people
    don't get full relief, resulting in a small positive income tax impact.
    """
    baseline_tax = baseline_simulation.calculate(
        "income_tax", POLICY_YEAR
    ).sum()
    reform_tax = reform_simulation.calculate("income_tax", POLICY_YEAR).sum()

    tax_change = reform_tax - baseline_tax

    print(f"\nBaseline income tax: £{baseline_tax/1e9:.3f}bn")
    print(f"Reform income tax: £{reform_tax/1e9:.3f}bn")
    print(f"Income tax change: £{tax_change/1e9:.3f}bn")

    # Income tax should increase slightly (due to pension relief caps)
    # Expected to be around £1-2bn
    assert (
        tax_change > 0
    ), f"Income tax should increase, got £{tax_change/1e9:.3f}bn"
    assert (
        tax_change < 3e9
    ), f"Income tax increase should be <£3bn, got £{tax_change/1e9:.3f}bn"


def test_excess_redirected_to_pension(reform_simulation):
    """
    Test that full excess is redirected to employee pension contributions.

    The blog assumes employees maintain their total pension contributions
    by redirecting the full excess to regular pension contributions.
    """
    redirected = reform_simulation.calculate(
        "salary_sacrifice_returned_to_income", POLICY_YEAR
    ).sum()

    # Should be significant (blog says £13.8bn excess - full amount redirected)
    assert (
        redirected > 12e9
    ), f"Redirected amount should be >£12bn, got £{redirected/1e9:.2f}bn"


def test_salary_sacrifice_data_exists(reform_simulation):
    """
    Test that salary sacrifice data exists in the simulation.

    Blog: 4.9 million workers with SS contributions, £22.7 billion total.
    """
    ss_contributions = reform_simulation.calculate(
        "pension_contributions_via_salary_sacrifice", POLICY_YEAR
    )

    total_ss = ss_contributions.sum()
    num_contributors = (ss_contributions > 0).sum()

    # Should have significant SS contributions
    assert (
        total_ss > 20e9
    ), f"Total SS contributions should be >£20bn, got £{total_ss/1e9:.2f}bn"
    assert (
        num_contributors > 4e6
    ), f"Should have >4 million contributors, got {num_contributors/1e6:.1f}m"


def test_affected_population(reform_simulation):
    """
    Test that a reasonable number of people are affected by the cap.

    Blog: 3.3 million workers exceed the £2,000 cap (68% of contributors).
    """
    ss_contributions = reform_simulation.calculate(
        "pension_contributions_via_salary_sacrifice", POLICY_YEAR
    )

    cap = 2000
    affected_count = (ss_contributions > cap).sum()

    # Should be around 3.3 million
    assert (
        affected_count > 2.5e6
    ), f"Expected >2.5 million affected, got {affected_count/1e6:.1f}m"
    assert (
        affected_count < 5e6
    ), f"Expected <5 million affected, got {affected_count/1e6:.1f}m"


def test_full_excess_redirected(reform_simulation):
    """
    Test that the full excess is redirected (no targeted haircut).

    The broad-base haircut reduces ALL workers' employment income,
    but the full excess above cap is redirected to regular pension contributions.
    """
    # Get weighted totals using map_to for proper aggregation
    ss_contributions = reform_simulation.calculate(
        "pension_contributions_via_salary_sacrifice",
        POLICY_YEAR,
        map_to="person",
    )
    weights = reform_simulation.calculate("person_weight", POLICY_YEAR)
    redirected = reform_simulation.calculate(
        "salary_sacrifice_returned_to_income", POLICY_YEAR, map_to="person"
    )

    cap = 2000
    raw_excess = (np.maximum(ss_contributions - cap, 0) * weights).sum()
    redirected_total = (redirected * weights).sum()

    # Redirected should be 100% of raw excess (no targeted haircut)
    ratio = redirected_total / raw_excess if raw_excess > 0 else 0

    assert 0.95 < ratio < 1.05, (
        f"Full excess should be redirected (ratio ~1.0). "
        f"Raw excess: £{raw_excess/1e9:.2f}bn, "
        f"Redirected: £{redirected_total/1e9:.2f}bn, "
        f"Ratio: {ratio:.2f}"
    )


def test_broad_base_haircut_affects_all_workers(reform_simulation):
    """
    Test that the broad-base haircut reduces employment income for all workers.

    The broad-base haircut (default 0.16%) applies to ALL workers,
    not just those with salary sacrifice.
    """
    haircut = reform_simulation.calculate(
        "salary_sacrifice_broad_base_haircut", POLICY_YEAR
    )
    weights = reform_simulation.calculate("person_weight", POLICY_YEAR)
    employment_income = reform_simulation.calculate(
        "employment_income_before_lsr", POLICY_YEAR
    )

    # All workers with employment income should have a haircut
    has_employment = employment_income > 0
    has_haircut = haircut < 0  # Haircut is negative

    # Count workers with employment income but no haircut
    workers_with_employment = (has_employment * weights).sum()
    workers_with_haircut = (has_haircut * weights).sum()

    print(
        f"\nWorkers with employment income: {workers_with_employment/1e6:.1f}m"
    )
    print(f"Workers with haircut: {workers_with_haircut/1e6:.1f}m")

    # Most workers with employment income should have a haircut
    haircut_coverage = workers_with_haircut / workers_with_employment
    assert haircut_coverage > 0.9, (
        f"Broad-base haircut should affect most workers, "
        f"but only {haircut_coverage:.1%} are affected"
    )


def test_decile_impact_negative_for_higher_earners(
    baseline_simulation, reform_simulation
):
    """
    Test that higher income deciles experience negative income changes.

    The salary sacrifice cap reduces household net income for affected workers
    (those with SS contributions > £2,000) because they now pay NI on the excess.
    Higher deciles should have larger negative impacts as they're more likely
    to have high salary sacrifice contributions.

    This validates the distributional impact methodology used in uk-budget-data.
    """
    # Calculate household net income for baseline and reform
    baseline_income = baseline_simulation.calculate(
        "household_net_income", period=POLICY_YEAR, map_to="household"
    )
    reform_income = reform_simulation.calculate(
        "household_net_income", period=POLICY_YEAR, map_to="household"
    )
    household_decile = baseline_simulation.calculate(
        "household_income_decile", period=POLICY_YEAR, map_to="household"
    )
    household_weight = baseline_simulation.calculate(
        "household_weight", period=POLICY_YEAR, map_to="household"
    )

    # Build decile DataFrame
    decile_df = pd.DataFrame(
        {
            "household_income_decile": household_decile.values,
            "baseline_income": baseline_income.values,
            "reform_income": reform_income.values,
            "income_change": (reform_income - baseline_income).values,
            "household_weight": household_weight.values,
        }
    )
    decile_df = decile_df[decile_df["household_income_decile"] >= 1]

    # Calculate weighted relative change by decile
    decile_names = [
        "1st",
        "2nd",
        "3rd",
        "4th",
        "5th",
        "6th",
        "7th",
        "8th",
        "9th",
        "10th",
    ]
    results = []

    for decile_num in range(1, 11):
        decile_data = decile_df[
            decile_df["household_income_decile"] == decile_num
        ]
        if len(decile_data) > 0:
            weighted_change = (
                decile_data["income_change"] * decile_data["household_weight"]
            ).sum()
            weighted_baseline = (
                decile_data["baseline_income"]
                * decile_data["household_weight"]
            ).sum()
            rel_change = (
                (weighted_change / weighted_baseline) * 100
                if weighted_baseline > 0
                else 0
            )
            results.append(
                {
                    "decile": decile_names[decile_num - 1],
                    "decile_num": decile_num,
                    "rel_change_pct": rel_change,
                    "abs_change": weighted_change,
                }
            )

    print("\nDecile Impact (relative % change in household net income):")
    for r in results:
        print(f"  {r['decile']}: {r['rel_change_pct']:.3f}%")

    # Higher deciles (8th, 9th, 10th) should have negative impacts
    # These workers are more likely to have high salary sacrifice
    high_decile_results = [r for r in results if r["decile_num"] >= 8]

    for r in high_decile_results:
        assert r["rel_change_pct"] < 0, (
            f"Decile {r['decile']} should have negative impact "
            f"(losers from reform), got {r['rel_change_pct']:.3f}%"
        )

    # The 10th decile should have the largest negative impact
    decile_10 = next(r for r in results if r["decile_num"] == 10)
    assert decile_10["rel_change_pct"] < -0.1, (
        f"10th decile should have significant negative impact (<-0.1%), "
        f"got {decile_10['rel_change_pct']:.3f}%"
    )

    # Overall impact should be negative (reform takes money from households)
    total_change = sum(r["abs_change"] for r in results)
    print(f"\nTotal household income change: £{total_change/1e9:.3f}bn")
    assert total_change < 0, (
        f"Total household income should decrease, "
        f"got £{total_change/1e9:.3f}bn change"
    )

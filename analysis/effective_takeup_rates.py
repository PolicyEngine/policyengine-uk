"""
Comprehensive analysis of effective take-up rates across all UK benefit programs.

This script calculates effective take-up rates after reweighting and SPI integration
for all major benefit programs in PolicyEngine UK.

Related to issue #1354: https://github.com/PolicyEngine/policyengine-uk/issues/1354
"""

from policyengine_uk import Microsimulation
import pandas as pd
import numpy as np
from datetime import datetime

# Analysis periods
PERIODS = [2025, 2026, 2029]

# Benefits with take-up parameters defined in the model
BENEFITS_CONFIG = {
    # Benefits with active take-up implementation
    "universal_credit": {
        "param_path": "gov.dwp.universal_credit.takeup_rate",
        "seeded_rate": 0.55,
        "entity": "benunit",
        "active": True,
        "notes": "Stochastic take-up applied in microsimulation",
    },
    "pension_credit": {
        "param_path": "gov.dwp.pension_credit.takeup",
        "seeded_rate": 0.70,
        "entity": "benunit",
        "active": True,
        "notes": "Stochastic take-up with complex eligibility logic",
    },
    "child_benefit": {
        "param_path": "gov.hmrc.child_benefit.takeup.overall",
        "seeded_rate": 0.89,
        "entity": "person",
        "active": True,
        "notes": "Age-based take-up rates (0.61-0.97 by age)",
    },
    "marriage_allowance": {
        "param_path": "gov.hmrc.income_tax.allowances.marriage_allowance.takeup_rate",
        "seeded_rate": 1.0,
        "entity": "person",
        "active": True,
        "notes": "Currently set to 100%, no actual take-up modeled",
    },
    # Legacy benefits with parameters but no active implementation
    "child_tax_credit": {
        "param_path": "gov.dwp.tax_credits.child_tax_credit.takeup",
        "seeded_rate": 1.0,
        "entity": "benunit",
        "active": False,
        "notes": "Legacy benefit - only existing claimants",
    },
    "working_tax_credit": {
        "param_path": "gov.dwp.tax_credits.working_tax_credit.takeup",
        "seeded_rate": 1.0,
        "entity": "benunit",
        "active": False,
        "notes": "Legacy benefit - only existing claimants",
    },
    "housing_benefit": {
        "param_path": "gov.dwp.housing_benefit.takeup",
        "seeded_rate": 1.0,
        "entity": "benunit",
        "active": False,
        "notes": "Legacy benefit - only existing claimants",
    },
    "income_support": {
        "param_path": "gov.dwp.income_support.takeup",
        "seeded_rate": 1.0,
        "entity": "benunit",
        "active": False,
        "notes": "Legacy benefit - only existing claimants",
    },
    # Additional benefits mentioned in the issue (no take-up params)
    "state_pension": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "person",
        "active": False,
        "notes": "No take-up parameter - universal entitlement",
    },
    "carers_allowance": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "person",
        "active": False,
        "notes": "No take-up parameter defined",
    },
    "attendance_allowance": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "person",
        "active": False,
        "notes": "No take-up parameter defined",
    },
    "dla": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "person",
        "active": False,
        "notes": "No take-up parameter defined",
    },
    "pip": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "person",
        "active": False,
        "notes": "No take-up parameter defined",
    },
    "esa_income": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "benunit",
        "active": False,
        "notes": "No take-up parameter defined",
    },
    "jsa_income": {
        "param_path": "gov.dwp.JSA.income.takeup",
        "seeded_rate": 0.56,  # 2015 value
        "entity": "benunit",
        "active": False,
        "notes": "Parameter exists but not implemented (historical data only)",
    },
    "council_tax_benefit": {
        "param_path": None,
        "seeded_rate": None,
        "entity": "benunit",
        "active": False,
        "notes": "No take-up parameter defined (Council Tax Reduction)",
    },
}


def calculate_effective_takeup(baseline_sim, full_takeup_sim, benefit_name, period):
    """
    Calculate effective take-up rate as the ratio of recipients in
    baseline vs 100% take-up scenario.

    Returns dict with metrics or None if benefit not applicable.
    """
    try:
        baseline_values = baseline_sim.calculate(benefit_name, period=period)
        full_values = full_takeup_sim.calculate(benefit_name, period=period)

        baseline_recipients = (baseline_values > 0).sum()
        full_recipients = (full_values > 0).sum()

        if full_recipients == 0:
            return {
                "baseline_recipients": int(baseline_recipients),
                "full_takeup_recipients": int(full_recipients),
                "baseline_spending_bn": round(baseline_values.sum() / 1e9, 3),
                "full_takeup_spending_bn": 0,
                "effective_takeup_rate": None,
                "spending_takeup_rate": None,
                "error": "No eligible recipients at 100% take-up",
            }

        effective_rate = baseline_recipients / full_recipients
        spending_rate = baseline_values.sum() / full_values.sum() if full_values.sum() > 0 else None

        return {
            "baseline_recipients": int(baseline_recipients),
            "full_takeup_recipients": int(full_recipients),
            "baseline_spending_bn": round(baseline_values.sum() / 1e9, 3),
            "full_takeup_spending_bn": round(full_values.sum() / 1e9, 3),
            "effective_takeup_rate": round(effective_rate * 100, 1),
            "spending_takeup_rate": round(spending_rate * 100, 1) if spending_rate else None,
        }
    except Exception as e:
        return {"error": str(e)}


def create_full_takeup_reform():
    """Create reform dictionary setting all take-up rates to 100%."""
    return {
        "gov.dwp.universal_credit.takeup_rate": {"2015-01-01.2100-12-31": 1.0},
        "gov.dwp.pension_credit.takeup": {"2015-01-01.2100-12-31": 1.0},
        "gov.hmrc.child_benefit.takeup.overall": {"2012-01-01.2100-12-31": 1.0},
    }


def run_analysis():
    """Run the complete take-up rate analysis."""
    print("=" * 70)
    print("EFFECTIVE TAKE-UP RATES ANALYSIS")
    print(f"PolicyEngine UK | {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 70)

    # Initialize simulations
    print("\nInitializing simulations...")
    baseline = Microsimulation()
    full_takeup = Microsimulation(reform=create_full_takeup_reform())

    results = []

    for period in PERIODS:
        print(f"\n{'=' * 70}")
        print(f"ANALYSIS FOR {period}")
        print("=" * 70)

        for benefit_name, config in BENEFITS_CONFIG.items():
            print(f"\n--- {benefit_name.replace('_', ' ').title()} ---")

            # Calculate effective take-up
            metrics = calculate_effective_takeup(
                baseline, full_takeup, benefit_name, period
            )

            if "error" in metrics:
                print(f"  Error/Note: {metrics.get('error', 'N/A')}")
                result = {
                    "period": period,
                    "benefit": benefit_name,
                    "seeded_rate": config["seeded_rate"],
                    "effective_rate": None,
                    "spending_rate": None,
                    "baseline_recipients": metrics.get("baseline_recipients"),
                    "full_recipients": metrics.get("full_takeup_recipients"),
                    "baseline_spending_bn": metrics.get("baseline_spending_bn"),
                    "full_spending_bn": metrics.get("full_takeup_spending_bn"),
                    "active_implementation": config["active"],
                    "notes": config["notes"],
                    "error": metrics.get("error"),
                }
            else:
                print(f"  Seeded take-up rate: {config['seeded_rate']}")
                print(
                    f"  Effective take-up rate: {metrics['effective_takeup_rate']}%"
                )
                print(
                    f"  Spending take-up rate: {metrics['spending_takeup_rate']}%"
                )
                print(
                    f"  Baseline recipients: {metrics['baseline_recipients']:,}"
                )
                print(
                    f"  Full take-up recipients: {metrics['full_takeup_recipients']:,}"
                )
                print(
                    f"  Baseline spending: £{metrics['baseline_spending_bn']:.2f}bn"
                )
                print(
                    f"  Full take-up spending: £{metrics['full_takeup_spending_bn']:.2f}bn"
                )

                # Calculate gap between seeded and effective
                if config["seeded_rate"] and metrics["effective_takeup_rate"]:
                    gap = metrics["effective_takeup_rate"] - (
                        config["seeded_rate"] * 100
                    )
                    print(
                        f"  Gap (effective - seeded): {gap:+.1f} percentage points"
                    )

                result = {
                    "period": period,
                    "benefit": benefit_name,
                    "seeded_rate": config["seeded_rate"],
                    "effective_rate": metrics["effective_takeup_rate"],
                    "spending_rate": metrics["spending_takeup_rate"],
                    "baseline_recipients": metrics["baseline_recipients"],
                    "full_recipients": metrics["full_takeup_recipients"],
                    "baseline_spending_bn": metrics["baseline_spending_bn"],
                    "full_spending_bn": metrics["full_takeup_spending_bn"],
                    "active_implementation": config["active"],
                    "notes": config["notes"],
                }

            results.append(result)

    # Create summary DataFrame
    df = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)

    # Create pivoted summary for active benefits
    active_benefits = df[df["active_implementation"] == True]
    if not active_benefits.empty:
        print("\n## Benefits with Active Take-up Implementation:")
        summary = active_benefits.pivot_table(
            index="benefit",
            columns="period",
            values=["seeded_rate", "effective_rate", "spending_rate"],
            aggfunc="first",
        )
        print(summary.to_string())

    return df


def generate_markdown_report(df):
    """Generate a markdown report from the analysis results."""
    report = """# Effective Take-Up Rates Analysis

## Overview

This analysis compares seeded take-up rates (from prior studies) with effective
take-up rates observed after reweighting and SPI integration in the PolicyEngine
UK microsimulation model.

## Key Findings

### Benefits with Active Take-up Implementation

| Benefit | Seeded Rate | 2025 Effective | 2026 Effective | 2029 Effective |
|---------|-------------|----------------|----------------|----------------|
"""

    for benefit in [
        "universal_credit",
        "pension_credit",
        "child_benefit",
        "marriage_allowance",
    ]:
        benefit_data = df[df["benefit"] == benefit]
        if benefit_data.empty:
            continue

        seeded = benefit_data["seeded_rate"].iloc[0]
        seeded_str = f"{seeded * 100:.0f}%" if seeded else "N/A"

        rates = {}
        for _, row in benefit_data.iterrows():
            rate = row["effective_rate"]
            rates[row["period"]] = f"{rate:.1f}%" if rate else "N/A"

        report += f"| {benefit.replace('_', ' ').title()} | {seeded_str} | "
        report += f"{rates.get(2025, 'N/A')} | {rates.get(2026, 'N/A')} | {rates.get(2029, 'N/A')} |\n"

    report += """
### Legacy Benefits (100% Take-up)

These benefits only track existing claimants (no new claims allowed):
- Child Tax Credit
- Working Tax Credit
- Housing Benefit
- Income Support

### Benefits Without Take-up Parameters

The following benefits do not have take-up modeling implemented:
- State Pension (universal entitlement)
- Carer's Allowance
- Attendance Allowance
- DLA (Disability Living Allowance)
- PIP (Personal Independence Payment)
- ESA (Employment and Support Allowance)
- JSA (Jobseeker's Allowance) - parameter exists but not implemented
- Council Tax Reduction

## Analysis Notes

1. **Effective take-up rate** = Recipients at baseline / Recipients at 100% take-up
2. **Spending take-up rate** = Spending at baseline / Spending at 100% take-up
3. Data processing (reweighting, SPI integration) affects effective rates
4. Effective rates may differ from seeded rates due to:
   - Survey reweighting adjustments
   - SPI data integration
   - Correlation between eligibility and other characteristics
   - Model assumptions about claiming behavior
"""

    return report


if __name__ == "__main__":
    print("Starting comprehensive take-up rate analysis...")
    print("This may take a few minutes to load the microsimulation data.\n")

    try:
        results_df = run_analysis()

        # Save results to CSV
        results_df.to_csv(
            "analysis/effective_takeup_results.csv", index=False
        )
        print("\nResults saved to analysis/effective_takeup_results.csv")

        # Generate markdown report
        report = generate_markdown_report(results_df)
        with open("analysis/effective_takeup_report.md", "w") as f:
            f.write(report)
        print("Report saved to analysis/effective_takeup_report.md")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure policyengine_uk is installed: pip install policyengine-uk")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

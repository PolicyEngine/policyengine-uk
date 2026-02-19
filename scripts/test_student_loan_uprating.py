"""
Test script: validate student loan plan uprating (2026-2029).

Prints the weighted number of people on each plan per year.

Run with:
    .venv/bin/python scripts/test_student_loan_uprating.py
"""

from policyengine.tax_benefit_models.uk import ensure_datasets

DATA_FOLDER = "/tmp/pe_student_loan_test"
YEARS = [2026, 2027, 2028, 2029]
PLANS = ["PLAN_1", "PLAN_2", "PLAN_5", "NONE"]


def get_plan_counts(year: int, datasets: dict) -> dict:
    dataset = datasets[f"enhanced_frs_2023_24_{year}"]
    person = dataset.data.person  # MicroDataFrame with person_weight
    return {
        plan: person[person["student_loan_plan"] == plan]
        .weights.sum()
        for plan in PLANS
    }


def main():
    print("Preparing datasets …")
    datasets = ensure_datasets(
        datasets=["hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5"],
        years=YEARS,
        data_folder=DATA_FOLDER,
    )
    print(f"Loaded: {list(datasets.keys())}\n")

    header = f"{'Year':>6}  " + "  ".join(f"{p:>10}" for p in PLANS) + f"  {'TOTAL_LOAN':>12}"
    print(header)
    print("-" * len(header))

    counts_by_year = {}
    for year in YEARS:
        counts = get_plan_counts(year, datasets)
        counts_by_year[year] = counts
        total_loan = sum(counts[p] for p in PLANS if p != "NONE")
        row = f"{year:>6}  " + "  ".join(f"{counts[p]/1e6:>9.3f}m" for p in PLANS)
        row += f"  {total_loan/1e6:>11.3f}m"
        print(row)

    print()
    print("Sanity checks:")

    # Plan 5 grows year-on-year
    prev = -1
    for year in YEARS:
        p5 = counts_by_year[year]["PLAN_5"]
        assert p5 >= prev, f"Plan 5 should not shrink: {year-1}={prev:,.0f} → {year}={p5:,.0f}"
        prev = p5
    print("  [PASS] Plan 5 count is non-decreasing")

    # Plan 1 shrinks year-on-year (write-offs exceed new entrants)
    prev = float("inf")
    for year in YEARS:
        p1 = counts_by_year[year]["PLAN_1"]
        assert p1 <= prev, f"Plan 1 should not grow: {year-1}={prev:,.0f} → {year}={p1:,.0f}"
        prev = p1
    print("  [PASS] Plan 1 count is non-increasing")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

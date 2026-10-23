# Child poverty validation: removing the two-child limit (2029-30)

This page compares PolicyEngine UK's estimate of the child-poverty
impact and fiscal cost of removing the [Universal Credit two-child
limit][gov-2cl] against the published estimates from the Department for
Work and Pensions, the Office for Budget Responsibility and the Resolution
Foundation. Budget 2025 announced the removal with effect from 6 April
2026, which the
`gov.dwp.universal_credit.elements.child.limit.child_count` parameter
encodes (`.inf` from `2026-04-06`).

Tracks [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398).

## Results

| Source | Children lifted from relative low income (2029-30) | Treasury cost (2029-30) |
|--------|----------------------------------------:|------------------------:|
| [DWP poverty impact assessment][gov-2cl] (children); [Budget 2025, Table 1.2][budget-2025] (cost, OBR-certified) | 450,000 (AHC); 300,000 (BHC) | £3.1 bn |
| [Resolution Foundation *No half measures*][rf-nhm] | 480,000 (AHC) | £3.5 bn |
| **PolicyEngine UK, Microcosm UK 2024-25 (AHC)** | **~548,000** | **£3.21 bn** |
| **PolicyEngine UK, Microcosm UK 2024-25 (BHC)** | **~460,000** | (same) |

All the figures are relative low income: below 60% of the contemporary
median. The PolicyEngine rows count HBAI dependent children
(`is_hbai_dependent_child`), as DWP does, and were run on 23 October 2026
on policyengine-uk 2.148.2 with the certified Microcosm UK 2024-25 national
release (`microcosm-uk-2024-25-national-20261019T083323Z-6cba5d71`, SHA-256
`810ba980…`). On that run PolicyEngine's headcounts are above DWP's and the
Resolution Foundation's, and its cost sits between the Budget 2025 and
Resolution Foundation figures.

On absolute low income (below 60% of the FYE 2025 median held constant in
real terms) the same run lifts ~549,000 children after housing costs and
~325,000 before, against DWP's 250,000 on both measures (Tables 3 and 4).

Earlier versions of this page reported ~463,000 (AHC) and ~336,000 (BHC)
children and £3.26 bn on an earlier Microcosm UK release (SHA-256
`aa31bdf6…`, policyengine-uk 2.123.7), and ~501,000, ~415,000 and £3.40 bn
on the Enhanced FRS 2022-23 in May 2026. The snippet behind them used
`in_poverty_ahc`, which is the absolute measure, and counted children with
`is_child`, so they are not comparable with the relative benchmarks above.

## How the estimate was produced

```python
from policyengine_uk import Microsimulation

# Local path to the Microcosm UK 2024-25 national release file.
DATASET = "microcosm_uk_2024_25.h5"
YEAR = 2029  # fiscal year 2029-30

# Current law baseline (TCL removed from 2026-04-06 per Budget 2025)
sim_baseline = Microsimulation(dataset=DATASET)

# Counterfactual where the TCL is held in place at 2 children
sim_counter = Microsimulation(
    dataset=DATASET,
    reform={
        "gov.dwp.universal_credit.elements.child.limit.child_count": {
            f"{YEAR}-01-01": 2,
        },
    },
)

# HBAI dependent children, as in DWP's statistics.
is_child = sim_baseline.calculate("is_hbai_dependent_child", YEAR)

for measure in ["in_relative_poverty_ahc", "in_relative_poverty_bhc"]:
    baseline = sim_baseline.calculate(measure, YEAR, map_to="person")
    counter = sim_counter.calculate(measure, YEAR, map_to="person")
    lifted = ((counter.astype(float) - baseline.astype(float)) * is_child).sum()
    print(f"{measure} children lifted: {lifted / 1e3:.0f}k")

fiscal_cost = (
    sim_counter.calculate("gov_balance", YEAR).sum()
    - sim_baseline.calculate("gov_balance", YEAR).sum()
)
print(f"Treasury cost: £{fiscal_cost / 1e9:.2f}bn")
```

This is a *reverse* comparison: PolicyEngine's baseline already includes
the TCL removal (the parameter flips to infinity from 2026-04-06), so the
counterfactual *re-imposes* the limit at 2 children to compute the
2029-30 effect. The signs cancel out: the children-lifted figure is
positive (baseline has fewer in poverty than counterfactual) and the
Treasury cost is positive (the baseline pays more Universal Credit, so its
`gov_balance`, tax less spending, is lower than the counterfactual's).

## Why the estimates differ

Three plausible drivers of the remaining differences:

1. **Nowcasting methodology**. RF projected with the OBR's March 2025
   earnings forecast and the Bank of England's August 2025 inflation
   forecast; DWP and the OBR used the OBR's November 2025 forecast. See the
   [PolicyEngine vs RF comparison](../assumptions/nowcasting-comparison.md)
   and the [RF methodology detail](../assumptions/rf-nowcasting-methodology.md)
   for where PolicyEngine's nowcasting differs from RF's.
2. **Take-up assumptions**. PolicyEngine decides Universal Credit claims
   with take-up flags set in the data (`would_claim_uc`), which do not
   respond to the reform. The data set the flag for every family that
   reports Universal Credit and draw it at a residual rate for the rest, so
   families newly entitled by the removal claim at that residual rate. A
   source that assumes lower take-up among newly entitled families would
   show a smaller headcount and cost.
3. **Data and calibration vintage**. The DWP and OBR estimates were
   finalised against the OBR's November 2025 forecast, and RF's
   (30 October 2025) against the OBR's March 2025 earnings forecast and the
   Bank of England's August 2025 inflation forecast; PolicyEngine's
   parameters tick over with each EFO release. The Microcosm release is
   built from FRS 2024-25, with take-up anchored on reported receipt.

## How to keep this validation alive

- Re-run the snippet on each new Microcosm UK release, and when the
  remaining `would_claim_*` conversions (#1621) land. Both could move the
  AHC poverty rate by a non-trivial amount.
- After each new EFO release, update the per-year poverty headcounts and
  the fiscal cost table.

## References

- HM Treasury, [Budget 2025][budget-2025], Table 1.2: the OBR-certified cost of removing the two-child limit (£3.1 billion in 2029-30).
- OBR, [Economic and Fiscal Outlook November 2025][obr-efo].
- Resolution Foundation, [No half measures: setting child poverty on a downward course at the Autumn Budget][rf-nhm] (30 October 2025).
- DWP, [Removing the two-child limit on Universal Credit: impact on low income poverty levels in the United Kingdom][gov-2cl], Tables 1 and 2 (relative low income) and 3 and 4 (absolute low income), financial year ending 2030.
- Issue: [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398). Related: [#1171](https://github.com/PolicyEngine/policyengine-uk/issues/1171), [#1388](https://github.com/PolicyEngine/policyengine-uk/issues/1388).

[obr-efo]: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
[budget-2025]: https://www.gov.uk/government/publications/budget-2025-document/budget-2025-html
[rf-nhm]: https://www.resolutionfoundation.org/publications/no-half-measures/
[gov-2cl]: https://www.gov.uk/government/publications/poverty-impacts-of-social-security-changes-at-budget-2025/removing-the-two-child-limit-on-universal-credit-impact-on-low-income-poverty-levels-in-the-united-kingdom

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

| Source | Children lifted from poverty (2029-30) | Treasury cost (2029-30) |
|--------|----------------------------------------:|------------------------:|
| [DWP poverty impact assessment][gov-2cl] (children); [Budget 2025, Table 1.2][budget-2025] (cost, OBR-certified) | 450,000 (AHC); 300,000 (BHC) | £3.1 bn |
| [Resolution Foundation *No half measures*][rf-nhm] | 480,000 (AHC) | £3.5 bn |
| **PolicyEngine UK, Microcosm UK 2024-25 (AHC)** | **~463,000** | **£3.26 bn** |
| **PolicyEngine UK, Microcosm UK 2024-25 (BHC)** | **~336,000** | (same) |
| PolicyEngine UK, Enhanced FRS 2022-23 (AHC), May 2026 | ~501,000 | £3.40 bn |
| PolicyEngine UK, Enhanced FRS 2022-23 (BHC), May 2026 | ~415,000 | (same) |

The October 2026 run uses the Microcosm UK 2024-25 national release
(SHA-256 `aa31bdf6…`) on policyengine-uk 2.123.7. On that dataset,
PolicyEngine's after-housing-costs headcount sits between the DWP and
Resolution Foundation figures, its before-housing-costs headcount is
above DWP's, and its cost sits between the Budget 2025 and Resolution
Foundation figures. The May 2026 Enhanced FRS run, kept for comparison,
was above both on headcount.

## How the estimate was produced

```python
from policyengine_uk import Microsimulation

# Local path to the Microcosm UK 2024-25 national release file.
DATASET = "microcosm_uk_2024_25.h5"
YEAR = 2029

# Current law baseline (TCL removed from 2026-04-06 per Budget 2025)
sim_baseline = Microsimulation(dataset=DATASET)

# Counterfactual where the TCL is held in place at 2 children
sim_counter = Microsimulation(dataset=DATASET, reform={
    "gov.dwp.universal_credit.elements.child.limit.child_count": {
        f"{YEAR}-01-01": 2,
    },
})

is_child = sim_baseline.calculate("is_child", YEAR)
in_poverty_baseline = sim_baseline.calculate(
    "in_poverty_ahc", YEAR, map_to="person"
).astype(float)
in_poverty_counter = sim_counter.calculate(
    "in_poverty_ahc", YEAR, map_to="person"
).astype(float)

children_lifted = ((in_poverty_counter - in_poverty_baseline) * is_child).sum()
fiscal_cost = (
    sim_counter.calculate("gov_balance", YEAR).sum()
    - sim_baseline.calculate("gov_balance", YEAR).sum()
)

print(f"AHC children lifted: {children_lifted/1e3:.0f}k")
print(f"Treasury cost:       £{fiscal_cost/1e9:.2f}bn")
```

This is a *reverse* comparison: PolicyEngine's baseline already includes
the TCL removal (the parameter flips to infinity from 2026-04-06), so the
counterfactual *re-imposes* the limit at 2 children to compute the
2029-30 effect. The signs cancel out: the children-lifted figure is
positive (baseline has fewer in poverty than counterfactual) and the
Treasury cost is positive (baseline collects less revenue than the
counterfactual would).

## Why the estimates differ

Three plausible drivers of the remaining differences, and of the move
between the Enhanced FRS and Microcosm runs:

1. **Nowcasting methodology**. RF and DWP/OBR use somewhat different
   earnings, rent, and benefit-uprating paths through 2029-30. See the
   [PolicyEngine vs RF comparison](../assumptions/nowcasting-comparison.md)
   and the [RF methodology detail](../assumptions/rf-nowcasting-methodology.md)
   for the specific divergence points.
2. **Take-up assumptions**. PolicyEngine applies the same Universal
   Credit take-up (`would_claim_uc`, set in the data) to families gaining
   entitlement from the removal as to existing claimants. A source that
   assumes lower take-up among newly entitled families would show a
   smaller headcount and cost.
3. **Data and calibration vintage**. The DWP, OBR and RF estimates were
   finalised against November 2025 assumptions; PolicyEngine's parameters tick
   over with each EFO release. The Microcosm release is built from FRS
   2024-25 rather than 2022-23, with take-up anchored on reported receipt.

## How to keep this validation alive

- Re-run the snippet on each new Microcosm UK release, and when the
  remaining `would_claim_*` conversions (#1621) land. Both could move the
  AHC poverty rate by a non-trivial amount.
- After each new EFO release, update the per-year poverty headcounts and
  the fiscal cost table.

## References

- HM Treasury, [Budget 2025][budget-2025], Table 1.2: the OBR-certified cost of removing the two-child limit (£3.1 billion in 2029-30).
- OBR, [Economic and Fiscal Outlook November 2025][obr-efo].
- Resolution Foundation, [No half measures: ending the two-child limit][rf-nhm].
- DWP, [Removing the two-child limit on Universal Credit: impact on low income poverty levels in the United Kingdom][gov-2cl], Tables 1 and 2 (financial year ending 2030).
- Issue: [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398). Related: [#1171](https://github.com/PolicyEngine/policyengine-uk/issues/1171), [#1388](https://github.com/PolicyEngine/policyengine-uk/issues/1388).

[obr-efo]: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
[budget-2025]: https://www.gov.uk/government/publications/budget-2025-document/budget-2025-html
[rf-nhm]: https://www.resolutionfoundation.org/publications/no-half-measures/
[gov-2cl]: https://www.gov.uk/government/publications/poverty-impacts-of-social-security-changes-at-budget-2025/removing-the-two-child-limit-on-universal-credit-impact-on-low-income-poverty-levels-in-the-united-kingdom

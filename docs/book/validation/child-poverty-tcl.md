# Child poverty validation: removing the two-child limit (2029-30)

This page compares PolicyEngine UK's estimate of the child-poverty
impact and fiscal cost of removing the [Universal Credit two-child
limit][gov-2cl] against the published estimates from the Office for
Budget Responsibility and the Resolution Foundation. The Autumn Budget
2025 announced the removal with effect from 6 April 2026 — see the
`gov.dwp.universal_credit.elements.child.limit.child_count` parameter
(`.inf` from `2026-04-06`).

Tracks [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398).

## Results

| Source | Children lifted from poverty (2029-30) | Treasury cost (2029-30) |
|--------|----------------------------------------:|------------------------:|
| [OBR EFO November 2025 (Table 3.2)][obr-efo] | 450,000 | £3.0 bn |
| [Resolution Foundation *No half measures*][rf-nhm] | 480,000 | £3.5 bn |
| **PolicyEngine UK, Microcosm UK 2024-25 (AHC)** | **~463,000** | **£3.26 bn** |
| **PolicyEngine UK, Microcosm UK 2024-25 (BHC)** | **~336,000** | (same) |
| PolicyEngine UK, Enhanced FRS 2022-23 (AHC), May 2026 | ~501,000 | £3.40 bn |
| PolicyEngine UK, Enhanced FRS 2022-23 (BHC), May 2026 | ~415,000 | (same) |

The October 2026 run uses the certified Microcosm UK 2024-25 national
release (SHA-256 `aa31bdf6…`) on policyengine-uk 2.123.7. On that
dataset, PolicyEngine's after-housing-costs headcount sits between the
OBR and Resolution Foundation figures, and its cost sits between theirs
too. The May 2026 Enhanced FRS run, kept for comparison, was above both
on headcount.

## How the estimate was produced

```python
from policyengine_uk import Microsimulation

# Path to the certified Microcosm UK 2024-25 national release
# (microcosm_uk_2024_25.h5 in policyengine/populace-uk-private).
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

1. **Nowcasting methodology**. RF and OBR use somewhat different
   earnings, rent, and benefit-uprating paths through 2029-30. See the
   [PolicyEngine vs RF comparison](../assumptions/nowcasting-comparison.md)
   and the [RF methodology detail](../assumptions/rf-nowcasting-methodology.md)
   for the specific divergence points.
2. **Take-up assumptions**. PolicyEngine assumes the same UC take-up rate
   at the household level for newly eligible (post-TCL-removal) cases as
   for currently eligible cases. RF's "No half measures" report uses a
   slightly lower marginal take-up for the new claimants, which would
   reduce headcount and cost.
3. **Data and calibration vintage**. RF/OBR estimates were finalised
   against November 2025 EFO assumptions; PolicyEngine's parameters tick
   over with each EFO release. The Microcosm release is built from FRS
   2024-25 rather than 2022-23, with take-up anchored on reported receipt.

## How to keep this validation alive

- Re-run the snippet on each new certified Microcosm UK release, and
  when the remaining `would_claim_*` conversions (#1621) land — both
  could move the AHC poverty rate by a non-trivial amount.
- After each new EFO release, update the per-year poverty headcounts and
  the fiscal cost table.

## References

- OBR, [Economic and Fiscal Outlook November 2025][obr-efo], Chapter 3 — published two-child limit removal costing.
- Resolution Foundation, [No half measures: ending the two-child limit][rf-nhm].
- gov.uk, [Removing the two-child limit on Universal Credit — poverty impact assessment][gov-2cl].
- Issue: [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398). Related: [#1171](https://github.com/PolicyEngine/policyengine-uk/issues/1171), [#1388](https://github.com/PolicyEngine/policyengine-uk/issues/1388).

[obr-efo]: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
[rf-nhm]: https://www.resolutionfoundation.org/publications/no-half-measures/
[gov-2cl]: https://www.gov.uk/government/publications/poverty-impacts-of-social-security-changes-at-budget-2025/removing-the-two-child-limit-on-universal-credit-impact-on-low-income-poverty-levels-in-the-united-kingdom

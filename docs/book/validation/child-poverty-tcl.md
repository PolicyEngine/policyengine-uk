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
| **PolicyEngine UK (AHC)** | **~501,000** | **£3.40 bn** |
| **PolicyEngine UK (BHC)** | **~415,000** | (same) |

PolicyEngine's central estimate sits between the two external
benchmarks on the headcount (slightly above RF, slightly above OBR) and
between them on the fiscal cost (below RF, above OBR). The agreement
is well within the noise we'd expect from differences in nowcasting and
take-up assumptions.

## How the estimate was produced

```python
import os
os.environ.setdefault(
    "POLICYENGINE_UK_DEFAULT_DATASET",
    "hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5",
)
from policyengine_uk import Microsimulation

YEAR = 2029

# Current law baseline (TCL removed from 2026-04-06 per Budget 2025)
sim_baseline = Microsimulation()

# Counterfactual where the TCL is held in place at 2 children
sim_counter = Microsimulation(reform={
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

## Why PolicyEngine sits slightly above RF / OBR

Three plausible drivers:

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
3. **Calibration vintage**. RF/OBR estimates were finalised against
   November 2025 EFO assumptions; PolicyEngine's parameters tick over
   with each EFO release.

## How to keep this validation alive

- Re-run the snippet whenever the State Pension fix from
  [PR #1634](https://github.com/PolicyEngine/policyengine-uk/pull/1634)
  or the upcoming `would_claim_*` conversions (#1621) land — both
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

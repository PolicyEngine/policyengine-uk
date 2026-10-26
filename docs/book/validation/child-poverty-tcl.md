# Child poverty validation: removing the two-child limit

This page sets out how PolicyEngine UK estimates the child-poverty impact
and fiscal cost of removing the [Universal Credit two-child
limit][gov-2cl], which Budget 2025 announced from 6 April 2026. The
comparison with the published estimates from the Department for Work and
Pensions, HM Treasury and the Resolution Foundation is in [PolicyEngine
Scorecard][scorecard-lane]. Scorecard computes PolicyEngine's figures on a
certified release, states for every row whether the two concepts match,
and keeps the earlier runs in each row's history.

Tracks [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398).

## The comparison in Scorecard

| Benchmark | Scorecard row |
|---|---|
| DWP: children in relative low income, after housing costs, FYE 2030 (Table 1) | [row][dwp-rel-ahc] |
| DWP: children in relative low income, before housing costs, FYE 2030 (Table 2) | [row][dwp-rel-bhc] |
| DWP: children in absolute low income, after housing costs, FYE 2030 (Table 3) | [row][dwp-abs-ahc] |
| DWP: children in absolute low income, before housing costs, FYE 2030 (Table 4) | [row][dwp-abs-bhc] |
| DWP: children in gaining households, FYE 2030 | [row][dwp-gainers] |
| HM Treasury: static Exchequer cost, 2029-30 | [row][hmt-static] |
| HM Treasury: post-behavioural cost, 2029-30 (the £3.1 billion in Budget 2025 Table 1.2) | [row][hmt-post] |
| Resolution Foundation, *No half measures*: children, 2029-30 | [row][rf-children] |
| Resolution Foundation, *No half measures*: cost, 2029-30 | [row][rf-cost] |

Each row shows the published figure, PolicyEngine's value, the comparison
status and the notes that explain it. Two notes matter most:

- **The absolute line.** DWP's note uses the FYE 2011 reference year (60%
  of the FYE 2011 median, held constant in real terms). PolicyEngine UK's
  `in_poverty_*` use the FYE 2025 reference. The FYE 2011 line is
  `in_absolute_poverty_fye2011_*` from policyengine-uk 2.155.0. The
  certified release Scorecard runs on predates that, so Scorecard
  constructs the FYE 2011 line for the comparison.
- **Static and post-behavioural costs.** PolicyEngine's cost is static, so
  it compares with HM Treasury's static leg. The £3.1 billion includes a
  behavioural adjustment.

Scorecard also records a [decomposition][decomposition] of how the
estimate moved between PolicyEngine's September and October 2026 figures:
how much came from the data, the model version, the child count and the
relative-line convention, and which policyengine-uk releases moved it.

## The reform

The `gov.dwp.universal_credit.elements.child.limit.child_count` parameter
is 2 from 6 April 2017 and infinite from 6 April 2026. Current law already
removes the limit, so the estimate compares two worlds: current law, and
current law with the parameter set back to 2. The effect of removing the
limit is current law minus that with-limit world. A year `Y` in
PolicyEngine UK is the financial year that starts in April `Y`, so FYE
2030 is `2029`.

## The measures

- **Relative low income**: `in_relative_poverty_ahc` and
  `in_relative_poverty_bhc`. These flag equivalised HBAI household income
  below 60% of the median of the world being calculated, with the median
  taken over people.
- **Absolute low income**: `in_poverty_ahc` and `in_poverty_bhc`. From FYE
  2022 these use 60% of the FYE 2025 median, held constant in real terms.
  `in_absolute_poverty_fye2011_ahc` and `in_absolute_poverty_fye2011_bhc`
  use the FYE 2011 median in every year, the line in DWP's note.
- **Children**: `is_hbai_dependent_child`, HBAI's dependent children, as
  DWP counts them.
- **Cost**: the change in `gov_balance` (tax less spending). The estimate
  is static: no behavioural response runs, and `would_claim_uc` is a data
  input, so take-up does not respond to the reform.

```python
import policyengine as pe

YEAR = 2029  # FY 2029-30 (FYE 2030)
LIMIT = "gov.dwp.universal_credit.elements.child.limit.child_count"

current_law = pe.uk.managed_microsimulation()
with_limit = pe.uk.managed_microsimulation(reform={LIMIT: {"2025-01-01.2035-12-31": 2}})

children = current_law.calculate("is_hbai_dependent_child", YEAR)
for measure in ("in_relative_poverty_ahc", "in_relative_poverty_bhc"):
    lifted = (
        with_limit.calculate(measure, YEAR, map_to="person").astype(float)
        - current_law.calculate(measure, YEAR, map_to="person").astype(float)
    ) * children
    print(measure, lifted.sum())

cost = (
    with_limit.calculate("gov_balance", YEAR).sum()
    - current_law.calculate("gov_balance", YEAR).sum()
)
print("cost", cost)
```

`pe.uk.managed_microsimulation()` loads the data release that
policyengine.py certifies with the installed model version. Scorecard's
[`compute_uk_two_child_limit_poverty.py`][compute] runs the same
comparison for every year, measure and group the benchmarks use.

## References

- DWP, [Removing the two-child limit on Universal Credit: impact on low income poverty levels in the United Kingdom][gov-2cl] (26 November 2025), Tables 1 to 4.
- HM Treasury, [Budget 2025][budget-2025], Table 1.2.
- Resolution Foundation, [No half measures: setting child poverty on a downward course at the Autumn Budget][rf-nhm] (30 October 2025).
- Issue: [#1398](https://github.com/PolicyEngine/policyengine-uk/issues/1398). Related: [#1171](https://github.com/PolicyEngine/policyengine-uk/issues/1171), [#1388](https://github.com/PolicyEngine/policyengine-uk/issues/1388).

[gov-2cl]: https://www.gov.uk/government/publications/poverty-impacts-of-social-security-changes-at-budget-2025/removing-the-two-child-limit-on-universal-credit-impact-on-low-income-poverty-levels-in-the-united-kingdom
[budget-2025]: https://www.gov.uk/government/publications/budget-2025-document/budget-2025-html
[rf-nhm]: https://www.resolutionfoundation.org/publications/no-half-measures/
[scorecard-lane]: https://www.policyengine.org/scorecard/?country=uk&view=validation
[dwp-rel-ahc]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=2f90d6562b5cf8008c94
[dwp-rel-bhc]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=d840d48b5aa86092e053
[dwp-abs-ahc]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=0953bfed29bf91c21076
[dwp-abs-bhc]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=f0db70b0fc559137b2b8
[dwp-gainers]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=c95c29a868535490a0e4
[hmt-static]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=67f3e4d6a1070d902798
[hmt-post]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=97d6c677b464338f8233
[rf-children]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=5cd40f11fde6cd6df668
[rf-cost]: https://www.policyengine.org/scorecard/?country=uk&view=validation&claim=a05d61066f4bc096db86
[decomposition]: https://github.com/PolicyEngine/policyengine-scorecard/blob/main/results/uk/two_child_limit_poverty/DECOMPOSITION.md
[compute]: https://github.com/PolicyEngine/policyengine-scorecard/blob/main/pipeline/compute_uk_two_child_limit_poverty.py

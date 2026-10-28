# Two-child limit: full roll-out and absolute child poverty

This page shows how to reproduce published estimates of reforming the
Universal Credit two-child limit that assume the limit is **fully rolled
out**, such as the IFS Green Budget 2025 comment [Options for reforming the
two-child limit][ifs-2025], and how PolicyEngine UK's results compare. For
how PolicyEngine UK estimates removing the limit in 2029-30, with links to
Scorecard's comparison against DWP, HM Treasury and Resolution Foundation
estimates, see
[Child poverty validation: removing the two-child limit](child-poverty-tcl.md).

## Settings that matter

**Year.** Budget 2025 removed the limit from 6 April 2026, and the baseline
encodes that (`gov.dwp.universal_credit.elements.child.limit.child_count` is
`.inf` from `2026-04-06`). In 2026-27 and later, an "abolish the limit" reform
therefore changes nothing. Model 2025-26 (`YEAR = 2025`), or re-impose the
limit as a counterfactual.

**Roll-out.** Under current law a child born before 6 April 2017 is protected
from the limit, so in 2025-26 the limit applies only to part of the large
families it will eventually affect. Estimates "when fully rolled out" treat
every child as born after that date. In PolicyEngine UK, set the
`born_before` dates for Universal Credit and Child Tax Credit to a date before
any child's birth. The same date also preserves the higher Universal Credit
child element for a first child born before 6 April 2017, so full roll-out
removes that too. IFS full roll-out analysis likewise removes the Child Tax
Credit family premium, its legacy equivalent ([IFS, 2024][ifs-2024], Table 6.5).
Tax credits ended on 5 April 2025 (`gov.dwp.tax_credits.active` is false from
6 April 2025), so in 2025-26 Child Tax Credit is zero and only the Universal
Credit settings change the results.

**Take-up.** Universal Credit claiming (`claims_universal_credit`) comes from
`would_claim_uc` and, for a family moved off legacy benefits,
`would_claim_uc_at_legacy_closure`. Both are set in the data, and neither
responds to the reform. For full take-up, set `would_claim_uc` to true for
every benefit unit with `set_input` before calculating anything that depends
on it; every benefit unit then claims.

**Poverty measure.** The poverty flags are household variables. Count children
by mapping them to people and multiplying by `is_hbai_dependent_child`, the
HBAI definition of a child:

| Variable | Measure |
|---|---|
| `in_poverty_ahc` | Absolute low income on HBAI's current FYE 2025 line, after housing costs |
| `in_poverty_bhc` | The same, before housing costs |
| `in_poverty` | Same as `in_poverty_bhc` (via the poverty gap) |
| `in_absolute_poverty_fye2011_ahc` | Absolute low income on the FYE 2011 line, after housing costs |
| `in_absolute_poverty_fye2011_bhc` | The same, before housing costs |
| `in_relative_poverty_ahc` | Relative low income (60% of the contemporary median), after housing costs |
| `in_relative_poverty_bhc` | Relative low income, before housing costs |

HBAI's absolute line is 60% of a reference year's median held constant in real
terms. Since March 2026 the reference year is FYE 2025, applied from FYE 2022,
and `in_poverty_ahc` and `_bhc` follow it. Estimates published before then,
including the IFS comment and DWP's Budget 2025 poverty impact notes, use 60% of
the FYE 2011 median. From policyengine-uk 2.155.0,
`in_absolute_poverty_fye2011_ahc` and `_bhc` compare equivalised income with
that line in every year (`poverty_threshold_fye2011_ahc` and `_bhc`, from the
parameters `household.poverty.absolute_poverty_threshold_fye2011_ahc` and
`_bhc`). The parameters hold HBAI's published values up to FYE 2025 and uprate
later years by headline OBR CPI, where HBAI uses its own CPI variants, so the
2025-26 line is close to HBAI's but not exact.

**Exceptions.** From policyengine-uk 2.161.0 the model applies the statutory
exceptions to the limit: multiple births, adoption, non-parental caring
arrangements, non-consensual conception and the continuation of an earlier
exception ([Universal Credit Regulations 2013, regulation 24A][reg24a] and
[Schedule 12][sch12]; [Child Tax Credit Regulations 2002, regulations 9 to
14][ctc-reg9]). Each is a person-level input that defaults to false:
`child_limit_multiple_birth_exception`, `child_limit_adoption_exception`,
`child_limit_non_parental_caring_exception`,
`child_limit_non_consensual_conception_exception` and
`child_limit_continuation_exception`. In Universal Credit, a third or later
child with the multiple births, non-consensual conception or continuation
exception gets the child element (`uc_child_limit_exception`). An adopted child
or one in non-parental care gets it whatever their place, and is left out of
the order of children that the limit counts (`uc_child_limit_disregarded`).
Child Tax Credit has its own equivalents (`is_CTC_child_limit_exception`).

The Microcosm release does not supply these inputs. The FRS does not record the
exceptions, so Microcosm leaves all five at their default
([`policyengine_uk_concepts.py`][microcosm-defaults]), and no child in the run
below has one. A child who would have an exception is then subject to the
limit in the baseline, so for those families the run overstates the loss from
the limit and the gain from removing it. DWP counted 26,300 households with an
exception in April 2025, out of about 470,000 affected ([UC two-child limit
statistics, April 2025][dwp-2cl]).

## Code

```python
import numpy as np
from policyengine_uk import Microsimulation

# Local path to the Microcosm UK 2024-25 national release file.
DATASET = "microcosm_uk_2024_25.h5"
YEAR = 2025  # fiscal year 2025-26, the last year the baseline has the limit
WINDOW = f"{YEAR}-01-01.{YEAR}-12-31"
UC = "gov.dwp.universal_credit.elements.child.limit"
CTC = "gov.dwp.tax_credits.child_tax_credit.limit"

# Full roll-out: no child keeps the pre-6 April 2017 protection. This also
# removes the higher first-child element, which the same date preserves.
FULL_ROLLOUT = {f"{p}.born_before": {WINDOW: 10000101} for p in (UC, CTC)}

# Absolute low income after and before housing costs, on HBAI's current
# FYE 2025 line and on the FYE 2011 line used before March 2026.
LINES = {
    "FYE 2025 line": ["in_poverty_ahc", "in_poverty_bhc"],
    "FYE 2011 line": [
        "in_absolute_poverty_fye2011_ahc",
        "in_absolute_poverty_fye2011_bhc",
    ],
}


def child_limit(n):
    return {f"{p}.child_count": {WINDOW: n} for p in (UC, CTC)}


def run(reform, full_take_up=False):
    sim = Microsimulation(dataset=DATASET, reform=reform or None)
    if full_take_up:
        n = len(sim.calculate("benunit_weight", YEAR))
        sim.set_input("would_claim_uc", YEAR, np.ones(n, dtype=bool))
    child = sim.calculate("is_hbai_dependent_child", YEAR)
    # Universal Credit and Child Tax Credit for each benefit unit, and the
    # same amounts against each of its members.
    benefits, per_person = (
        sim.calculate("universal_credit", YEAR, map_to=entity)
        + sim.calculate("child_tax_credit", YEAR, map_to=entity)
        for entity in (None, "person")
    )
    poor = {
        m: (sim.calculate(m, YEAR, map_to="person") * child).sum()
        for measures in LINES.values()
        for m in measures
    }
    return benefits, per_person, child, poor


def compare(setting, full_take_up=False):
    base, base_per_person, child, base_poor = run(setting, full_take_up)
    for name, n in [("abolish", np.inf), ("three-child limit", 3)]:
        reformed, per_person, _, poor = run({**setting, **child_limit(n)}, full_take_up)
        cost = (reformed.sum() - base.sum()) / 1e9
        # Benefit units gaining more than £1 a year, and their children.
        units = (reformed > base + 1).sum() / 1e3
        children = ((per_person > base_per_person + 1) * child).sum() / 1e6
        print(
            f"{name}: cost £{cost:.2f}bn; {units:.0f}k benefit units gain, "
            f"with {children:.2f}m children"
        )
        for line, (ahc, bhc) in LINES.items():
            lifted = [(base_poor[m] - poor[m]) / 1e3 for m in (ahc, bhc)]
            print(
                f"  children lifted (thousands), {line}: "
                f"AHC {lifted[0]:.0f}, BHC {lifted[1]:.0f}"
            )


compare({})  # current law: pre-April 2017 children protected
compare(FULL_ROLLOUT)
compare(FULL_ROLLOUT, full_take_up=True)
```

Reform keys use the `YYYY-MM-DD.YYYY-MM-DD` form, which the dictionary and
`Reform.from_dict` routes read the same way.

## Results, 2025-26

These results come from running the snippet above on 28 October 2026 with
policyengine-uk 2.162.14 and the Microcosm UK 2024-25 national release
`microcosm-uk-2024-25-national-20261028T061416Z-3c0d11b6` (SHA-256
`a5ae72ae…`), which was built with that version. Only the `DATASET` path was
changed. The run is nine microsimulations: a baseline and two reforms for each
setting. policyengine.py 6.11.1 certifies policyengine-uk 2.151.0, which has
neither the exception rules nor the FYE 2011 line variables, so this pair is
not a certified one. Cost is the change in Universal Credit and Child Tax
Credit spending. A benefit unit gains if those two rise by more than £1 a year.

| Setting | Abolish: cost | Abolish: benefit units gaining (their children) | Three-child limit: cost | Three-child limit: benefit units gaining (their children) |
|---|---:|---:|---:|---:|
| Current law (protection for pre-April 2017 children) | £1.91bn | 459k (1.64m) | £1.15bn | 351k (1.13m) |
| Full roll-out | £3.07bn | 639k (2.21m) | £2.13bn | 632k (2.17m) |
| Full roll-out, full UC take-up | £3.56bn | 767k (2.62m) | £2.52bn | 757k (2.57m) |
| IFS, fully rolled out | about £3.6bn | over 800,000 households | about £2.6bn | — |

Children lifted out of absolute low income, in thousands, after / before
housing costs:

| Setting | Abolish: FYE 2025 line | Abolish: FYE 2011 line | Three-child limit: FYE 2025 line | Three-child limit: FYE 2011 line |
|---|---:|---:|---:|---:|
| Current law (protection for pre-April 2017 children) | 209 / 299 | 229 / 235 | 132 / 219 | 194 / 97 |
| Full roll-out | 392 / 417 | 287 / 339 | 267 / 313 | 186 / 178 |
| Full roll-out, full UC take-up | 450 / 496 | 366 / 361 | 294 / 399 | 240 / 184 |
| IFS, fully rolled out | | 630 (after housing costs) | | 420 (after housing costs) |

Under current law, 459,000 benefit units with 1.64 million children gain from
abolition in 2025-26. DWP's April 2025 statistics count 453,600 households not
receiving the child element for at least one child, with 1.61 million children.

Each children-lifted figure comes from between 59 and 196 household records,
out of 21,086 households with children in the release, and no household moves
into absolute low income in any comparison. The ten records that contribute
most make up between 29% and 69% of each figure, and one record contributes up
to 57,000 children, so two figures can differ by that much because of one
household.

## Why the results differ from the IFS's

- **Roll-out.** Under current law, abolition costs £1.91bn and lifts 229,000
  children on the IFS's line (FYE 2011, after housing costs), just over a
  third of its 630,000. Full roll-out raises the cost to £3.07bn and the
  benefit units gaining from 459,000 to 639,000. For abolition it raises
  children lifted on the FYE 2011 line after housing costs from 229,000 to
  287,000, less than on the FYE 2025 line (209,000 to 392,000). For the
  three-child limit it lowers them on the FYE 2011 line (194,000 to 186,000).
  Full roll-out also removes the higher first-child element, which neither
  reform restores, so a family that a reform lifts out of low income under
  current law may stay in it at full roll-out. On that line the largest single
  record contributes 57,000 children to each current-law figure, but at most
  17,000 to a full roll-out one.
- **Take-up.** With full roll-out and full take-up, the cost (£3.56bn to
  abolish, £2.52bn for a three-child limit) is close to the IFS's (about
  £3.6bn and £2.6bn), and 767,000 benefit units gain from abolition, against
  the IFS's "over 800,000 households".
- **The remaining gap.** On the IFS's line, children lifted are about 42% short
  of the IFS figures: 366,000 against 630,000 for abolition, and 240,000
  against 420,000 for a three-child limit. On the higher FYE 2025 line they are
  about 30% short (450,000 and 294,000). These checks do not isolate the cause.
  Plausible contributors, none of them ruled out:
  - *Family size in the data.* At FYE 2025 the Microcosm release has about 13%
    fewer children in families with three or more children than HBAI (4.04
    million against 4.64 million, HBAI table 4.5db), and about 20% fewer of
    those children in relative low income after housing costs (1.66 million
    against 2.07 million). See [PolicyEngine/microcosm#1371](https://github.com/PolicyEngine/microcosm/issues/1371).
    A shortfall in relative low income does not show how many children cross
    an absolute line after the reform, so this alone cannot size the gap.
  - *The poverty line.* The model uprates the FYE 2011 line beyond FYE 2025 by
    headline OBR CPI (see above), which may not match the IFS's uprating.
  - *Take-up.* Full take-up here sets `would_claim_uc` to true for everyone,
    which is not the IFS adjustment to reported take-up ([IFS, 2024][ifs-2024],
    Appendix 6B), and this page has not matched that adjustment.
  - *Sample size.* The two full take-up figures on the IFS's line come from 185
    and 137 household records, and the ten that contribute most make up 29% and
    38% of them.

  The exceptions do not explain the gap: no child in the release has one, which
  if anything raises the figures here.
  Attributing the gap to any one of these would need a controlled comparison.
- **Data year and method.** The IFS used TAXBEN on FRS 2022-23 and 2023-24,
  additionally reweighting 2022-23 by number of children, and FRS data as
  published before HBAI's March 2026 administrative-data linking. PolicyEngine
  uses FRS 2024-25 and its own calibration.

## References

- IFS, [Options for reforming the two-child limit][ifs-2025], Green Budget 2025 comment, 23 October 2025 (endnotes 3 to 5 and 8 for the line, data and roll-out).
- IFS, [Child poverty: trends and policy options][ifs-2024], 3 October 2024, Table 6.5 and Appendix 6B (take-up).
- DWP, [Universal Credit claimants: statistics on the two-child limit policy, April 2025][dwp-2cl].
- DWP, [Households Below Average Income FYE 2025, background information and methodology][hbai-meth], section 2.3 (absolute reference year).
- [Universal Credit Regulations 2013, regulation 24A][reg24a] and [Schedule 12][sch12].
- [Child Tax Credit Regulations 2002, regulations 9 to 14][ctc-reg9].

[ifs-2025]: https://ifs.org.uk/articles/options-reforming-two-child-limit
[ifs-2024]: https://ifs.org.uk/publications/child-poverty-trends-and-policy-options
[dwp-2cl]: https://www.gov.uk/government/statistics/universal-credit-claimants-statistics-on-the-two-child-limit-policy-april-2025/universal-credit-claimants-statistics-on-the-two-child-limit-policy-april-2025
[hbai-meth]: https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#update-to-the-absolute-low-income-reference-year
[reg24a]: https://www.legislation.gov.uk/uksi/2013/376/regulation/24A/2025-04-06
[sch12]: https://www.legislation.gov.uk/uksi/2013/376/schedule/12/2025-04-06
[ctc-reg9]: https://www.legislation.gov.uk/uksi/2002/2007/regulation/9/2025-04-06
[microcosm-defaults]: https://github.com/PolicyEngine/microcosm/blob/daaf543023b8d3d327798c94a4028bd917a7bd73/packages/microcosm-frame/src/microcosm/frame/adapters/policyengine_uk_concepts.py#L232-L243

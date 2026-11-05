# Working Tax Credit and Child Tax Credit

```{note}
Working Tax Credit (WTC) and Child Tax Credit (CTC) are **legacy benefits**.
They closed to new claims at various points from 2018 onwards and the
scheme stopped paying ongoing awards on **5 April 2025**. PolicyEngine
gates the entire tax credits computation behind
`gov.dwp.tax_credits.active`, which flips to `false` from 2025-04-06. This
page describes how WTC and CTC were modelled while the scheme was live.
```

WTC and CTC were jointly administered by HMRC (and historically DWP-routed
on legacy migrations). PolicyEngine UK groups them under
`gov.dwp.tax_credits` because the means-test logic is shared. The
combined household award is the variable `tax_credits`, which sums the
two with a minimum-payment floor:

```python
amount = wtc_pre_minimum + ctc_pre_minimum
tax_credits = where(amount < min_benefit, 0, amount)
```

Parameters live in `policyengine_uk/parameters/gov/dwp/tax_credits/` and
the formulas in `policyengine_uk/variables/gov/dwp/`.

## Working Tax Credit (WTC)

WTC was paid to working-age adults whose hours and income met the
eligibility test. PolicyEngine computes it via `wtc_entitlement`, which
is the **maximum WTC amount** minus the shared `tax_credits_reduction`
from the means test, gated by the `would_claim_WTC` take-up input.

### Elements (`gov.dwp.tax_credits.working_tax_credit.elements`)

| Element | Parameter | Notes |
|---------|-----------|-------|
| Basic | `basic.yaml` | Flat amount everyone meeting the hours test gets |
| Couple | `couple.yaml` | Couple addition |
| Lone parent | `lone_parent.yaml` | Lone-parent addition |
| 30-hour | `worker.yaml` | Awarded when total hours hit the higher band |
| Disabled worker | `disabled.yaml` | |
| Severely disabled worker | `severely_disabled.yaml` | |
| Childcare cap | `childcare_1.yaml`, `childcare_2.yaml`, `childcare_coverage.yaml` | 70% of approved childcare costs up to the weekly cap (one or two-plus children) |

### Hours test

The `min_hours` tree (`min_hours/default.yaml`, `lower.yaml`,
`old_age.yaml`, `couple_with_children.yaml`) encodes the bands that gate
WTC eligibility — typically 30 hours/week for adults with no kids, 16 for
lone parents, with a lower band for workers aged 60 or over.

For the joint-claim rules from 6 April 2012, an individual's own age or
disability must qualify that individual's hours. Two childless workers cannot
pool 15 hours each to meet the ordinary 30-hour route, and a nonworking
partner cannot lend their age or disability to the worker. Parents can combine
24 hours, with at least one claimant working 16 hours. Hours worked by a
child or other dependant do not count towards that total. The `min_age` and
`min_age_without_children_or_disability` parameters provide the 16-year and
25-year thresholds; the existing `min_hours.old_age` parameter provides 60.
Native annual formula selection retains the earlier formula for a year whose
start precedes 6 April 2012; this change does not certify all earlier rules.

`is_disabled_for_benefits` remains a generic proxy for the statutory disabled
worker conditions. For parents, the model also retains its existing proxy
for an exception based on the other partner's disability. These flags do not
encode all regulation 9 or regulation 13 tests, incapacity, hospital or prison
status, carer's allowances, or the expected four-week and paid-work conditions.
The reported-award, migration, take-up and scheme-closure rules remain separate.

## Child Tax Credit (CTC)

CTC supported families with children regardless of whether anyone in the
benunit worked. PolicyEngine computes it via `ctc_entitlement`, gated by
`would_claim_CTC`.

### Elements (`gov.dwp.tax_credits.child_tax_credit.elements`)

| Element | Parameter |
|---------|-----------|
| Family | `family_element.yaml` (one amount, subject to the birth-date condition below) |
| Per qualifying child | `child_element.yaml` |
| Disabled child addition | `dis_child_element.yaml` |
| Severely disabled child addition | `severe_dis_child_element.yaml` |

### Family element birth-date condition

From 6 April 2017, the family element is included only if a claimant or
joint claimant is responsible for a qualifying child or qualifying young
person born **strictly before 6 April 2017**. A child born on that date
does not qualify. One qualifying child is enough for the single family
amount; an older adult or an excluded child cannot unlock it. The model
uses its existing CTC child/QYP responsibility mask, including its existing
looked-after-child and own-right-benefit approximations.

`CTC_family_element` applies this condition separately from the individual
child element's two-child limit. Its activation and cutoff parameters live
under `child_tax_credit/eligibility/`; reforming them does not change the
individual-element cutoff. The existing flat £545 amount is unchanged.
Before the condition applies, supported model years retain the prior flat
family amount. The false activation value at 2015-01-01 anchors model
coverage, rather than statutory commencement. Annual parameters use the
existing April sampling convention; this is not a part-year award model.

The rule reuses `birth_day`: a supplied valid `date_of_birth` must agree
with legal age on 6 October. A missing or zero date uses the existing
annual age and months-since-birthday fallback; `birth_year` is not a
replacement. Those conventions are not exact birth-date observations.
Explicit family-element and final-amount inputs retain the ordinary model
override contract and are not evidence of legal entitlement. Continuing
claims, income tests, minimum awards, other elements and 2025 closure are
unchanged; this update does not audit daily statutory award rounding.

Historical coverage remains incomplete: this change addresses the
supported 2015+ birth-date rule only. The pre-2011 baby addition and
2003–2014 coverage remain follow-up work under issue #2050; no raw
historical values or annual-conversion rules were extended.

### Two-child limit

Since April 2017 the child element has been restricted to the first two
qualifying children. The `child_count` parameter under
`child_tax_credit/limit/` encodes this, and `born_before` (6 April 2017,
Tax Credits Act 2002 s.9(3A)) sets which children it applies to: those
born before it are exempt, compared on `date_of_birth`. A few specific
exceptions (non-consensual conception, multiple births, kinship care)
also apply in law but are not modelled; `gov/contrib/two_child_limit/`
holds reform options such as an age-based exemption.

### Qualifying child tests

A child counts towards CTC if they are under 16, or under 20 and in
approved education or training and meet the qualifying-young-person
conditions. These tests are exposed as a family of `*_for_child_tax_credit`
variables (`is_child_for_child_tax_credit`,
`meets_qualifying_young_person_*_for_child_tax_credit`).

## Shared means test

WTC and CTC share a single income test in
`gov.dwp.tax_credits.means_test`:

```python
threshold = ctc_only ? income_threshold_CTC_only : income_threshold
overage = max(0, tax_credits_applicable_income - threshold)
reduction = overage * income_reduction_rate
```

`tax_credits_applicable_income` is the benunit's total income net of
specific disregards (pension contributions, certain benefits). The
non-earned disregard for unearned income is the
`means_test/non_earned_disregard.yaml` parameter. Awards below
`min_benefit` (a £26-ish floor) are paid as zero.

## Scheme end

From `2025-04-06` onwards the `tax_credits` variable returns zero
unconditionally — the `active` parameter flips off and the formula
short-circuits with an empty array. The remaining caseload was migrated
to Universal Credit via the DWP/HMRC managed-migration programme
finalised on 5 April 2025.

The reported variables (`working_tax_credit_reported`,
`child_tax_credit_reported`) remain available for historical analysis,
and the take-up flags (`would_claim_WTC`, `would_claim_CTC`) continue to
be populated stochastically when the dataset is built so historical
years still match published caseload aggregates.

## References

- [Tax Credits Act 2002](https://www.legislation.gov.uk/ukpga/2002/21/contents) — primary statute.
- [The Working Tax Credit (Entitlement and Maximum Rate) Regulations 2002 (SI 2002/2005)](https://www.legislation.gov.uk/uksi/2002/2005/contents).
- [The Child Tax Credit Regulations 2002 (SI 2002/2007)](https://www.legislation.gov.uk/uksi/2002/2007/contents).
- HMRC, [Tax credits have ended](https://www.gov.uk/tax-credits-have-ended) — official end-of-scheme announcement.
- House of Commons Library, [Completing Universal Credit rollout (CBP-9984)](https://commonslibrary.parliament.uk/research-briefings/cbp-9984/) — managed-migration timeline.
- HMRC, [Child and Working Tax Credit statistics](https://www.gov.uk/government/collections/personal-tax-credits-statistics) — caseload and expenditure outturns used for calibration.

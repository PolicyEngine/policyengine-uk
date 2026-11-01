# Future-dating policy announcements

PolicyEngine UK supports modelling policy changes that have been
**announced but not yet implemented**, or that take effect at a known
future date. The mechanism is the same one that handles legislated rate
schedules: parameters in `policyengine_uk/parameters/` carry a list of
values keyed by effective date.

This was originally requested in [#636](https://github.com/PolicyEngine/policyengine-uk/issues/636)
in the context of the Truss "growth plan" announcements in autumn 2022.
Nothing new was needed: parameter values have been keyed by effective
date since the model began in 2020, and the parameter files already carry
many future-dated rows. This page documents the current usage pattern so
that future analyses don't need to reinvent it.

## How it works

Every parameter is a `values:` map from effective date to value. When
the tax-benefit system is built, `convert_to_fiscal_year_parameters`
(`policyengine_uk/utils/parameters.py`) turns each parameter under `gov`
into one value per model year from 2015 to 2040, where model year 2026 is
the fiscal year 6 April 2026 to 5 April 2027:

- by default, the value in force on 30 April of that year;
- for parameters with `fiscal_year_blend: true` in their metadata (fuel
  duty, for example), the day-weighted average over the fiscal year, so a
  change part-way through the year counts for the share of the year it
  applies;
- parameters with `preserve_calendar_dates: true` keep their statutory
  dates, and the code that reads them handles the dates itself (the
  alcohol and tobacco duty formulas, for example, split each fiscal year
  into dated segments with `policyengine_uk/utils/excise.py`).

Example from
[`gov/hmrc/income_tax/allowances/personal_allowance/amount.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/parameters/gov/hmrc/income_tax/allowances/personal_allowance/amount.yaml):

```yaml
values:
  ...
  2021-04-06:
    value: 12_570
    ...
  2027-04-06:
    value: 12_570
    ...
  2030-04-06:
    value: 12_570
    metadata:
      reference:
        - title: Finance Act 2021 s. 5 (2), as amended by Finance Act 2026 s. 10 (3)
          href: https://www.legislation.gov.uk/ukpga/2026/11/section/10
```

The 2030-04-06 row records a future-dated decision: the freeze to
2030-31, announced at the 2025 Budget and since enacted by Finance Act
2026 s. 10. The file has no uprating. From the tax year after its last
row, `policyengine_uk/parameters/gov/hmrc/create_threshold_indexation.py`
applies the Income Tax Act 2007 s. 57 CPI indexation year by year. So
model years 2021 to 2030 return £12,570, and indexation starts in 2031.

## Patterns for common cases

### Announced but reversed before taking effect

Some announcements are walked back before the effective date. The
basic-rate cut to 19%, which the Truss "growth plan" of 23 September 2022
brought forward to April 2023 and which was reversed on 17 October 2022,
is the canonical example. To represent this
honestly:

1. When the announcement is made, add the announced value at the
   announced effective date with a reference to the announcement (for
   the Truss case, 19% from 6 April 2023).
2. When it is reversed, remove that row, or replace its value with the
   value that actually applies from that date (20% from 6 April 2023),
   and cite the reversal announcement. A new row at the reversal date
   does not cancel the future row: parameter rows apply from their own
   dates, so a 20% row dated October 2022 is followed by the 19% row in
   April 2023, and fiscal-year conversion still gives 19% for 2023.
3. Keep the announcement history in the row's references and in version
   control rather than in a live value.

The baseline then follows what was finally enacted. PolicyEngine UK has
no "policy as announced on date X" switch, so to score an announcement as
it stood before a reversal, apply it as a reform (see "Dated changes" in
the [scenarios guide](../usage/scenarios.md) for how dated reforms are
annualised, and the [excise duties page](../../engineering/excise-duties.md)
for duties that keep their calendar dates).

### Phased-in or staggered changes

Phased rate changes are a common future-dating pattern. Each phase is a
row at its effective date with a separate `reference`. The Class 1
employee main rate (`gov.hmrc.national_insurance.class_1.employee_scale[1].rate`,
in `national_insurance/class_1/employee_scale.yaml`) is a good worked
example: 13.25% from April 2022 under the Health and Social Care Levy Act
2021 (a temporary 1.25 percentage point rise for 2022-23, ahead of a
separate levy due from April 2023), back to 12% for earnings paid from
6 November 2022 under the Health and Social Care Levy (Repeal) Act 2022,
then the cuts to 10% in January 2024 and 8% in April 2024. The rate has
no `fiscal_year_blend`, so each model year takes the 30 April rate:
13.25% for 2022, 12% for 2023 and 8% from 2024. The November 2022 and
January 2024 changes do not show in annual results
([#1807](https://github.com/PolicyEngine/policyengine-uk/issues/1807)).

### Announced abolitions

For an abolition announced ahead of its effective date (for example the
removal of the two-child limit, announced at the 2025 Budget and since
enacted by the Universal Credit (Removal of Two Child Limit) Act 2026, in
[`gov/dwp/universal_credit/elements/child/limit/child_count.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/parameters/gov/dwp/universal_credit/elements/child/limit/child_count.yaml)):

- The relevant parameter (`gov.dwp.universal_credit.elements.child.limit.child_count`)
  has its limiting value (2) up to the announced effective date
  (2026-04-06) and `.inf` from that date onwards.
- Model year 2025 (fiscal year 2025-26) returns 2, so the limit applies.
- From model year 2026 the value is `.inf`, so the limit no longer
  restricts the UC child element.

The same pattern applies in reverse to one-off or time-limited
payments. The means-tested Cost-of-Living Payment in
[`gov/treasury/cost_of_living_support/means_tested_households/amount.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/parameters/gov/treasury/cost_of_living_support/means_tested_households/amount.yaml)
is £650 from 2022, £900 from 2023 and goes back to zero from
2024-01-01.

## Best practices

1. **Cite the announcement in `metadata.reference`** at every
   future-dated row. Where possible, cite both the announcement and
   the legislation that enacts it once it is published. The 2022-04-06
   row of the Class 1 employee main rate
   (`national_insurance/class_1/employee_scale.yaml`), for example, cites
   both the Health and Social Care Levy Act 2021 and the Budget document.
2. **Don't extrapolate**. Each future-dated row should reflect a
   specific announcement. If a parameter would otherwise move with
   uprating, let the uprating handle it. Adding a "frozen forever" row is
   a policy assertion that needs its own reference.
3. **Check how the parameter is annualised.** A change dated part-way
   through a fiscal year only counts for part of the year if the
   parameter has `fiscal_year_blend: true`, or has
   `preserve_calendar_dates: true` and a formula that splits the year (as
   the alcohol and tobacco duties do); otherwise the model year takes the
   value in force on 30 April.

## What this isn't

This is not the same as **scenario analysis** or **policy reform**
parameters under `gov.contrib.*`. Those are reform-side toggles for
hypothetical changes the user wants to evaluate; future-dated parameter
rows under `gov.hmrc.*`, `gov.dwp.*` etc. are **baseline** policy
representing what is actually announced.

If a future change is uncertain or contested, model it under
`gov.contrib.*` until it's announced; once announced, move it into the
baseline tree with an effective-date row.

## References

- Issue [#636](https://github.com/PolicyEngine/policyengine-uk/issues/636): the original request, from the Truss growth plan period.
- PolicyEngine research: [Tax cuts in Prime Minister Truss's Growth Plan 2022](https://www.policyengine.org/uk/research/tax-cuts-in-prime-minister-trusss-growth-plan), a worked example of modelling an announcement before its reversal.
- [PolicyEngine Core](https://github.com/PolicyEngine/policyengine-core): the date-keyed parameter mechanism underneath.
- `convert_to_fiscal_year_parameters` in `policyengine_uk/utils/parameters.py`: how dated values become model-year values.

# Company-director National Insurance

## Supported 2022–23 employee schedule

For model year `2022`, the explicit Person/year input
`is_full_year_category_a_director` selects the employee primary Class 1
schedule for a person who was a director throughout the tax year, had one
employment and was in category A throughout. The input defaults to `False`;
the model does not infer it from salary, dividends or company ownership.
The input label names its supported 2022–23 period. In other model years,
even an explicit `True` leaves the ordinary calculation unchanged.

HMRC's [2022–23 employer guidance][rates] gives this annual director schedule:

| Annual NI earnings | Employee rate |
| --- | ---: |
| Up to £11,908 | 0% |
| Above £11,908 up to £50,270 | 12.73% |
| Above £50,270 | 2.73% |

For example, £30,000 of annual NI earnings produces £2,303.1116 before
monetary rounding: (£30,000 − £11,908) × 12.73%. The model retains its existing
floating-point representation; this is not a new payroll rounding rule.
The director route uses the existing `ni_class_1_income` earnings definition,
including its statutory-pay components, and the existing final `ni_liable`
age gate. Employer NI, income-tax and other NI formulas and rates remain
unchanged. Their outputs need not all be unchanged: the existing Class 4 annual
maximum uses primary Class 1 contributions, so it can change for a director
who also has trading profits. That is propagation through the existing cap,
not a new Class 4 rule or a certification of all mixed-income cases.

A policy-test input for this restricted case is:

```yaml
period: 2022
input:
  age: 40
  employment_income: 30000
  is_full_year_category_a_director: true
output:
  ni_class_1_employee: 2303.1116
```

The primary and additional component variables allocate their respective
annual liabilities equally over twelve model months. Adding the months
recovers the annual liability. These allocations are **not** statutory
interim payroll deductions, observed monthly cash, cumulative year-to-date
charges or a model of bonus timing. The annual earnings interface does not
represent when pay was received.

## Why this differs from the ordinary route

The ordinary employee route reads weekly thresholds and converts them to
monthly equivalents. Existing fiscal parameter processing samples 30 April:
model year `2022` therefore uses the ordinary employee rate and threshold
in force on 30 April 2022. That convention does not reproduce the distinct
annual director schedule above. Annual salary inputs alone do not make the
two routes equivalent for 2022–23.

The new director parameters store annual thresholds, with raw dates starting
6 April 2022. A separate implementation-coverage parameter is true only for
2022–23, mapping to model year `2022` under that same fiscal convention.
Its false value from 6 April 2023 limits this implementation; it does not
mean that director law ended then. No ordinary rate or threshold history is
changed. Broader fiscal-year representation remains separate work under
[#1807](https://github.com/PolicyEngine/policyengine-uk/issues/1807).

## Remaining limits

HMRC describes a [standard annual method and an alternative method][directors].
The alternative method uses pay-period calculations during the year and
reconciles to the annual amount at year end. This page and the model's new
route concern the supported full-year annual liability, not either method's
in-year payment sequence.

Appointment years, category changes, multiple employments, other years and
employer-side director NI remain outside this implementation. The separate
employer rate and threshold in HMRC's table are not employee inputs. An
explicit contribution output supplied by a user retains the existing input
override contract; the new fact does not validate that supplied amount.

This is a partial response to
[#721](https://github.com/PolicyEngine/policyengine-uk/issues/721), which
remains open. It introduces no director imputation, population estimate or
encoded policy-parity claim. Integration with the separate NI scale migration
in [PR #2490](https://github.com/PolicyEngine/policyengine-uk/pull/2490) requires
coordination of the two employee component files; tests on this branch alone
do not establish that combined-tree compatibility.

[rates]: https://www.gov.uk/guidance/rates-and-thresholds-for-employers-2022-to-2023
[directors]: https://www.gov.uk/employee-directors

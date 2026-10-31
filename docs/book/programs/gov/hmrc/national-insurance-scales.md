# National Insurance parameter scales

PolicyEngine UK stores three marginal National Insurance (NI) schedules as
parameter scales. Each schedule holds its contribution rates and the thresholds
at which they apply. The schedules retain their dated values and units.

All paths below start with `gov.hmrc.national_insurance.`. Bracket indices start
at zero. Bracket zero supplies the fixed zero-threshold, zero-rate sentinel.
Contribution reforms use brackets 1 and 2 below. Any nonzero, missing or null
threshold or rate in bracket zero is rejected with a targeted error naming the
canonical leaf. Validation covers its full dated history, including future
entries; an explicit update to zero leaves calculations unchanged.

| Scale | Contribution bands | Threshold period in the parameter files |
| --- | --- | --- |
| `class_1.employee_scale` | Primary rate in bracket 1; additional rate in bracket 2 | Week |
| `class_1.employer_scale` | Employer rate in bracket 1 | Week |
| `class_4.contribution_scale` | Main rate in bracket 1; additional rate in bracket 2 | Year |

The contribution formulas retain their period conversions. Changing the
parameter layout does not make a weekly threshold an annual amount. Class 2's
flat contribution amount and its eligibility thresholds remain scalar
parameters.

## Reform paths

Use the following canonical paths when specifying new rate or threshold reforms.
The old scalar paths remain live views of the corresponding scale components.
Updating either path changes the same dated parameter history.

| Existing scalar path | Canonical scale component |
| --- | --- |
| `class_1.rates.employee.main` | `class_1.employee_scale[1].rate` |
| `class_1.rates.employee.additional` | `class_1.employee_scale[2].rate` |
| `class_1.thresholds.primary_threshold` | `class_1.employee_scale[1].threshold` |
| `class_1.thresholds.upper_earnings_limit` | `class_1.employee_scale[2].threshold` |
| `class_1.rates.employer` | `class_1.employer_scale[1].rate` |
| `class_1.thresholds.secondary_threshold` | `class_1.employer_scale[1].threshold` |
| `class_4.rates.main` | `class_4.contribution_scale[1].rate` |
| `class_4.rates.additional` | `class_4.contribution_scale[2].rate` |
| `class_4.thresholds.lower_profits_limit` | `class_4.contribution_scale[1].threshold` |
| `class_4.thresholds.upper_profits_limit` | `class_4.contribution_scale[2].threshold` |

The bracket syntax above identifies a leaf in a reform path. Python callables
access a raw scale through its `brackets` list, for example
`parameters.gov.hmrc.national_insurance.class_1.employee_scale.brackets[1].rate`.
Existing scalar attribute chains and leaf updates remain supported. The model's
scalar views expose the old names, current dated values, descriptions and units.

Apply scalar changes through the rate or threshold leaf. The compatibility views
do not provide a second editable copy of the NI schedules. Replacing, deleting or
reparenting legacy subtrees requires an explicit structural migration using the
canonical scales; conflicting legacy replacements raise a migration error.

## Contribution outputs

The scales preserve the model's contribution components. Employee Class 1 NI
still adds `ni_class_1_employee_primary` and
`ni_class_1_employee_additional`. These outputs retain their separate input
overrides. Class 4 still calculates its main and additional contributions and
applies the existing annual-maximum rules. Employer NI retains its existing
pension-contribution switch.

The parameter migration preserves the existing calculation rules, liability
conditions and rounding.

## Maintaining the schedules

Edit the canonical scale components when changing the model. Their dated values,
references, units and uprating metadata supply the legacy scalar views. The NI
threshold generator writes to these canonical leaves. Parameter processing visits
each numerical history once; metadata discovery also exposes the legacy names.

Metadata retains both primitive IDs and their histories and units. Discovery
marks the ten legacy scalar views and the six fixed-zero leaves with
`household: false` and `economy: false`; the ten canonical contribution rate and
threshold leaves remain visible. Direct legacy lookup still resolves the same
canonical metadata and values, while enumeration supplies presentation-only
views. Hiding a fixed-zero control does not change its input-validation rule.

The pinned, source-extracted API contract tests cover these flags, all other
record fields and update routes. They do not verify a deployed API or the app's
tree, search and control presentation. Consumer owners must check those surfaces
before relying on the migration in a UI.

The separate full-year Category A director scale and factual-input gate for
2022–23 retain their constrained annual calculation and monthly allocation.
They are not replaced by the ordinary employee schedule. The savings starting
rate remains an annual limit, indexed alongside the five canonical NI threshold
writers without treating it as a weekly amount.

For NI rate reforms in behavioural scenarios, see
[Labour supply dynamics](../../../usage/dynamics.md).

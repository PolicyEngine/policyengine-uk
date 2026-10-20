# Negative FRS amounts

A negative entry in a raw Family Resources Survey (FRS) amount column does not
have one model-wide treatment. The data pipeline applies different operations
to named fields before they reach PolicyEngine UK. A value of `-1` therefore
cannot be assumed to become zero, to trigger imputation, or to retain its raw
value in every field.

This page describes public implementation code at
[`policyengine-uk-data` commit `a43e8c5`](https://github.com/PolicyEngine/policyengine-uk-data/tree/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f)
and the model-input boundary at
[`policyengine-uk` commit `e1601db`](https://github.com/PolicyEngine/policyengine-uk/tree/e1601dbe4feb15e71d0d59b7a57f9d860741c068).
These are code descriptions, not findings about the contents of a particular
FRS, Enhanced FRS or Microcosm release artifact.

## Raw fields and model inputs

The FRS loader reads tab-separated survey tables and coerces entries to numeric
values where possible. It fills missing entries with zero when combining the
adult and child tables. Numeric negative entries survive those steps; there is
no general replacement of every `-1` in every raw table. Later, field-specific
operations determine what is passed to the model.
[FRS loader, lines 876–912](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/datasets/frs.py#L876-L912)

A DataFrame supplied directly to PolicyEngine UK uses model variable names,
periods and entity identifiers. Its numeric model-input columns are read as
supplied values by the DataFrame converter; it does not interpret raw FRS
variable codes. Resolve a raw survey code before passing it as an amount such
as `maintenance_income`. The model's dataset loader is a different stage from
the upstream FRS transformation.
[Model-input conversion, lines 376–409](https://github.com/PolicyEngine/policyengine-uk/blob/e1601dbe4feb15e71d0d59b7a57f9d860741c068/policyengine_uk/data/input_dataframe.py#L376-L409)

## Tax and benefit amount fields

The following examples describe the named import steps, not all subsequent
calculations of tax or benefit entitlement.

| Raw fields and imported value | Existing treatment |
| --- | --- |
| Household `ctannual` → `council_tax` | A negative or missing annual bill selects an imputed mean for the household's region, Council Tax band and single-person status, with the loader's existing fallback. A reported zero remains zero. The existing Scottish water adjustment is applied when constructing tax-only bills. |
| Household `ctrebamt` → `council_tax_benefit_reported` | The amount is assigned to the household reference person, missing values are filled with zero, the weekly amount is annualised, and the result is floored at zero. |
| Benefits-table `benamt` → reported benefit amounts, including `child_tax_credit_reported` and `working_tax_credit_reported` | Matching benefit codes are selected, amounts are summed for each person, and weekly amounts are annualised. This import step does not floor negative amounts or replace them with an imputed entitlement. A hypothetical matching `-1` participates in that sum. This does not establish the value of the final calculated award. |

Sources: [Council Tax import, lines 1207–1243](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/datasets/frs.py#L1207-L1243),
[Council Tax Benefit import, lines 1491–1501](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/datasets/frs.py#L1491-L1501),
[reported benefits and tax credits, lines 1391–1420](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/datasets/frs.py#L1391-L1420),
and [person-level aggregation helper](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/utils/datasets.py#L13-L25).

## The original income-field examples

The discussion behind [issue #596](https://github.com/PolicyEngine/policyengine-uk/issues/596)
started with negative private-transfer and maintenance income in the older
OpenFisca UK data pipeline. The January 2022
[discussion](https://github.com/PolicyEngine/openfisca-uk-data/issues/71#issuecomment-1016616474)
asked whether `-1` meant missing. It did not establish a universal FRS value
label. [PR #72](https://github.com/PolicyEngine/openfisca-uk-data/pull/72)
merged targeted handling for maintenance, miscellaneous and private-transfer
income in that now-archived repository.

The named operations in the pinned current data code are:

| Imported amount | Existing treatment before annualisation |
| --- | --- |
| `maintenance_income` | The selected maintenance components are floored individually at zero, then added. |
| `miscellaneous_income` | The named miscellaneous fields are summed across the person's row, then that sum is floored at zero. Odd-job income is added separately. |
| `private_transfer_income` | The named private-transfer fields are summed across the person's row, then that sum is floored at zero. |

Despite its name, `sum_from_positive_fields` floors the **row sum**, rather
than each field. For two fields containing `-1` and `10`, it contributes `9`
before annualisation. `sum_positive_variables`, used for maintenance, floors
each component before adding them. These operations do not retain a separate
flag indicating that a negative raw amount contributed to an imported zero.
[Current income imports, lines 1344–1384](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/datasets/frs.py#L1344-L1384),
[sum helpers, lines 40–65](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/utils/datasets.py#L40-L65)

The archived pipeline multiplied these income amounts by `52`. The pinned
current pipeline uses `WEEKS_IN_YEAR = 365.25 / 7` for these amounts. An old
pipeline result should therefore not be treated as an exact current amount.
[Archived implementation](https://github.com/PolicyEngine/openfisca-uk-data/blob/d27d7540e504aec4ec17f5c39991019db33bcaed/openfisca_uk_data/datasets/frs/frs.py),
[current conversion factor](https://github.com/PolicyEngine/policyengine-uk-data/blob/a43e8c5196c7e7c09b6ecb4924f034444dd83b8f/policyengine_uk_data/datasets/frs.py#L46-L50)

## Interpreting a negative code

Use the questionnaire or data dictionary for the particular variable and survey
release to establish what its negative codes mean. The code examples above do
not establish that every negative tax, benefit or income amount means missing.
They also do not justify replacing negative values across all model variables:
other variables can represent genuine losses or use their own input conventions.

Once an import has replaced an amount with zero, that amount alone cannot
distinguish the replacement from a reported zero. Issue #596 also raised an
optional future investigation into using different imputation probabilities for
missing amounts and reported zeros. This documentation does not select or
implement that change. Such work would need variable-specific survey evidence
and a way to preserve the distinction through the data pipeline.

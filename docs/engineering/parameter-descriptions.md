# Parameter descriptions

Write descriptions that explain a parameter without requiring the reader to
infer its programme or purpose from its path. This follows the
[description review on PR 37](https://github.com/PolicyEngine/policyengine-uk/pull/37#pullrequestreview-536084082)
and the follow-up in [issue 39](https://github.com/PolicyEngine/policyengine-uk/issues/39).
Use the full programme name where needed to make that meaning clear. For example,
the capital limit in `gov/dwp/ESA/income/capital/limit.yaml` can be described as:

```yaml
description: Capital limit for income-related Employment and Support Allowance eligibility.
```

Keep descriptions accurate and self-contained. Explain qualifications or modelling
approximations when they affect the meaning. Additional sentences can carry those
qualifications; the checker does not count sentences or infer semantic correctness.
Use programme-specific terminology where it matters rather than mechanically
replacing every “allowance” with “disregard”. A reviewer must check that the prose
matches the parameter and its sources. An acronym search cannot establish that.

## Labels and descriptions

Use `metadata.label` as a concise, lowercase noun phrase that names the quantity.
Use `description` to explain the quantity's purpose without relying on the
parameter path. Include the programme name and relevant scope when the short
label leaves them unclear.

These wording examples illustrate the distinction without defining policy rules:

```yaml
metadata:
  label: capital limit
description: Capital limit used to assess eligibility for the example programme.
```

```yaml
metadata:
  label: earnings disregard
description: Amount of earnings excluded from the income assessment for the example programme.
```

Start an amount, rate or threshold description with the quantity and explain its
role. Use a complete sentence when it explains an action or condition more
clearly. End either form with a period. Avoid padding a repeated label with
"is" or extra words that add no meaning.

Keep the label stable when improving a description. Do not rename a parameter
or change its meaning to make the prose fit a template. Retain established
programme terminology, necessary qualifications and modelling approximations;
additional sentences can explain them. Review the meaning against the parameter
and its sources rather than enforcing one grammatical template across every
programme. Labels do not need a trailing period.

## Automated checks

`policyengine_uk/tests/test_parameter_descriptions.py` checks top-level metadata:

| YAML record | Description rule |
| --- | --- |
| Scalar with `values` | Required, nonempty string. |
| Scale with `brackets` | Required, nonempty string. |
| Structural/index/table container | Optional; if present, a nonempty string. |
| Every provided top-level description | Ends with a period after trimming whitespace. |

The scanner reports malformed YAML and incompatible root shapes with their file
paths. `values` must be a mapping and `brackets` a list; a record cannot contain
both. A container can have children without describing each child independently.
This check does not impose a description on every nested record or bracket
component, or validate the complete Core parameter schema.

The checker uses a private safe YAML loader that retains timestamp scalars as
text, including the existing year-`0000` keys. Other safe scalar types remain
typed: booleans, numbers, lists and nulls do not become valid description strings.
The global `yaml.SafeLoader` is unchanged. The check retains normal safe-loader
merge and duplicate-description-key behavior; it introduces no new duplicate-key
policy. This test-local reader does not change the model's date handling, source
YAML, parameter values or public API serializer.

Run the focused check from the repository root:

```bash
uv run pytest policyengine_uk/tests/test_parameter_descriptions.py -q
```

The existing Python CI shards collect this module. Its fixture tests cover the
previous silent omission of year-`0000` files as well as syntax, type, shape and
global-loader compatibility. The repository-wide check reads the current corpus;
invalid files must fail with a diagnostic rather than disappear from that scan.

## Remaining review work

This guide and checker address part of issue 39. They do not certify the semantic
quality of all existing descriptions, settle the
[allowance/disregard discussion](https://github.com/PolicyEngine/policyengine-uk/issues/39#issuecomment-748796235),
require descriptions on all nested tables, or implement fancy indexing. Keep
those follow-ups separate from mechanical validation and avoid bulk prose or
parameter-path rewrites as a side effect.

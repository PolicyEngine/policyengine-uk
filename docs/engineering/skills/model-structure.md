# UK Model Structure

Use this skill when adding or changing variables, parameters, reforms, enums,
program metadata, or model structure.

## Core Layout

- Parameters live under `policyengine_uk/parameters/`, usually organized by
  government department such as `gov/hmrc/`, `gov/dwp/`, or `gov/dfe/`.
- Variables live under `policyengine_uk/variables/`, following the same policy
  structure as parameters where practical.
- Policy YAML tests live under `policyengine_uk/tests/policy/`.
- Program coverage metadata lives in `policyengine_uk/programs.yaml`.

For government departments, use the correct department for the policy. For
devolved programs, use the appropriate devolved agency path, such as
`gov/social_security_scotland/`, `gov/revenue_scotland/`, `gov/senedd/`, or
`gov/welsh_revenue_authority/`.

## Variables And Parameters

- Match the variable file name to the class name, for example `pip_dl.py`
  defines `class pip_dl(Variable)`.
- Use vectorized formula helpers such as `where(...)`, `max_(...)`, and
  `min_(...)`; do not use Python scalar `if`, `max`, or `min` inside formulas.
- Use `np.ceil` and other NumPy functions where OpenFisca formulas need array
  behavior.
- Cite durable policy sources in `reference` fields when available.
- Parameter labels should be concise, lowercase, and stable.
- Add or update focused tests alongside variables and parameters.

## Program Registry

`policyengine_uk/programs.yaml` is the single source of truth for UK program
coverage metadata. It is served through the `/uk/metadata` API and consumed by
model coverage surfaces.

When adding a program, include:

- `id`
- `name`
- `full_name`
- `category`
- `agency`
- `status`
- `coverage`
- `variable`
- `parameter_prefix`

When extending year coverage, update `verified_years` only after verifying that
parameters and tests cover the new year. Status values include `complete`,
`partial`, and `in_progress`.

## Refactoring Recovery Lessons

During the 2025-05-31 variable refactor recovery, a script that split
multi-variable Python files into single-variable files dropped classes when one
class had the same name as the original file. Recovery was made harder when enum
values were recreated from assumptions instead of source history.

When recovering or refactoring model code:

1. Check original code with `git show <commit>:path/to/file`.
2. Verify enum values exactly, including spelling, capitalization, and labels.
3. Use `.possible_values` to access enum values rather than importing enum
   classes directly when formula context expects possible values.
4. Test incrementally after each fix.
5. Document recovery steps when they affect durable model behavior.

Known enum recovery pitfalls included `TenureType`, `AccommodationType`,
`EducationType`, `FamilyType`, `EmploymentStatus`, `MinimumWageCategory`,
`CouncilTaxBand`, and `StatePensionType`. Treat enum labels as compatibility
surface, not cosmetic text.

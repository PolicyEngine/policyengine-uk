# Contributing to policyengine-uk

See the [shared PolicyEngine contribution guide](https://github.com/PolicyEngine/.github/blob/main/CONTRIBUTING.md) for cross-repo conventions (towncrier changelog fragments, `uv run`, PR description format, anti-patterns). This file covers policyengine-uk specifics.

## Commands

```bash
make install           # install deps (uv)
make format            # format (required — CI enforces)
make test              # full test suite
uv run policyengine-core test policyengine_uk/tests/path/to/test.yaml -c policyengine_uk
uv run pytest policyengine_uk/tests/path/to/test_file.py::test_name -v
```

Python 3.11–3.14. Default branch: `main`.

## Writing variables and reforms

Four types of files usually change together:

| Type                  | Location                                                   |
| --------------------- | ---------------------------------------------------------- |
| YAML unit tests       | `policyengine_uk/tests/policy/...`                         |
| Parameter (`.yaml`)   | `policyengine_uk/parameters/gov/<agency>/...` (DWP, HMRC, DfE, …) |
| Variable (`.py`)      | `policyengine_uk/variables/gov/<agency>/...`               |
| Changelog fragment    | `changelog.d/<branch>.<type>.md`                           |

Conventions:

- Write YAML tests **first** (TDD). They fail until the variable formula is in place.
- Use `where(...)`, `max_(...)`, `min_(...)` inside formulas — never Python `if` / `max` / `min`. Vectorisation requires numpy.
- Match the variable file name to the class name (e.g. `pip_dl.py` defines `class pip_dl(Variable)`).
- For devolved programs, use the correct agency:
  - England default → `gov/dwp/` or `gov/hmrc/` or `gov/dfe/`
  - Scotland → `gov/social_security_scotland/` or `gov/revenue_scotland/`
  - Wales → `gov/senedd/` / `gov/welsh_revenue_authority/` as appropriate
- Cite UK legislation in the variable's `reference` field (gov.uk, legislation.gov.uk).

## Program registry

`policyengine_uk/programs.yaml` is the single source of truth for program coverage metadata and drives the `/uk/metadata` API. When adding a program, add an entry with `id`, `name`, `full_name`, `category`, `agency`, `status`, `coverage`, `variable`, `parameter_prefix`. When extending year coverage, bump `verified_years` after verifying parameters and tests cover the new year.

## Repo-specific anti-patterns

- **Don't change HF upload destinations** in the `policyengine-uk-data` upload pipeline without explicit authorisation — the private/public split exists to respect the UK Data Service licence.
- **Don't hardcode FRS-year logic** in variable formulas; defer to `policyengine-uk-data` for dataset semantics.

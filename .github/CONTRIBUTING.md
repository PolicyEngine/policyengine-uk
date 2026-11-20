# Contributing to policyengine-uk

See the [shared PolicyEngine contribution guide](https://github.com/PolicyEngine/.github/blob/main/CONTRIBUTING.md) for cross-repo conventions (towncrier changelog fragments, `uv run`, PR description format, anti-patterns). This file covers policyengine-uk specifics.

## Commands

```bash
make install           # install development dependencies with pip
make format            # format (required — CI enforces)
make test              # full test suite
uv run policyengine-core test policyengine_uk/tests/path/to/test.yaml -c policyengine_uk
uv run pytest policyengine_uk/tests/path/to/test_file.py::test_name -v
```

The package supports Python 3.11–3.14. Default branch: `main`.

## Dependencies

CI's test suite installs exactly what `uv.lock` pins (`uv sync --frozen`). If you change dependencies in `pyproject.toml`, run `uv lock` and commit `uv.lock` with the change; otherwise CI tests the dependencies in the old lock, not the ones you asked for.

Every Monday, `.github/workflows/weekly-uv-lock.yaml` runs `uv lock --upgrade` on `main` and opens a pull request with the result, or refreshes the one already open. That is how CI moves to new dependency releases. Merge it when its CI passes. If a new release breaks a test, push the fix to that pull request's branch; the workflow then stops refreshing it. To take one release sooner, run `uv lock --upgrade-package <name>` in your own pull request.

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

`policyengine_uk/programs.yaml` is the single source of truth for program
coverage metadata and drives the `/uk/metadata` API. Every entry includes `id`,
`name`, `full_name`, `category`, `agency`, `status`, `coverage`, and
`verified_start_year`. Add `variable` and `parameter_prefix` when applicable,
and add `verified_end_year` when verified coverage has a defined end. Change the
verified year fields only after confirming that parameters and tests cover the
stated years.

The registry also defines the budget totals. `household_tax` adds every entry
flagged `budget: tax` and `household_benefits` every entry flagged
`budget: benefit`, in the order the file's `budget_order` lists them.
`policyengine_uk.programs.budget_programs()` returns those terms with their
labels, `tax` or `benefit` and `group`; downstream code reads that function, or
`HOUSEHOLD_TAX_VARIABLES` and `HOUSEHOLD_BENEFIT_VARIABLES`, rather than its own
copy. Four fields set a term's place in the totals:

- `budget`: `tax` or `benefit` on each entry whose `variable` a total adds;
  leave it off the rest.
- `group`: an optional key shared by terms that move together, such as the
  childcare entitlements.
- `budget_dropped_when`: the path of a boolean parameter that removes the term
  from its total while true (`gov.contrib.abolish_council_tax` on council tax,
  the High Value Council Tax Surcharge and Council Tax Reduction).
- `budget_uprating`: which of `gov.contrib.benefit_uprating`'s `all` and
  `non_sp` rates scale a benefit term. A benefit term without it takes both.
  The State Pension takes `[all]` and basic income `[]`.

A total's term that no programme entry carries goes under `budget_terms`, with a
`kind`: `programme_measure` (the amount counted for the programme that `program`
names, such as `esa_income` for ESA), `programme` (a programme the coverage list
does not carry yet), `reform_measure` (not a programme: a hypothetical tax or
benefit, or a change from baseline such as `vat_change`, zero unless a reform
sets it) or `public_service` (public services in kind). These entries stay out
of `programs`, so the coverage page never lists them, and they carry no
verified-year fields. The package refuses to load when a budget field is
misspelt or the flags and `budget_order` disagree.

To add a term to a total:

1. Flag its entry with `budget`, or add a `budget_terms` entry for it.
2. Append its variable to the end of `budget_order`'s list for that total.
3. Add a head for it to `policyengine_uk/data/fiscal_partition.yaml` that lists
   the total in its `totals`: a `tax_heads` entry for a tax term, a
   `spending_heads` entry for a benefit term. If the term carries
   `budget_dropped_when`, add it under that parameter in the total's
   `dropped_when` there too.
4. For a benefit term, also add its variable to `GOV_SPENDING_VARIABLES` in
   `policyengine_uk/variables/gov/gov_spending.py`, or, if government does not
   pay it, to `NOT_PAID_BY_GOVERNMENT` in
   `policyengine_uk/tests/code_health/test_household_benefits_in_government_spending.py`
   with the reason.

## Axiom parity

Every policy change here must also be correct in [rulespec-uk](https://github.com/TheAxiomFoundation/rulespec-uk). That covers a new programme, a parameter or threshold update, an eligibility rule and a bug fix. The shared guide, [Mirror policy changes in Axiom](https://github.com/PolicyEngine/.github/blob/main/CONTRIBUTING.md#mirror-policy-changes-in-axiom), defines the `axiom:` line your PR description needs and what a `queued` issue must contain. UK specifics:

- National modules live under `uk/`, and council schemes such as council tax reduction live under `uk-<council>/`. Search `main` there before opening a new issue.
- An `encoded-correct` claim names the module and a companion case in its `.test.yaml` that exercises the same situation as your YAML test.
- Use `queued` only when the signed encoder is blocked; record the blocker in the issue. Each billed encoder run requires separate approval. Label `queued` issues `pe-parity`. Reuse your YAML test's externally sourced expected values (legislation.gov.uk, gov.uk guidance, official calculators) as the companion tests; don't copy values computed by policyengine-uk.

## Repo-specific anti-patterns

- **Don't change HF upload destinations** in the `policyengine-uk-data` upload pipeline without explicit authorisation — the private/public split exists to respect the UK Data Service licence.
- **Don't hardcode FRS-year logic** in variable formulas; defer to `policyengine-uk-data` for dataset semantics.

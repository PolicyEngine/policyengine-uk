# CTR Agent Handoff

Use this file to continue PR #1534 autonomously without needing thread context.

## Drop-in prompt

```text
Continue PolicyEngine UK PR #1534 from `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/agent_handoff.md`.

Follow `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/scheme_encoding_guidance.md`. Work autonomously on branch `codex/ctr-framework`: encode more remaining Council Tax Reduction schemes in source-linked batches, using TDD, source review, focused verification, commits, and pushes. Stop only at a clean pushed checkpoint or a real blocker.
```

## Current checkpoint

- PR: https://github.com/PolicyEngine/policyengine-uk/pull/1534
- Branch: `codex/ctr-framework`
- Pull the latest PR branch before continuing; this checkpoint includes Bath and North East Somerset, Rushmoor, Hart, Maldon, Hartlepool, Hertsmere, East Hampshire, Brentwood, West Berkshire, Tendring, St Helens, Tewkesbury, Forest of Dean, and Braintree.
- Coverage at this checkpoint: `103` current English working-age billing authorities, plus the national Wales and Scotland CTR schemes.
- Last focused local verification: `uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml -n "Braintree"` passed with `12` tests in this worktree.
- Last full local verification: `uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml` passed with `986` tests after Braintree review fixes.
- Recent completed schemes: South Gloucestershire, Gloucester, Bath and North East Somerset, Rushmoor, Hart, Maldon, Hartlepool, Hertsmere, East Hampshire, Brentwood, West Berkshire, Tendring, St Helens, Tewkesbury, Forest of Dean, Braintree.

Before continuing, pull the latest branch and inspect current status:

```bash
git fetch origin
git status --short
git log --oneline -5
gh pr checks 1534 --watch=false
```

If a push does not trigger new CI, check mergeability before assuming a workflow issue:

```bash
gh pr view 1534 --json mergeStateStatus,mergeable
```

## Autonomous workflow

For each council:

- Prefer official council scheme PDFs, council webpages, committee papers, or legislation.
- If a current-year report says the scheme is unchanged, pair that current report with the carried-forward full scheme and cite both.
- Do not implement an income-banded scheme from headline summaries alone; if thresholds are missing, mark it source incomplete in `scheme_work_queue.md`.
- Add failing YAML tests first in `policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml`.
- For UC branches, add at least one positive UC-income regression with no source override: include a positive UC award, UC assessed earned or unearned income, and a different legacy CTR applicable income so the test proves the implementation is not using `would_claim_uc` or the UC award alone.
- For pension-age carve-outs, assert both the jurisdiction variable and `simulated_council_tax_reduction_benunit` so local-rule cases do not double-count the national pensioner scheme. Include a mixed-age couple test where the scheme keys off the applicant or partner rather than a household-wide pensioner flag.
- Keep implementation jurisdiction-scoped:
  - Parameters: `policyengine_uk/parameters/gov/local_authorities/<authority>/council_tax_reduction/`
  - Variables: `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`
- Register the scheme in:
  - `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/config.py`
  - `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/simulated_council_tax_reduction_benunit.py`
  - `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/README.md`
  - `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/scheme_work_queue.md`
  - `changelog.d/council-tax-reduction.added.md`
- Run a source-fidelity review pass after implementation. Fix findings before pushing.
- Commit and push each completed council or small batch.

## Review traps

Check these every time:

- Actual UC award versus `would_claim_uc`.
- UC assessed income and capital where the source references DWP or UC calculations. Do not use the UC award alone unless the source explicitly says the award is the income base.
- Pre-deduction or pre-benefit-cap UC award where source requires it.
- UC earnings before allowances/work allowances versus `uc_earned_income` after allowances. If the source says before allowances, use or create a source input/proxy and test a work-allowance case.
- Capital boundary wording: `more than`, `at least`, `exceeds`, `does not exceed`, and exact threshold tests.
- Tariff income rounding: complete blocks versus complete-or-partial blocks.
- Minimum award cutoffs.
- Band caps and protected exceptions.
- Protected-group "who counts" scope. If the source says applicant, partner, or dependant, add a regression proving a disabled non-dependant does not uplift the claimant.
- Protected-group acronym mismatches, especially Armed Forces Independence Payment versus Armed Forces Compensation Scheme. Add a named-benefit regression when the variables are easy to confuse.
- Income-banded countable-income coverage. Add at least one source-countable non-earnings income regression, such as tax credits or contributory benefits, so the implementation is not accidentally earnings-only.
- Non-dependant deduction ordering, gross versus earned income, remunerative-work hours, and one-deduction couple rules.
- Do not add a 16-hour/remunerative-work gate to non-dependant earnings tables unless the non-dependant section itself says so. Some schemes define remunerative work for childcare only while applying non-dependant gross-income bands at any hours.
- Pension-age UC or income-based benefit local-rule carve-outs, including tests that avoid double-counting national pensioner CTR.
- Applicant/partner pension-age wording versus household-wide pensioner flags. A working-age applicant with a pension-age partner can still be in the local scheme even though `council_tax_reduction_household_has_pensioner` is true.
- Source conflicts between live pages, summaries, examples, and adopted scheme PDFs. Document conflicts in `scheme_work_queue.md`.

## Verification before push

Run these at minimum:

```bash
uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml -c policyengine_uk
uvx ruff format <new-or-edited-python-files>
uvx ruff format --check <new-or-edited-python-files>
uv run ruff check <new-or-edited-python-files> policyengine_uk/variables/gov/local_authorities/council_tax_reduction/config.py policyengine_uk/variables/gov/local_authorities/council_tax_reduction/simulated_council_tax_reduction_benunit.py
uv run python - <<'PY'
from policyengine_uk import CountryTaxBenefitSystem
system = CountryTaxBenefitSystem()
print("import smoke ok", len(system.variables))
PY
find policyengine_uk -type d -name __pycache__ -prune -exec rm -rf {} +
git diff --check
git status --short
```

After push:

```bash
gh pr checks 1534 --watch=false
```

## Next candidates

Use `scheme_work_queue.md` as the source of truth for remaining authorities and statuses.

## Source-incomplete note

Durham is currently marked source incomplete in `scheme_work_queue.md`: official sources confirm headline parameters but do not expose adopted income-band thresholds. Do not encode Durham until the current detailed threshold grid is available from a primary source.

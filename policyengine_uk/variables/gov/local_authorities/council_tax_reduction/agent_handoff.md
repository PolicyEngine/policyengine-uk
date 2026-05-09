# CTR Agent Handoff

Use this file to continue PR #1534 autonomously without needing thread context.

## Drop-in prompt

```text
Continue PolicyEngine UK PR #1534 from `policyengine_uk/variables/gov/local_authorities/council_tax_reduction/agent_handoff.md`.

Work autonomously on branch `codex/ctr-framework`: encode more remaining Council Tax Reduction schemes in source-linked batches, using TDD, source review, focused verification, commits, and pushes. Stop only at a clean pushed checkpoint or a real blocker.
```

## Current checkpoint

- PR: https://github.com/PolicyEngine/policyengine-uk/pull/1534
- Branch: `codex/ctr-framework`
- Last known pushed head before the Coventry batch: `4f4690621`; pull latest before continuing.
- Coverage at this checkpoint: `79` current English working-age billing authorities, plus the national Wales and Scotland CTR schemes.
- Last focused local verification: `uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml -n Coventry` passed with `14` tests.
- Last full local verification: `uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml -c policyengine_uk` passed with `672` tests.
- Recent completed schemes: Chelmsford, Cheshire West and Chester, Chichester, Coventry.

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

### Cotswold

- Enum exists: `LocalAuthority.COTSWOLD`
- Sources:
  - https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf
  - https://meetings.cotswold.gov.uk/ieIssueDetails.aspx?IId=6872&Opt=3
- Shape: income-banded working-age scheme with separate protected-group fallback.
- Headline rules from scout:
  - Non-protected max support `100%`, then bands by family type and combined net weekly income.
  - Single bands: `0-154.48` 100%, `154.49-204.48` 80%, `204.49-254.48` 60%, `254.49-304.48` 40%, `304.49-354.48` 20%, above top band zero.
  - Capital must not be above `GBP 10,000`, so `GBP 10,000` eligible and `GBP 10,000.01` excluded.
  - Band cap restricts F/G/H to Band E.
  - UC uses DWP income calculation before UC earnings disregard, adds UC award annualised to weekly, deducts UC housing element and listed disregards.
  - Non-dependants: `GBP 15.95/week` if in remunerative work, `GBP 5.20` otherwise, with lower working rates for gross income bands.
  - UC non-dependant with no earned income exempt.
- Suggested tests:
  - Single income `GBP 154.48/week`: `GBP 1,800`.
  - Single income `GBP 154.49/week`: `GBP 1,440`.
  - Single income `GBP 204.49/week`: `GBP 1,080`.
  - Single income `GBP 304.49/week`: `GBP 360`.
  - Single income `GBP 354.49/week`: `GBP 0`.
  - Capital `GBP 10,000` eligible; `GBP 10,000.01` excluded.
  - Band 1 with one non-working non-dependant: `GBP 1,528.71`.
- Trap: protected group is not banded; it uses liability less non-dependants less `20%` of excess over applicable amount.

## Source-incomplete note

Durham is currently marked source incomplete in `scheme_work_queue.md`: official sources confirm headline parameters but do not expose adopted income-band thresholds. Do not encode Durham until the current detailed threshold grid is available from a primary source.

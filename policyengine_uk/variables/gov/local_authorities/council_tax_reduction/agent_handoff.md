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
- Last known pushed head from this handoff: `cd65bac2e`
- Coverage at this checkpoint: `78` current English working-age billing authorities, plus the national Wales and Scotland CTR schemes.
- Last focused local verification: `uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml -c policyengine_uk` passed with `646` tests.
- Recent completed schemes: Thurrock, Chelmsford, Cheshire West and Chester.

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
- UC assessed income and capital where the source references DWP or UC calculations.
- Pre-deduction or pre-benefit-cap UC award where source requires it.
- Capital boundary wording: `more than`, `at least`, `exceeds`, `does not exceed`, and exact threshold tests.
- Tariff income rounding: complete blocks versus complete-or-partial blocks.
- Minimum award cutoffs.
- Band caps and protected exceptions.
- Non-dependant deduction ordering, gross versus earned income, remunerative-work hours, and one-deduction couple rules.
- Pension-age UC or income-based benefit local-rule carve-outs, including tests that avoid double-counting national pensioner CTR.
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

### Chichester

- Enum exists: `LocalAuthority.CHICHESTER`
- Sources:
  - https://chichester.moderngov.co.uk/documents/s30862/09.0%20Local%20Council%20Tax%20Reduction%20Scheme%202026-27.pdf
  - https://chichester.moderngov.co.uk/documents/s30863/09.1%20Appendix%201%20Local%20Council%20Tax%20Reduction%20Scheme%20Rules%202026%20-%202027.pdf
- Shape: hybrid legacy means test plus UC income bands.
- Headline rules from scout:
  - Max support `100%`.
  - Non-UC Class D full support if income is below applicable amount, passported, or maximum UC.
  - Non-UC Class E taper is `20%` of excess income.
  - Capital above `GBP 16,000` excludes, so `GBP 16,000` eligible and `GBP 16,000.01` excluded.
  - No Band cap found.
  - UC Class F bands by household type, using DWP UC income.
  - Class F flat `GBP 3.90` weekly deduction for each 18+ non-dependant in remunerative work.
- Suggested tests:
  - No-income non-UC claimant on Band D `GBP 1,800`: `GBP 1,800`.
  - Non-UC excess income `GBP 10/week`: `GBP 1,695.71`.
  - UC single income `GBP 124.00/week`: `GBP 1,800`; `GBP 124.01/week`: `GBP 1,440`.
  - UC single income `GBP 218.01/week`: `GBP 0`.
  - Capital `GBP 16,000` eligible; `GBP 16,000.01` excluded.
  - Class F full-support band with one working non-dependant: `GBP 1,596.43`.
- Trap: UC couple `60%` band appears typoed as `GBP 206.01-GBP 2229.00`; confirm against report or older scheme before encoding that cell.

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

### Coventry

- Enum exists: `LocalAuthority.COVENTRY`
- Sources:
  - https://www.coventry.gov.uk/downloads/download/2513/council-tax-support-scheme
  - https://www.coventry.gov.uk/downloads/file/46761/council-tax-support-scheme-2026-to-2027
- Shape: simple excess-income banded scheme.
- Headline rules from scout:
  - Max support is `80%` of liability.
  - Weekly excess-income bands: `0-14.99` 80%, `15-39.99` 65%, `40-69.99` 40%, `70-79.99` 20%, `80+` zero.
  - Capital above `GBP 16,000` excluded, so `GBP 16,000` eligible and `GBP 16,000.01` excluded.
  - No Band cap found.
  - UC cases use DWP UC income estimate plus UC award, with UC capital estimate for UC cases.
  - Non-dependants: `GBP 15.95/week` working, `GBP 5.20/week` non-working, gross-income reduced working rates, one deduction per couple, UC non-dependant with no earned income exempt.
  - Pension-age UC local-rule carve-out with relevant-period protection.
- Suggested tests:
  - Excess income `GBP 0/week`: `GBP 1,440`.
  - Excess income `GBP 15/week`: `GBP 1,170`.
  - Excess income `GBP 40/week`: `GBP 720`.
  - Excess income `GBP 70/week`: `GBP 360`.
  - Excess income `GBP 80/week`: `GBP 0`.
  - Capital `GBP 16,000` eligible; `GBP 16,000.01` excluded.
  - Band 1 with one non-working non-dependant: `GBP 1,168.71`.
- Trap: do not multiply the `80%` maximum by the `80%` band again; the band percentages are direct percentages of liability.

## Source-incomplete note

Durham is currently marked source incomplete in `scheme_work_queue.md`: official sources confirm headline parameters but do not expose adopted income-band thresholds. Do not encode Durham until the current detailed threshold grid is available from a primary source.

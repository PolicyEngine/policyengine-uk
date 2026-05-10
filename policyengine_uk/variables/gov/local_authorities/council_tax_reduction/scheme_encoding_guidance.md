# CTR Scheme Encoding Guidance

Use this file for durable Council Tax Reduction implementation rules. Keep `agent_handoff.md` focused on the current PR checkpoint and copy-paste prompts.

## Source Standard

- Prefer official council scheme PDFs, council webpages, committee papers, or legislation.
- If a current-year report says the scheme is unchanged, pair that current report with the carried-forward full scheme and cite both.
- Do not implement an income-banded scheme from headline summaries alone; if thresholds are missing, mark it source incomplete in `scheme_work_queue.md`.
- Before writing tests, extract a source-facts table covering authority, scheme year, URLs, paragraph/page refs, archetype, maximum support/bands, taper, capital boundary wording, band cap, income basis, earnings disregards, pension-contribution treatment, UC treatment, non-dependants, who counts, pension-age carve-outs, and limitations.

## TDD And Implementation

- Add failing YAML tests first in `policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml`.
- Cover no-income maximum award, capital boundary, non-dependant case if present, UC case if the source mentions UC, and one source-specific edge.
- If the source contains multiple current working-age branches, such as a separate UC class or protected-group maximum, implement and test those branches before marking the scheme implemented.
- For income-banded schemes, add at least one test for source earnings disregards or pension-contribution deductions when present, and one test that dependent children or non-dependants do not drive applicant/partner income bands unless the source says they do.
- For income-banded schemes, add one non-earnings-income regression using a source-countable benefit or tax credit where the source counts income other than earnings. This catches formulas that accidentally model earnings-only bands.
- For protected-group uplifts, add a "who counts" regression when the source says applicant/partner/dependants. A non-dependant's disability or benefit status must not uplift the claimant unless the source explicitly includes non-dependants.
- For protected-group uplifts, test any source-listed benefit names that have easy-to-confuse PolicyEngine variables, such as Armed Forces Independence Payment versus Armed Forces Compensation Scheme.
- For UC branches, add at least one positive UC-income regression with no source override: include a positive UC award, UC assessed earned or unearned income, and a different legacy CTR applicable income so the test proves the implementation is not using `would_claim_uc` or the UC award alone.
- If the source has UC maximum-amount, UC income, or UC capital paragraphs, add regressions that would fail under the generic legacy helper.
- For pension-age carve-outs, assert both the jurisdiction variable and `simulated_council_tax_reduction_benunit` so local-rule cases do not double-count the national pensioner scheme.
- Keep implementation jurisdiction-scoped under `policyengine_uk/parameters/gov/local_authorities/<authority>/council_tax_reduction/` and `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`.
- Use separate jurisdiction-specific variables even if formulas duplicate another council.
- Do not leave `uv.lock`, `__pycache__`, generated files, or unrelated edits in the diff.

## Review Traps

- Actual UC award versus `would_claim_uc`.
- UC assessed income and capital where the source references DWP or UC calculations.
- UC earnings before allowances/work allowances versus `uc_earned_income` after allowances.
- Capital boundary wording: `more than`, `at least`, `exceeds`, `does not exceed`, and exact threshold tests.
- Band caps and protected exceptions.
- Income-banded schemes: net earnings deductions, standard earnings disregards, half versus full pension-contribution deductions, and whether dependent-child or non-dependant income is excluded from applicant/partner income.
- Income-banded schemes: do not stop at earnings. If the source's income rules include benefits, tax credits, pensions, or other non-earnings income subject to disregards, encode and test at least one countable non-earnings income source.
- Protected-group schemes: scope disability/benefit tests to the people named in the source. Avoid household-wide aggregation when the source says applicant, partner, or dependant.
- Non-dependant deduction ordering, gross versus earned income, remunerative-work hours, and one-deduction couple rules.
- Do not add a 16-hour/remunerative-work gate to non-dependant earnings tables unless the non-dependant section itself says so.
- Pension-age UC or income-based benefit local-rule carve-outs, including tests that avoid double-counting national pensioner CTR.
- Default-style formal PDFs often define the council's local scheme in section 1.6/Class D/E as including pension-age applicants on UC or relevant income-based benefits. If present, create a jurisdiction-scoped `*_is_local_scheme` variable and exclude that flag from `england_pensioners`.
- Source conflicts between live pages, summaries, examples, and adopted scheme PDFs. Document conflicts in `scheme_work_queue.md`.

## Verification Before Push

```bash
uv run policyengine-core test policyengine_uk/tests/policy/baseline/gov/local_authorities/council_tax_reduction/council_tax_reduction.yaml
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

# Programme-specific income concepts

Draft PR: https://github.com/PolicyEngine/policyengine-uk/pull/2620
Issue: https://github.com/PolicyEngine/policyengine-uk/issues/2619
Branch: `split-program-income`
Final head including this report: recorded after commit in `.job/HANDOFF.md` and on the PR.
Validated implementation head: `7bdd785099b9e5bd6c47770a0d92b80e98d734b1` (validated model implementation; the final report/test commit does not change formulas).

Fetched `origin/main` at `c417f283a92a8618e85dfea270d5c29b4d25b82d`. #2066 was open at start; first commit `57d2f5f63413a42bccb6326f5b72ed77a0b13c0d` merged its requested head `76108fafe74d9ee8d73e8d7a871aa723f39bfb20`, retaining main's statutory paternity pay when resolving HB earnings conflicts. All commits are pushed; the PR remains draft and is neither merged nor enqueued.

## Consumers and legal definitions

The old raw base R was employment income, private pension income, tax-purpose social security income, self-employment income, property income, savings interest, other investment income, dividends and nonnegative miscellaneous income. It excluded SSP/SMP/SPP and deducted no employment expenses.

| Consumer | Old → new | Source |
|---|---|---|
| Exported `total_income` | R → `adds = ["total_income_charged_to_tax"]`: tax-chain components before general-income loss relief, restoring embedded carried-forward trading relief and deducting separately held net-pay pension relief | [ITA 2007 s.23 Step 1](https://www.legislation.gov.uk/ukpga/2007/3/section/23), [s.31](https://www.legislation.gov.uk/ukpga/2007/3/section/31), [s.989](https://www.legislation.gov.uk/ukpga/2007/3/section/989) |
| WFP legacy eligibility test and actual charge | Old eligibility read R; prerequisite charge used a separate tax total → both read retained `total_income`; actual charge remains individual and strictly above £35,000 | [ITEPA 2003 s.681I](https://www.legislation.gov.uk/ukpga/2003/1/section/681I) |
| HB non-dependant deduction | R − other investment income + positive spousal maintenance → `housing_benefit_non_dep_gross_income`, adding statutory pay, child maintenance, MA, IIDB, SDA and periodic war widow's pension, with specified disregards | [HB 2006 reg74](https://www.legislation.gov.uk/uksi/2006/213/regulation/74), [pension-age HB reg55](https://www.legislation.gov.uk/uksi/2006/214/regulation/55) |
| CTR non-dependant deduction | Same cross-programme expression → separate `council_tax_reduction_non_dep_gross_income`, with the currently representable gross sources and its own national references | [England Sch1 para8](https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8), [Scotland working age reg90](https://www.legislation.gov.uk/ssi/2021/249/regulation/90), [Scotland pension age reg48](https://www.legislation.gov.uk/ssi/2012/319/regulation/48), [Wales pension-age Sch1 para3](https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3), [Wales working-age Sch6 para5](https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5) |
| HB / shared CTR net earnings | Earnings numerator explicit but tax denominator inferred from R and `total_income.adds` → explicit earnings and positive raw-component denominator, algebraically preserving existing values and WFP-charge exclusion | [HB regs35–36](https://www.legislation.gov.uk/uksi/2006/213/regulation/35), regs37–38; [pension-age regs35–36](https://www.legislation.gov.uk/uksi/2006/214/regulation/35) |
| `post_tax_income` | Household R − Income Tax − NI → household `gross_taxable_inputs` − Income Tax − NI | Explicit household measure: base preserved, no statutory definition claimed |
| Individual and household UBI phase-outs | Rates/thresholds applied to R → same rules applied to `gross_taxable_inputs` | Reform design choice: base preserved |

The tax total delegates to the prerequisite's calculation; component-level limitations (netted miscellaneous income and deficiency relief deducted from dividends) remain documented. Statutory pay enters once through `employment_benefits`. Other investment income remains deliberately excluded from non-dependant bases pending #2007 and its remunerative-work test. Disability/compensation disregards are documented. Benefit-unit recipient attribution and the UC/HB benefit-cap cycle prevent safely adding computed benefit-unit awards; BSP/AFCS inputs mix capital and periodic payments. Signed trading/property inputs are retained, with cross-source loss treatment unresolved rather than presented as a legal entitlement to offset. Existing worker/leave gates and the national CTR HB-scale proxy are unchanged. No #2535 changes or unrelated Budget work.

## Compatibility audit

Read-only exact-word searches in sibling repositories found:

- `policyengine.py/src/policyengine/tax_benefit_models/uk/model.py:72` exports `total_income`; `tests/test_models.py:261–269` requires nonempty `adds` (preserved). Four UK household-calculator snapshots contain the output key. The graph extractor's similarly named fixture is synthetic.
- `policyengine-api`: no tracked exact-word references.
- `policyengine-app-v2/app/src/mocks/UK_Metadata.json`: variable metadata at lines 9717–9743, abolition metadata at 36677–36681 and namespace at 44307–44310. `gov.hmrc.income_tax.total_income` still exists. No sibling repository was edited.

PR #2535 is untouched. Its proposed addition of `employment_benefits` to `total_income` would count statutory pay twice after this change. Its gross-income test should use an explicit programme income definition, following the new HB/CTR concepts.

## Tests added

- Tax-total YAML: SSP/SMP/SPP exercise the actual WFP charge, retained tax aliases, preserved post-tax income and active individual/household UBI phase-outs; original investment-income cases retained.
- Additional SSP/SMP/SPP scenarios exercise the deprecated WFP eligibility reform's income test directly.
- HB gross-income YAML: 21 cases, including national/claimant-age routing, statutory pay, maintenance, periodic benefits and disability disregards.
- CTR gross-income YAML: 18 cases, including routed England pensioner and Scotland/Wales working/pension-age national schemes and final award plumbing.
- HB/CTR earnings YAML: 3 mixed-income cases with two claimant ages each, checking statutory pay once in the earnings numerator and tax denominator.
- `test_income_concepts_properties.py`: Hypothesis count-once property across all tax/HB/CTR concepts and preserved bases; differential property across all tax components, expenses, ISA interest, trading/property deductions, current/carried-forward losses and net-pay/RAS pensions. Synthetic populations only.
- Existing HB direct-input and UBI phase-out fixtures updated to name their intended income bases.

## Validation and CI

- Reservation gate exited0 before local tests; local pytest limited to 2 workers and BLAS/OpenMP threads limited to 2.
- Full `ruff format --check .`, `ruff check .` and `uvx ruff format --check .` passed.
- Locked environment: `UV_LINK_MODE=clone uv sync --frozen --extra dev`, with cache inside the workspace; installed 153 locked packages including policyengine-core 3.33.2.
- Local Python properties: `uv run --no-sync pytest policyengine_uk/tests/test_income_concepts_properties.py policyengine_uk/tests/test_total_income_net_pay_properties.py -n 2 --dist worksteal -q`: **3 passed** in 768.82 s. Focused tax/WFP YAML, including additional deprecated-reform cases: **9 passed** in 23.72 s, with one existing anyio assertion-rewrite warning.
- Implementation-head CI: **4,488 YAML cases passed** in 299.51 s; fix evidence, lint, documentation and Python 3.11–3.14 smoke imports passed. All five Python shards and Test / Result outcome audit passed. Aggregate impact passed. The final report/test commit triggers fresh CI; its results are tracked on the PR and in the hand-off.
- No local microsimulation, dataset build or documentation build. CI runs the full suite and documentation; microsimulation/aggregate work stays on CI.
- Aggregate impact: **passed** at the validated implementation head; figures below. The initial prerequisite run was superseded and cancelled.
- Independent review is reserved for the hub under the host hand-off rules; no in-job reviewer was spawned. `axiom: needed` is recorded in the PR because the task permits writes only in this workspace.

## Aggregate impact figures

[Aggregate impact run 40014615941](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40014615941) **passed**. Base `c417f283a92a8618e85dfea270d5c29b4d25b82d` versus GitHub merge head `52686bd7b4e7b46110c73363c6635a6225576148` (PR implementation source `7bdd785099b9e5bd6c47770a0d92b80e98d734b1`), on certified `enhanced_frs_2024_25.h5`, data 1.58.1 / sha256 `056e80fd8e91`. These figures include the requested #2066 prerequisite, which remains unmerged on main. The final documentation/test commit changes no formulas.

| Change (£m) | 2025-26 | 2026-27 | 2027-28 | 2028-29 | 2029-30 | 2030-31 | 2031-32 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Income Tax receipts | +293.298 | +310.085 | +337.063 | +350.861 | +368.800 | +396.103 | +420.894 |
| Winter Fuel Payment spending | +175.420 | +183.658 | +214.634 | +217.058 | +228.189 | +259.066 | +293.788 |
| Housing Benefit spending | -0.269 | -0.280 | -0.291 | -0.298 | -0.306 | -0.313 | -0.321 |
| Council Tax Reduction spending | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Government balance † | +118.146 | +126.708 | +122.720 | +134.101 | +140.916 | +137.350 | +127.427 |

| Caseload change | 2025-26 | 2026-27 | 2027-28 | 2028-29 | 2029-30 | 2030-31 | 2031-32 |
|---|---:|---:|---:|---:|---:|---:|---:|
| WFP recipients gained (weighted people) | 783,692 | 816,587 | 934,788 | 940,210 | 991,896 | 1,139,819 | 1,303,000 |

HB and CTR caseloads are unchanged in every measured year. CTR spending is exactly unchanged. **0 newly broken checks; 1 pre-existing failure on both sides (negative VAT); 22 moves flagged for review.** All 85 fiscal counted-once perturbation checks passed, with 0 skipped.

† As in the report, government balance excludes suppressed Disabled Students’ Allowance figures from fewer than 10 records. Other totals/deciles carrying that component use the same suppression rule. The certified dataset has no positive SPP records, so SPP coverage comes from the YAML and random-input tests. Full distributional, poverty and reform-costing figures are in the linked report.

## Workspace and hand-off

The original `.git` points into the caller's protected repository. Its metadata could not be written. Git metadata for this job lives in `.job/git`, using `GIT_DIR=$PWD/.job/git GIT_WORK_TREE=$PWD`; code, commits and pushes use this workspace only. `.job/PROGRESS.md`, `.job/HANDOFF.md` and `.job/handoffs.jsonl` are local hand-off artifacts. The pushed PR branch is authoritative.

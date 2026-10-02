# Effective take-up rate analysis plan

```{note}
**Planning page.** Tracks
[#1354](https://github.com/PolicyEngine/policyengine-uk/issues/1354),
which asks for a comprehensive analysis of how the data processing
pipeline (reweighting, SPI integration) changes effective take-up
rates away from the seed values in `policyengine-uk-data`. This page
documents the methodology and per-programme target list.
```

## Why this matters

PolicyEngine UK doesn't compute benefit take-up from scratch — it
**seeds** stochastic take-up flags (`would_claim_*`) per programme in
`policyengine-uk-data` from prior research-published target rates,
then runs them through:

1. **Reported anchoring** (currently inconsistent — only UC and PC use
   the input-only pattern; HB / IS / WTC / CTC still derive at
   runtime; see [pipeline alignment plan](./uk-pipeline-alignment-plan.md)).
2. **Reweighting** to match aggregate caseload and expenditure
   targets.
3. **SPI integration** for income-tax-relevant variables (which can
   shift the income distribution and therefore who falls into each
   benefit's eligible population).

By the end of the pipeline the *effective* take-up rate — the share of
the eligible population that ends up with `would_claim_X == True` — can
diverge from the seed rate by a few percentage points. The seeded rates
themselves were calibrated against pre-reweighted aggregates, so the
real interest is how the post-pipeline shares stack up against
published outturn share figures.

## Programmes to cover

Per #1354, with current PolicyEngine UK take-up handling status:

| Programme | Variable | Take-up input | Source of seed rate | Status |
|-----------|----------|----------------|---------------------|--------|
| Universal Credit | `universal_credit` | `would_claim_uc` (input-only) | DWP UC official statistics | Modern pattern |
| Pension Credit | `pension_credit` | `would_claim_pension_credit` (input-only) | DWP Pension Credit take-up tables | Modern pattern |
| Housing Benefit | `housing_benefit` | `would_claim_housing_benefit` (formula-derived) | `gov.dwp.housing_benefit.takeup` | Legacy pattern (#1621 item 1) |
| Income Support | `income_support` | `would_claim_IS` (formula-derived) | `gov.dwp.income_support.takeup` | Legacy pattern (#1621 item 1) |
| Child Tax Credit | `child_tax_credit` | `would_claim_CTC` (formula-derived) | `gov.dwp.tax_credits.child_tax_credit.takeup` | Legacy pattern; scheme ended 2025-04-06 |
| Working Tax Credit | `working_tax_credit` | `would_claim_WTC` (formula-derived) | `gov.dwp.tax_credits.working_tax_credit.takeup` | Legacy pattern; scheme ended 2025-04-06 |
| Tax-Free Childcare | `tax_free_childcare` | `would_claim_tfc` | HMRC TFC statistics | – |
| Child Benefit | `child_benefit` | `would_claim_child_benefit` | `gov.hmrc.child_benefit.takeup.overall` + by_age | – |
| Marriage Allowance | `marriage_allowance` | `would_claim_marriage_allowance` | `gov.hmrc.income_tax.allowances.marriage_allowance.takeup_rate` (0.5 post-2019 steady state per #623) | – |
| Bursary Fund 16-19 | `bursary_fund_16_to_19` | `would_claim_bursary_fund_16_to_19` | DfE bursary statistics | – |
| Adult Dependants Grant | – | `would_claim_adult_dependants_grant` | SFE statistics | – |
| Travel Grant | – | `would_claim_travel_grant` | SFE statistics | – |
| Extended Childcare Entitlement | `extended_childcare_entitlement` | `would_claim_extended_childcare` | DfE take-up | – |
| Targeted Childcare Entitlement | `targeted_childcare_entitlement` | `would_claim_targeted_childcare` | DfE take-up | – |
| Scottish Child Payment | `scottish_child_payment` | `would_claim_scp` | Social Security Scotland statistics | – |
| State Pension | `state_pension` | n/a (effectively universal) | – | Universal — see [state-pension.md](../programs/gov/dwp/state-pension.md) |
| PIP / DLA / AA / SDA / Carer's Allowance | various | currently coded as "reported = paid" | DWP caseload | No explicit take-up variable today; covered in [disability-legacy-benefits.md](../programs/gov/dwp/disability-legacy-benefits.md) |
| Council Tax Reduction | `council_tax_benefit` | (no formula; reported-only) | – | Tracked in #1669 — rules-based formula in flight |

## Methodology

For each programme above, the analysis should produce:

1. **Seed take-up rate** — what the relevant `*_takeup_rate` parameter
   reports for the analysis year, plus the source (HMRC / DWP /
   academic study) and vintage.
2. **Effective take-up rate post-pipeline** — counted from the built
   dataset as `sum(would_claim_X * weight) / sum(eligible_X * weight)`,
   where `eligible_X` is computed from the runtime formulas.
3. **Published outturn share** for the same year — DWP / HMRC
   statistical publications giving claimant counts and either eligible
   population counts (where DWP estimates them) or a published take-up
   rate.
4. **Pipeline drift** — `effective − seed` per programme, with a sign
   convention so positive means more claimants than seeded.

The published reference rates change roughly annually. The analysis
should be repeatable, ideally as a notebook under
[`docs/book/validation/`](../validation/) so future builds can re-run
it and update the gaps table.

## Output

A new validation notebook
`docs/book/validation/take-up-rates.ipynb` should:

- pull each programme's seed take-up parameter,
- compute the effective rate against the built dataset,
- compare to the most recent published share (DWP take-up tables for
  income-related benefits, HMRC TFC + tax credits statistics for the
  rest),
- flag drifts of more than ±2 percentage points for follow-up.

The first run is the deliverable for #1354. After that the notebook
becomes a part of the validation page and gets re-run on each EFO /
data refresh.

## Related work

- The **takeup-anchoring port** from `policyengine-us-data`
  (`assign_takeup_with_reported_anchors`, see [pipeline alignment
  plan](./uk-pipeline-alignment-plan.md)) is the most likely cause of
  systematic drift between seed and effective for the legacy-pattern
  programmes. Landing that port first would change the numbers this
  analysis produces.
- The **`would_claim_*` input-only conversion** (also in #1621) would
  give the analysis a cleaner ladder: with all of `would_claim_*` as
  inputs, the effective rate is exactly the share assigned by the
  stochastic step in `frs.py`, and pipeline drift becomes a pure
  reweighting question.

## References

- Issue: [#1354](https://github.com/PolicyEngine/policyengine-uk/issues/1354).
- Initial analysis (UC + CTC): https://gist.github.com/MaxGhenis/763db9278ddecdf310f160a73e138c8a
- DWP, [Income-related benefits: estimates of take-up](https://www.gov.uk/government/collections/income-related-benefits-estimates-of-take-up) — primary reference rates for HB / IS / PC / UC.
- HMRC, [Personal tax credits statistics](https://www.gov.uk/government/collections/personal-tax-credits-statistics).
- HMRC, [Child Benefit statistics](https://www.gov.uk/government/collections/child-benefit-statistics) and Marriage Allowance statistics.
- Cross-links: [`uk-pipeline-alignment-plan.md`](./uk-pipeline-alignment-plan.md), [`state-pension.md`](../programs/gov/dwp/state-pension.md), [`disability-legacy-benefits.md`](../programs/gov/dwp/disability-legacy-benefits.md), [`tax-credits.md`](../programs/gov/dwp/tax-credits.md).

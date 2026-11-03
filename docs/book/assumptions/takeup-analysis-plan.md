# Effective take-up rate analysis plan

```{note}
**Planning page.** Tracks
[#1354](https://github.com/PolicyEngine/policyengine-uk/issues/1354),
which asks for a comprehensive analysis of how the data processing
pipeline (reweighting, SPI integration) changes effective take-up
rates away from the seed values. This page documents the methodology
and per-programme target list.
```

```{admonition} Status, October 2026
The analysis below has not been run yet. Stochastic take-up flags are
drawn in the data build, not in this repository; the Housing Benefit,
Income Support, tax credit and Council Tax Reduction flags are formulas
here (see below). Since policyengine.py 6.10.0 (21 October 2026) the
certified UK default dataset is Microcosm UK (`microcosm_uk_2024_25`),
built by [Microcosm](https://github.com/PolicyEngine/microcosm). The
Enhanced FRS built by
[`policyengine-uk-data`](https://github.com/PolicyEngine/policyengine-uk-data)
stays loadable by name at release 1.58.1, and it is the dataset this
repository's credentialed tests pin
(`policyengine_uk/tests/certified_dataset.yaml`). Both draw Universal
Credit, Pension Credit and Child Benefit take-up anchored on reported
receipt, and Microcosm adds some draws the Enhanced FRS lacks (see the
table), so the analysis should run on whichever dataset is the certified
default at the time.
```

## Why this matters

PolicyEngine UK does not compute benefit take-up from scratch. The data
build **seeds** stochastic take-up flags (`would_claim_*`) for most
programmes from target rates (some published take-up estimates, some
fitted to caseload or spending, and Universal Credit's 0.55, which has no
cited source in policyengine-uk-data and is held in Microcosm for parity
with the earlier pipeline), then runs them through:

1. **Reported anchoring.** Universal Credit, Pension Credit and Child
   Benefit flags are inputs, drawn so that units reporting receipt
   claim. Housing Benefit, Income Support, the tax credits and Council
   Tax Reduction instead derive their flags at runtime: on data-built
   simulations they equal reported receipt, and hand-entered households
   also claim when `claims_all_entitled_benefits` is true; see
   [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
2. **SPI integration** for income-tax-relevant variables (which can
   shift the income distribution and therefore who falls into each
   benefit's eligible population).
3. **Reweighting** to match aggregate caseload and expenditure
   targets.

Both builds integrate the SPI before reweighting. Pension Credit take-up
(both builds), and Child Benefit and Carer's Allowance take-up
(Microcosm), are redrawn after the SPI step.

By the end of the pipeline the *effective* take-up rate, the share of
the eligible population that ends up with `would_claim_X == True`, can
diverge a long way from the seed rate: the initial analysis linked below
found 74.9% of the benefit units entitled to Universal Credit in 2026
receiving it, against a 55% seed (Enhanced FRS 2023-24, policyengine-uk
2.53.1). Part of the gap is by construction, because the data builds
apply most seed rates to every benefit unit, not only to eligible ones.
Some seed rates are published take-up estimates (Pension Credit, Child
Benefit, Scottish Child Payment, Marriage Allowance); others were fitted
to caseload or spending targets, some at calibrated weights (Tax-Free
Childcare in policyengine-uk-data, the Universal Credit childcare element
in Microcosm). The real interest is how the post-pipeline shares stack up
against published outturn share figures.

## Where the seed rates live

The take-up rate parameters in this repository (for example
`gov.dwp.universal_credit.takeup_rate` and `gov.dwp.housing_benefit.takeup`)
are reference values: no formula reads them. The rates the data build
draws from are in `policyengine_uk_data/parameters/take_up/` in
policyengine-uk-data and in
`packages/microcosm-build/src/microcosm/build/uk/take_up_contract.json`
in Microcosm. The analysis should read the seed rate from the data build
that produced the dataset, and check the matching parameter here is in
sync. Two already differ: Pension Credit is 0.7 here against 0.62 in
policyengine-uk-data from April 2023, and Scottish Child Payment for
children aged 6 and over is 0.86 here against 0.85 in both builds.

## Programmes to cover

Per #1354, with current PolicyEngine UK take-up handling:

| Programme | Variable | Take-up flag | Reference parameter here | Handling |
|-----------|----------|--------------|--------------------------|----------|
| Universal Credit | `universal_credit` | `would_claim_uc` (input) | `gov.dwp.universal_credit.takeup_rate` | Drawn in the data build, anchored on reported receipt |
| UC on legacy closure | `claims_uc_at_legacy_closure` | `would_claim_uc_at_legacy_closure` (input) | – | Drawn in Microcosm at DWP's Move to Universal Credit claim rates by legacy benefit combination; the Enhanced FRS does not set it, so it defaults to true |
| UC childcare element | `uc_childcare_element` (claimed via `uc_childcare_element_claimed`) | `would_claim_uc_childcare` (input) | – | Drawn in Microcosm at single and couple rates; the Enhanced FRS does not set it, so it defaults to true |
| Pension Credit | `pension_credit` | `would_claim_pc` (input) | `gov.dwp.pension_credit.takeup` | Drawn in the data build, anchored on reported receipt |
| Child Benefit | `child_benefit` | `would_claim_child_benefit` (input) | `gov.hmrc.child_benefit.takeup.overall` and `.by_age` | Drawn in the data build, anchored on reported receipt |
| Housing Benefit | `housing_benefit` | `would_claim_housing_benefit` (formula) | `gov.dwp.housing_benefit.takeup` | Follows reported receipt (#1621) |
| Income Support | `income_support` | `would_claim_IS` (formula) | `gov.dwp.income_support.takeup` | Follows reported receipt (#1621); scheme closed 2026-04-01 |
| Income-based JSA / income-related ESA | `jsa_income`, `esa_income` | none | `gov.dwp.JSA.income.takeup`, `gov.dwp.ESA.income.takeup_estimate_fye_2019` | Paid on reported awards that pass capital and work tests; income-based JSA closed 2026-04-01 |
| Child Tax Credit | `child_tax_credit` | `would_claim_CTC` (formula) | `gov.dwp.tax_credits.child_tax_credit.takeup` | Follows reported receipt; scheme ended on 5 April 2025 |
| Working Tax Credit | `working_tax_credit` | `would_claim_WTC` (formula) | `gov.dwp.tax_credits.working_tax_credit.takeup` | Follows reported receipt; scheme ended on 5 April 2025 |
| Council Tax Reduction | `council_tax_reduction` | `would_claim_council_tax_reduction` (formula) | – | Simulated for England's pension-age scheme, the Scottish and Welsh schemes and five English councils' working-age schemes, reported reductions elsewhere; on data-built simulations take-up follows reported receipt |
| Tax-Free Childcare | `tax_free_childcare` | `would_claim_tfc` (input) | – | Drawn in the data build at a flat rate |
| Universal childcare entitlement | `universal_childcare_entitlement` | `would_claim_universal_childcare` (input) | – | Drawn in the data build at a flat rate |
| Extended childcare entitlement | `extended_childcare_entitlement` | `would_claim_extended_childcare` (input) | – | Drawn in the data build at a flat rate |
| Targeted childcare entitlement | `targeted_childcare_entitlement` | `would_claim_targeted_childcare` (input) | – | Drawn in the data build at a flat rate |
| Marriage Allowance | `marriage_allowance` | `would_claim_marriage_allowance` (input) | `gov.hmrc.income_tax.allowances.marriage_allowance.takeup_rate` (0.5, the post-2019 steady state) | Drawn in the data build at a flat rate |
| Scottish Child Payment | `scottish_child_payment` | `would_claim_scp` (input) | `gov.social_security_scotland.scottish_child_payment.takeup_rate` (under 6, 6 and over) | Drawn in the data build by age |
| Carer's Allowance | `carers_allowance` | `would_claim_carers_allowance` (input) | – | Set from reported receipt in Microcosm, whose main branch since 20 October 2026 also draws a claim at 0.6 for carers outside Scotland whom only the earnings limit keeps from the allowance; the Enhanced FRS does not set it, so it defaults to true |
| 16 to 19 Bursary Fund | `bursary_fund_16_to_19` | `would_claim_bursary_fund_16_to_19` (input) | – | Defaults to true |
| Student support grants | `adult_dependants_grant`, `childcare_grant`, `parents_learning_allowance`, `travel_grant`, `disabled_students_allowance` | `would_claim_adult_dependants_grant`, `would_claim_childcare_grant`, `would_claim_parents_learning_allowance`, `would_claim_travel_grant`, `would_claim_disabled_students_allowance` (inputs) | – | Default to true |
| Care to Learn | `care_to_learn` | `would_claim_care_to_learn` (input) | – | Defaults to true |
| State Pension | `state_pension` | none | – | Paid from reported State Pension (`state_pension_reported`); see [state-pension.md](../programs/gov/dwp/state-pension.md) |
| PIP / DLA / AA / SDA | various | none | – | PIP, DLA and AA category inputs set from reported receipt (PIP categories can also come from points); SDA paid at the maximum rate where `sda_reported` is positive; see [disability-legacy-benefits.md](../programs/gov/dwp/disability-legacy-benefits.md) |

## Methodology

For each programme above, the analysis should produce:

1. **Seed take-up rate:** the rate the data build drew from for the
   analysis year, plus the source (HMRC, DWP or an academic study) and
   vintage.
2. **Effective take-up rate post-pipeline:** counted from the built
   dataset as
   `sum(would_claim_X * eligible_X * weight) / sum(eligible_X * weight)`,
   where `eligible_X` is computed from the runtime formulas. The
   numerator counts only eligible units, because `would_claim_X` can be
   true for ineligible units too (otherwise one eligible unit and two
   willing units would give 200%). Where no unit is eligible the
   denominator is zero; report the rate as undefined (n/a), not 0%.
3. **Published outturn share** for the same year: DWP and HMRC
   statistical publications giving claimant counts and either eligible
   population counts (where DWP estimates them) or a published take-up
   rate.
4. **Pipeline drift:** `effective − seed` per programme, with a sign
   convention so positive means more claimants than seeded.

Most published reference rates change roughly annually (HMRC's tax
credit take-up rates stop at 2017 to 2018). The analysis should be
repeatable, ideally as a notebook under
[`docs/book/validation/`](../validation/) so future builds can re-run
it and update the gaps table. A notebook needs its own `file:` entry
under Validation in `myst.yml` to appear in the docs, since only
Markdown pages are picked up by folder.

## Output

A new validation notebook
`docs/book/validation/take-up-rates.ipynb` should:

- pull each programme's seed take-up rate from the data build that
  produced the dataset,
- compute the effective rate against the built dataset,
- compare to the most recent published share (DWP's income-related
  benefits take-up tables; HMRC's Child Benefit, Tax-Free Childcare and
  tax relief statistics; Scottish Government take-up rates; DfE
  childcare statistics),
- flag drifts of more than ±2 percentage points for follow-up.

The first run is the deliverable for #1354. After that the notebook
becomes a part of the validation page and gets re-run on each EFO /
data refresh.

## Related work

- **Reported-anchored take-up** is in both data builds for UC, Pension
  Credit and Child Benefit. The programmes whose flags still follow
  reported receipt at runtime have no seed draw: their effective rate is
  the share of eligible units that report receipt, which the analysis
  should compare with the published rate directly.
- The **`would_claim_*` input-only conversion** (also in #1621) would
  give the analysis a cleaner ladder: with all of `would_claim_*` as
  inputs, every flag comes from the data build's take-up stage, and
  pipeline drift comes only from the steps after it (SPI income
  imputation and reweighting).

## References

- Issue: [#1354](https://github.com/PolicyEngine/policyengine-uk/issues/1354).
- Initial analysis (UC and CTC): <https://gist.github.com/MaxGhenis/763db9278ddecdf310f160a73e138c8a> (policyengine-uk 2.53.1; it measured take-up by setting `gov.dwp.universal_credit.takeup_rate` to 1, which no longer changes take-up on main).
- DWP, [Income-related benefits: estimates of take-up](https://www.gov.uk/government/collections/income-related-benefits-estimates-of-take-up--2): reference rates for Pension Credit and pensioners' Housing Benefit, and (from the financial year ending 2025 edition) a composite Universal Credit (or equivalent benefits) rate.
- HMRC, [Personal tax credits statistics](https://www.gov.uk/government/collections/personal-tax-credits-statistics).
- HMRC, [Child Benefit: annual release](https://www.gov.uk/government/collections/child-benefit-geographical-statistics), and Marriage Allowance claimants and cost in HMRC's [tax relief statistics](https://www.gov.uk/government/statistics/tax-reliefs/tax-relief-statistics-january-2026).
- Pipeline alignment: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
- Cross-links: [`state-pension.md`](../programs/gov/dwp/state-pension.md), [`disability-legacy-benefits.md`](../programs/gov/dwp/disability-legacy-benefits.md), [`tax-credits.md`](../programs/gov/dwp/tax-credits.md).

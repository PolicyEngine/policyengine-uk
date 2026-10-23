# UK model/data pipeline alignment plan

```{note}
**Planning page** setting out the gaps between the UK model and data
pipeline and the US `policyengine-us` / `policyengine-us-data` patterns,
plus a sequence of scoped PRs that would close them. Tracked in
[#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
Most items here are **cross-repo**: they touch the data pipeline rather
than this repo, but the model-side contract is documented here so the
receiving side has a stable target.
```

```{admonition} Status, October 2026
The target data pipeline is now
[Microcosm UK](https://github.com/PolicyEngine/microcosm), which replaced
the Enhanced FRS build in `policyengine-uk-data`; its UK national line is
built on the Family Resources Survey 2024-25 (`microcosm_uk_2024_25`).
Gaps 2 and 3 below, and PR 4 of the sequence, are implemented there (and
were in policyengine-uk-data in April 2026, gap 3 in narrower form);
gap 1 is still open on the model side. The aggregate residuals other than
State Pension are the figures #1621 reported for 2025 on Enhanced FRS 1.50.3
in April 2026, and none has been re-measured on the Microcosm release.
```

## Architectural gaps vs US

### 1. `_reported` consulted at runtime in some `would_claim_*` formulas

**US pattern**: `_reported` columns are consulted **once, in the
data-build**, to anchor stochastic take-up flags (reported recipient →
takeup = True with certainty; rest filled probabilistically to a target
rate). Runtime formulas only read the pre-computed
`takes_up_X_if_eligible` flag, so reforms that change eligibility flow
through cleanly to take-up.

**UK pattern (partial)**: some UK `would_claim_*` variables already
match: `would_claim_uc` and `would_claim_pc` are input-only with
`default_value = True`, populated by the data build (now Microcosm
UK's `frs_take_up` stage). But several still derive from
`_reported` at runtime:

- `would_claim_housing_benefit`
- `would_claim_council_tax_reduction`
- `would_claim_IS`
- `would_claim_WTC`
- `would_claim_CTC`

In hand-entered situations each is `claims_all_entitled_benefits | (foo_reported > 0)`
(for Income Support only the claimant's or partner's report counts), and
`claims_all_entitled_benefits` is true for a benefit unit that reports under
£1 across seven means-tested benefits. In data-built simulations
`claims_all_entitled_benefits` is false for every benefit unit, and Housing
Benefit and Council Tax Reduction ignore it, so a reform expanding
eligibility only reaches existing `_reported > 0` claimants. Setting
`claims_all_entitled_benefits` to true does not change this for Child Tax
Credit, Working Tax Credit, Income Support or working-age Housing Benefit,
because their eligibility tests (`is_CTC_eligible`, `is_WTC_eligible`,
`income_support_eligible`, `housing_benefit_eligible`) also require a
reported award.

**Fix**: convert each to input-only `default_value = True` (matching
`would_claim_uc`), and add each to Microcosm UK's reported-anchored
take-up stages. Because of those eligibility tests, this changes take-up for
non-reporters only for Council Tax Reduction and pension-age Housing
Benefit. Tax credits stopped paying ongoing awards on 5 April
2025, and `gov.dwp.tax_credits.active` is false from 2025-04-06 (see
[tax-credits.md](../programs/gov/dwp/tax-credits.md)), so the WTC and CTC
fix matters only for simulations of earlier years.

### 2. Take-up assignment ignores reported data

**Done in Microcosm UK.** Its `frs_take_up`, `pension_credit_take_up`
and `child_benefit_take_up` stages keep every benefit unit that reports
receipt as a claimant and draw the rest to the target rate
([`source_stages.json` at `75167a6`](https://github.com/PolicyEngine/microcosm/blob/75167a68/packages/microcosm-build/src/microcosm/build/uk/source_stages.json)).
The description below is the Enhanced FRS behaviour before
[policyengine-uk-data#359](https://github.com/PolicyEngine/policyengine-uk-data/pull/359)
(April 2026), which anchored the same three flags on reported receipt.

Until then the Enhanced FRS take-up assignment was a pure random draw:

```python
pe_benunit["would_claim_uc"] = generator.random(len(pe_benunit)) < universal_credit_rate
```

This discards information: respondents who reported receiving UC
clearly took it up, and should have `would_claim_uc = True` with
certainty.

**Fix** (done in policyengine-uk-data#359): port
`policyengine_us_data/utils/takeup.py::assign_takeup_with_reported_anchors`
into `policyengine-uk-data` and apply it to each take-up variable where
a `_reported` column exists (`would_claim_uc`, `would_claim_pc`,
`would_claim_child_benefit`). This tightens per-variable calibration
without changing the target rates.

### 3. Second-stage imputation gap on SPI donors

**Done in Microcosm UK.** `hmrc_spi_income_spine` draws `gift_aid` and
`charitable_investment_gifts` from the SPI with the new incomes, and trains
an FRS-only second stage on FRS rows that it predicts from those incomes
(pension contributions, tax-free savings income and the `*_reported`
benefits), `spi_housing_shell` redraws tenure,
dwelling and council tax band for the SPI households, and the wealth,
spending and VAT stages now run after the SPI block, so they are drawn
for the new incomes rather than inherited from the FRS parent. The
description below is the Enhanced FRS behaviour before April 2026:
policyengine-uk-data#347 then added `gift_aid` and
`charitable_investment_gifts` to the SPI imputation, and #362 added a
second-stage QRF (`datasets/imputations/frs_only.py`) for pension
contributions, tax-free savings income and the `*_reported` benefits; rent
and wealth on SPI rows still come from the FRS parent there.

`policyengine_uk_data/datasets/imputations/income.py::impute_income`
trained a QRF that replaced only six income variables on SPI donor
rows; everything else (rent, wealth, pension contributions, gift aid,
benefits-reported flags) stayed as whatever middle-income FRS donor
happened to be sampled. So a synthetic SPI donor ending up with £2M
imputed self-employment income still carried an unchanged middle-FRS-
donor's savings balance and zero gift aid.

The US equivalent ([`policyengine-us-data#589`](https://github.com/PolicyEngine/policyengine-us-data/pull/589))
fixed this by adding a second-stage QRF: train on CPS with predictors =
demographics + newly-imputed income vars, outputs = the ~60 CPS-only
variables; for PUF-clone prediction, substitute imputed PUF incomes as
predictors so CPS-only variables come out consistent with imputed
income.

**Fix**: add the analogous second-stage QRF in
`policyengine_uk_data/datasets/imputations/`, training on FRS with
predictors = demographics + 6 income vars, outputs = a wide set of
"FRS-only" consequential variables including rent,
`mortgage_interest_repayment`, `gift_aid`, `covenanted_payments`,
`charitable_investment_gifts`, `other_deductions`,
`employee_pension_contributions*`, `employer_pension_contributions`,
total wealth components, `capital_allowances`, `deficiency_relief`,
and the full list of `*_reported` benefits. policyengine-uk-data#362 (April
2026) added this stage with a narrower output list: pension contributions,
tax-free savings income and the `*_reported` benefits.

## Specific aggregate residuals

After the formula-side fixes already merged (BASIC/NEW classification
in [PR #1618](https://github.com/PolicyEngine/policyengine-uk/pull/1618),
new State Pension pro-rating + Protected Payment in
[PR #1634](https://github.com/PolicyEngine/policyengine-uk/pull/1634)),
the residual benefit-aggregate gaps against OBR on the Enhanced FRS
(for the rows other than State Pension, the figures #1621 reported for 2025
on Enhanced FRS 1.50.3 in April 2026; the State Pension row is taken from
the State Pension page; none re-measured on Microcosm UK) were:

| Variable | Model | Target | Gap | Likely cause |
|----------|------:|------:|----:|--------------|
| `income_support` | ~£1.07 bn | ~£0.2 bn | **+£0.9 bn** | Legacy benefit near-fully migrated; same `reported > 0` retention issue as the (pre-fix) tax credits. |
| `esa_contrib` | ~£5.56 bn | ~£2.5 bn | **+£3.1 bn** | Large. Likely reported-based take-up plus no phase-out for migrated cases. |
| `attendance_allowance` | ~£8.76 bn | ~£7.0 bn | +£1.8 bn | Cap-rate or take-up issue. |
| `tax_free_childcare` | ~£0.41 bn | ~£0.9 bn | **-£0.5 bn** | Understated by about half: under-imputed eligible families. |
| `state_pension` | £119.0 bn | £131.3 bn | -£12.2 bn | 2024-25, against DWP's Spring Forecast 2026 less payments abroad, on policyengine-uk-data-private 1.57.4, as documented in [state-pension.md](../programs/gov/dwp/state-pension.md). Most of the shortfall arises in building the Enhanced FRS ([policyengine-uk-data#493](https://github.com/PolicyEngine/policyengine-uk-data/issues/493)). |

Each warrants a scoped PR pair (model + data) once the architectural
fixes above land.

## Items already fixed since #1621 was filed

The issue body flagged three small items; two are resolved:

- `tax_credits/min_benefit.yaml` unit was `currency-USD`; it is now `currency-GBP` (#1627).
- `benunit_weekly_hours` label said "Average" but the formula sums; label now reads "Total weekly hours worked by adults in the benefit unit" (#1627).
- Some `~` operations on Python bools raised `DeprecationWarning: Bitwise inversion '~' on bool`, which becomes an error in Python 3.16; no fix is tracked.

Separately, the `state_pension_type` BASIC/NEW classification was rewritten in PR #1618.

This page reflects the *current* gap rather than the issue body, so the
next reviewer working through the queue doesn't waste time on
already-fixed items.

## Candidate PR sequence

1. **Convert remaining `would_claim_*` formulas to input-only** (model
   side) + reported-anchored assignment in Microcosm UK's `frs_take_up`
   stage. Still open: the five formulas above read `_reported` at
   runtime on `main`.
2. ~~Port `assign_takeup_with_reported_anchors`~~: done in
   policyengine-uk-data#359 and in Microcosm UK (gap 2).
3. ~~Add second-stage QRF for FRS-only variables on SPI donors~~: done
   in policyengine-uk-data#362 (narrower outputs) and in Microcosm UK
   (gap 3).
4. ~~Add `gift_aid` to `IMPUTATIONS`~~: done in policyengine-uk-data#347
   and in Microcosm UK, where `gift_aid` is a stage-1 SPI output.
5. **Residual benefit-aggregate follow-ups**: re-measure on the
   Microcosm release first, then separate small PRs for ESA contrib
   investigation, AA calibration, TFC under-imputation, the State Pension
   data-side fix (#1632, policyengine-uk-data#493). The IS phase-out
   landed in #1631 (`gov.dwp.income_support.active` is false from
   2026-04-01).

## References

- Tracking issue: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
- US pattern reference: [`policyengine-us-data#589`](https://github.com/PolicyEngine/policyengine-us-data/pull/589).
- Related state pension docs: [state-pension.md](../programs/gov/dwp/state-pension.md), [#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632).
- Related calibration scope: [non-uk-benefit-receipt-plan.md](./non-uk-benefit-receipt-plan.md) (#842), separate from this pipeline alignment but interacting with it on the calibration target side.

# UK model/data pipeline alignment plan

```{note}
**Planning page** capturing the gaps between the UK model + enhanced FRS
pipeline and the US `policyengine-us` / `policyengine-us-data` patterns,
plus a sequence of scoped PRs that would close them. Tracked under
[#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
Most items here are **cross-repo** — they touch
`policyengine-uk-data` rather than this repo — but the model-side
contract is documented here so the receiving side has a stable target.
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
match — `would_claim_uc` and `would_claim_pc` are input-only with
`default_value = True`, populated stochastically in
`policyengine-uk-data/datasets/frs.py`. But several still derive from
`_reported` at runtime:

- `would_claim_housing_benefit`
- `would_claim_IS`
- `would_claim_WTC`
- `would_claim_CTC`

The runtime pattern is `claims_all_entitled_benefits | (foo_reported > 0)`,
which means a reform expanding eligibility only reaches existing
`_reported > 0` claimants — non-claimants who newly qualify are
invisible unless the user manually sets
`claims_all_entitled_benefits = True` everywhere.

**Fix**: convert each to input-only `default_value = True` (matching
`would_claim_uc`), populate stochastically in
`uk-data/datasets/frs.py`. Note: WTC and CTC ceased to pay new awards on
2025-04-06 (see [tax-credits.md](../programs/gov/dwp/tax-credits.md)),
so their fix is primarily for back-cast simulations.

### 2. Take-up assignment ignores reported data

Today's UK take-up assignment is a pure random draw:

```python
pe_benunit["would_claim_uc"] = generator.random(len(pe_benunit)) < universal_credit_rate
```

This discards information: respondents who reported receiving UC
clearly took it up, and should have `would_claim_uc = True` with
certainty.

**Fix**: port `policyengine_us_data/utils/takeup.py::assign_takeup_with_reported_anchors`
into `policyengine-uk-data` and apply it to each take-up variable where
a `_reported` column exists. This tightens per-variable calibration
without changing the target rates.

### 3. Second-stage imputation gap on SPI donors

`policyengine_uk_data/datasets/imputations/income.py::impute_income`
trains a QRF that replaces only six income variables on SPI donor
rows; everything else (rent, wealth, pension contributions, gift aid,
benefits-reported flags) stays as whatever middle-income FRS donor
happened to be sampled. So a synthetic SPI donor ending up with £2M
imputed self-employment income still carries an unchanged middle-FRS-
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
and the full list of `*_reported` benefits.

## Specific aggregate residuals

After the formula-side fixes already merged (BASIC/NEW classification
in [PR #1618](https://github.com/PolicyEngine/policyengine-uk/pull/1618),
new State Pension pro-rating + Protected Payment in
[PR #1634](https://github.com/PolicyEngine/policyengine-uk/pull/1634)),
the residual benefit-aggregate gaps against OBR are:

| Variable | Model | Target | Gap | Likely cause |
|----------|------:|------:|----:|--------------|
| `income_support` | ~£1.07 bn | ~£0.2 bn | **+£0.9 bn** | Legacy benefit near-fully migrated; same `reported > 0` retention issue as the (pre-fix) tax credits. |
| `esa_contrib` | ~£5.56 bn | ~£2.5 bn | **+£3.1 bn** | Large. Likely reported-based take-up plus no phase-out for migrated cases. |
| `attendance_allowance` | ~£8.76 bn | ~£7.0 bn | +£1.8 bn | Cap-rate or take-up issue. |
| `tax_free_childcare` | ~£0.41 bn | ~£0.9 bn | **-£0.5 bn** | Understated by about half — under-imputed eligible families. |
| `state_pension` | ~£127.5 bn | ~£140 bn | -£12 bn | Documented in [state-pension.md](../programs/gov/dwp/state-pension.md); data-side ASP under-imputation. |

Each warrants a scoped PR pair (model + data) once the architectural
fixes above land.

## Items already fixed since #1621 was filed

The issue body flagged three small bugs; all are now resolved:

- `tax_credits/min_benefit.yaml` unit was `currency-USD` — now `currency-GBP`.
- `benunit_weekly_hours` label said "Average" but the formula sums; label now reads "Total weekly hours worked by adults in the benefit unit".
- `state_pension_type` BASIC/NEW classification (the `is_SP_age` heuristic in the issue) was rewritten in PR #1618.

This page reflects the *current* gap rather than the issue body, so the
next reviewer working through the queue doesn't waste time on
already-fixed items.

## Candidate PR sequence

1. **Convert remaining `would_claim_*` formulas to input-only** (model
   side) + stochastic assignment in `policyengine-uk-data`
   (`datasets/frs.py`). Low risk; matches the existing UC/PC pattern.
2. **Port `assign_takeup_with_reported_anchors`** into
   `policyengine-uk-data`. Pure data-pipeline change; tightens
   calibration.
3. **Add second-stage QRF for FRS-only variables on SPI donors** in
   `policyengine-uk-data`. Biggest single ticket but directly addresses
   the "high-income donor has zero gift aid / zero rent" failure.
4. **Add `gift_aid` to `IMPUTATIONS`** (one-line addition in
   `policyengine_uk_data/datasets/imputations/income.py`). Independent
   of (3); can land immediately.
5. **Residual benefit-aggregate follow-ups** — separate small PRs for
   IS phase-out (analogous to the WTC/CTC reactive scheme close-out),
   ESA contrib investigation, AA calibration, TFC under-imputation,
   ASP data-side fix (the residual #1632 leg).

## References

- Tracking issue: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
- US pattern reference: [`policyengine-us-data#589`](https://github.com/PolicyEngine/policyengine-us-data/pull/589).
- Related state pension docs: [state-pension.md](../programs/gov/dwp/state-pension.md), [#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632).
- Related calibration scope: [non-uk-benefit-receipt-plan.md](./non-uk-benefit-receipt-plan.md) (#842) — separate from this pipeline alignment but interacts with the calibration target side.

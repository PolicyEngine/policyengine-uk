# Capital gains distribution plan

```{note}
**Planning page.** Tracks [#818](https://github.com/PolicyEngine/policyengine-uk/issues/818)
and the related zero-wealth imputation question raised in
[#817](https://github.com/PolicyEngine/policyengine-uk/issues/817).
PolicyEngine UK's capital gains imputation lives in
`policyengine-uk-data`, not in this repo — but the modelling
assumptions and the calibration constraints are documented here so the
cross-repo plan is discoverable from a single page.
```

## Current state

PolicyEngine UK reads `capital_gains_before_response` as a person-level
input variable; the runtime variables under
[`variables/gov/hmrc/capital_gains_tax/`](../../../policyengine_uk/variables/gov/hmrc/capital_gains_tax)
then compute the elasticity-based behavioural response and the tax
liability against the published CGT bracket structure.

The input itself is produced in `policyengine-uk-data` by:

1. Splitting the population into income deciles.
2. Fitting a separate marginal distribution of capital gains within
   each decile (against HMRC's *Capital Gains Statistics*).
3. Drawing values for each FRS row from the decile-conditional
   distribution.

This is the **independent per-decile model** that #818 flagged.

## Limitations of the current approach

### 1. Overfitting at the boundaries

Per-decile fitting means each decile's tail is fit independently from
its neighbours. With HMRC's published CGT statistics binning gains by
income, the per-decile tails contain few observations — the fitted
upper tails are noisy, and the joint distribution of "income + capital
gains" can have spurious features at decile boundaries.

### 2. No conditioning on wealth

#817 reported a related failure mode: capital gains are imputed to
households with zero recorded wealth. That's structurally implausible
(you can't realise gains on assets you don't own) and arises because
the per-decile model conditions only on income, not on wealth holdings.
Many low-income retirees with substantial wealth would receive gains
the current model misses; many low-income tenants with zero wealth
incorrectly receive them.

### 3. No covariance between income and gains beyond decile membership

A higher-rate-band earner with £200k income and a lower-rate earner
with £40k income within the same decile (after weighting / SPI)
receive draws from the same marginal distribution. In reality the
correlation between income and gains is much stronger than that.

## Proposed approach (#818)

Switch to a **multivariate model over (income, wealth, age, gender)**
that produces capital gains as a derived dimension. Concrete options:

### A. Multivariate KDE

The [OG-USA bequest model](https://pslmodels.github.io/OG-USA/content/api/bequest_transmission.html)
referenced in #818 uses a multivariate Gaussian KDE over the relevant
conditioning variables. For UK gains the bandwidth + kernel choice
would need calibrating against HMRC's gains-by-income-by-age cross-tabs;
the SAS *Survey of Personal Incomes* extracts (where available via
Datalab) give a richer conditioning set.

Tradeoffs:

- **Pro**: no per-decile boundary artefacts; the joint distribution
  comes out smooth in all dimensions.
- **Con**: KDE bandwidth choice is tricky in the tail; large gains
  remain noisy unless we supplement with a tail model.

### B. Two-stage QRF

Train a quantile-regression-forest (QRF) on the SPI donor set with
predictors = `(age, gender, region, employment_income,
self_employment_income, savings_interest_income, dividend_income,
total_wealth, gross_financial_wealth)` and output = annual capital
gains. This is the same machinery already used in
`policyengine-uk-data/datasets/imputations/income.py` and the
proposed second-stage QRF in [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621)
/ [pipeline alignment plan](./uk-pipeline-alignment-plan.md).

Tradeoffs:

- **Pro**: the QRF naturally handles correlated predictors and
  produces well-calibrated quantiles in the tail. Reuses existing
  imputation infrastructure.
- **Con**: requires a clean SPI-linked donor set with all the
  conditioning variables (currently the QRF in `income.py` doesn't
  output capital gains).

**Recommendation**: option B. The infrastructure is in place, the
calibration is testable against HMRC published gains-by-income-band
tables, and it consistently solves both #818 (overfitting) and #817
(implausible zero-wealth gains) by making `total_wealth` a predictor.

## What changes in this repo

The model-side surface is small:

- The `capital_gains_before_response` input variable stays the same.
  All the changes are upstream in `policyengine-uk-data`.
- A regression test in the model that asserts **no positive capital
  gains for households with zero total wealth** would catch
  reintroductions of the #817 failure mode and live well in
  `policyengine_uk/tests/`.

## Open questions

- Wealth in the FRS is incomplete and noisy; the WAS (Wealth and
  Assets Survey) is the better wealth conditioning source but is on a
  different sampling frame. Should the QRF be trained on a WAS-linked
  donor, or do we condition on the FRS-imputed wealth and accept the
  noise?
- HMRC's published CGT statistics break gains down by income, age, and
  asset type but not by household wealth. Calibration targets will
  need to be assembled across multiple HMRC and ONS sources.
- Behavioural response (`capital_gains_behavioural_response` in this
  repo) currently uses a single elasticity. A multivariate model that
  gets the distribution right opens the door to **elasticity by
  income / wealth band** — useful for reform analysis but adds a
  parameter surface.

## References

- Issue: [#818](https://github.com/PolicyEngine/policyengine-uk/issues/818) — original "model gains jointly across income groups".
- Related: [#817](https://github.com/PolicyEngine/policyengine-uk/issues/817) — avoid imputing CG to zero-wealth households.
- Reference implementation: [OG-USA bequest-transmission multivariate KDE](https://pslmodels.github.io/OG-USA/content/api/bequest_transmission.html).
- Reusable infrastructure: the QRF in [`policyengine_uk_data/datasets/imputations/income.py`](https://github.com/PolicyEngine/policyengine-uk-data) and the second-stage QRF plan in [pipeline alignment](./uk-pipeline-alignment-plan.md).
- HMRC, [Capital Gains Tax statistics](https://www.gov.uk/government/collections/capital-gains-tax-statistics) — calibration source.
- ONS, [Wealth and Assets Survey](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/totalwealthingreatbritain/latest) — alternative conditioning source for wealth.
- Existing variables: [`capital_gains_before_response`](../../../policyengine_uk/variables/gov/hmrc/capital_gains_tax/capital_gains_before_response.py), [`capital_gains`](../../../policyengine_uk/variables/household/income/capital_gains.py), [`capital_gains_behavioural_response`](../../../policyengine_uk/variables/gov/hmrc/capital_gains_tax/capital_gains_behavioural_response.py).

# Indirect tax effects of reforms (planned)

```{note}
**Planning page.** PolicyEngine UK already routes ad-hoc indirect-tax
revenue changes through `consumer_incident_tax_revenue_change` at the
household level, but this is a **manual** lever the user has to set via
the `gov.contrib.policyengine.budget.consumer_incident_tax_change`
parameter. There is no automatic pass-through from changes in direct
taxes (e.g. income tax, NI) to consumption-mediated indirect taxes.
This page captures the proposed automation route tracked under
[#1114](https://github.com/PolicyEngine/policyengine-uk/issues/1114).
```

## What this is about

When a direct tax reform changes a household's disposable income, real
households respond by adjusting consumption. That changes the indirect
tax revenue (VAT, excise duties, fuel duty) the household generates.
Right now PolicyEngine UK computes:

1. **Direct effect** — full structural change to income tax / NI / UC /
   etc. given the reform.
2. **Behavioural response on labour supply** — modelled via the
   substitution/income-elasticity machinery at
   `variables/gov/simulation/labour_supply_response/`.
3. **Indirect-tax response** — *not modelled*. Households' consumption
   bundles are read from the dataset and don't shift in response to
   income changes.

UKMOD's *Tax Calculator and Outlook* (TCO) module models this gap with
an aggregate **consumption elasticity of 0.8**: a 1% increase in net
income produces a 0.8% increase in consumption, which then flows
through VAT and excise revenue.

## Scope

### Phase 1 — household-level consumption response

- New parameter `gov/simulation/indirect_tax_response/consumption_elasticity.yaml`
  with the default UKMOD value of 0.8 (cite the source explicitly in
  the metadata).
- New variable `consumption_response_factor` (Household, YEAR) =
  `1 + elasticity * (net_income_change / baseline_net_income)`.
- Apply the factor to each consumption category (`food_and_non_alcoholic_beverages_consumption`,
  `alcohol_and_tobacco_consumption`, `transport_consumption`, etc.) so
  that downstream VAT and excise duty variables pick up the change
  automatically.

### Phase 2 — heterogeneity by category

- A 0.8 economy-wide elasticity hides that some categories (food
  staples, domestic energy) are nearly income-inelastic while others
  (recreation, restaurants) are not. Replace the single
  `consumption_elasticity.yaml` with a per-category set, calibrated to
  ONS *Living Costs and Food Survey* income-elasticity estimates.

### Phase 3 — incidence link

- Today's `consumer_incident_tax_revenue_change` distributes a
  user-specified aggregate across households using consumption shares
  (see
  [`consumer_incident_tax_revenue_change.py`](../../../policyengine_uk/variables/contrib/policyengine/consumer_incident_tax_revenue_change.py)).
  In Phase 3 the variable derives its aggregate **from** the Phase-2
  variables so the user doesn't need to set a separate budget lever.

## Implementation outline

### Variables

- `consumption_response_factor` (Household, YEAR) — Phase 1.
- `disposable_income_change` (Household, YEAR) — difference between
  reform and baseline `household_net_income`. This already exists in
  spirit; expose explicitly.
- Optional `consumption_response_factor_by_category` (Household,
  per-category) — Phase 2.

### Hook points

Each `*_consumption` input variable currently reads straight from the
dataset. Two options for the hook:

1. **Decorate at the input layer**: add `defined_for` /
   `default_formula` that multiplies by `consumption_response_factor`.
   This is clean but ties the consumption inputs to indirect-tax
   modelling.
2. **Insert a derived layer**: keep `*_consumption_baseline` (reads from
   data) and introduce `*_consumption` formulas that apply the response
   factor. This is the safer route — non-indirect-tax users keep the
   pre-reform consumption as `*_consumption_baseline`.

Recommendation: route (2). The dataset-side variable becomes
`*_consumption_baseline`; the response factor is applied at
`*_consumption`.

### Tests

- A reform that drops income tax for low-income households should
  produce a *positive* `consumer_incident_tax_revenue_change` aggregate
  (more take-home pay -> more consumption -> more VAT).
- A reform that raises NI should produce a *negative* aggregate.
- The aggregate should track 0.8 × (sum of net income change × VAT-equivalent rate)
  to within a small tolerance.

## Open questions

- Should the elasticity vary by household income decile? Empirical
  evidence suggests low-income households have higher marginal
  consumption propensity.
- Should saving be modelled explicitly (the residual after consumption)?
  Phase 1 implicitly assumes any income change above the elasticity
  applies to saving.
- How does this interact with the existing labour-supply response so
  we don't double-count?

## References

- UKMOD TCO module documentation (consumption elasticity of 0.8).
- ONS [Living Costs and Food Survey](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/familyspendingintheuk/latest) — income-elasticity calibration source for Phase 2.
- HMRC, [VAT and excise duty receipts statistics](https://www.gov.uk/government/collections/value-added-tax-vat-statistics) — calibration target for the aggregate.
- Existing infrastructure: [`consumer_incident_tax_revenue_change`](../../../policyengine_uk/variables/contrib/policyengine/consumer_incident_tax_revenue_change.py) and the broader `gov/simulation/labour_supply_response/` tree for the parallel labour-supply pattern.
- Related issue: [#1114](https://github.com/PolicyEngine/policyengine-uk/issues/1114).

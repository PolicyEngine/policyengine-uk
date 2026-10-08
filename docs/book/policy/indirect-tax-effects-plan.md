# Indirect tax effects of reforms (planned)

```{note}
**Planning page.** PolicyEngine UK already routes ad-hoc indirect-tax
revenue changes through `consumer_incident_tax_revenue_change` at the
household level, but this is a **manual** lever the user has to set via
the `gov.contrib.policyengine.budget.consumer_incident_tax_change`
parameter. There is no automatic pass-through from changes in direct
taxes (e.g. income tax, NI) to consumption-mediated indirect taxes.
This page sets out a proposed automatic route, tracked in
[#1114](https://github.com/PolicyEngine/policyengine-uk/issues/1114) (still
open, October 2026).
```

## What this is about

When a direct tax reform changes a household's disposable income, real
households respond by adjusting consumption. That changes the indirect
tax revenue (VAT, excise duties, fuel duty) the household generates.
Right now PolicyEngine UK computes:

1. **Direct effect** — full structural change to income tax / NI / UC /
   etc. given the reform.
2. **Behavioural response on labour supply** — modelled with the
   substitution and income elasticities under
   `gov.simulation.labour_supply_responses` (`policyengine_uk/dynamics/labour_supply.py`,
   `employment_income_behavioral_response`).
3. **Indirect-tax response** — *not modelled*. Households' consumption
   bundles are read from the dataset and don't shift in response to
   income changes.

#1114 reports that UKMOD handles this with an aggregate **consumption
elasticity of 0.8**: a 1% rise in net income gives a 0.8% rise in
consumption, which then flows through VAT and excise revenue. That figure
has not yet been checked against UKMOD's own documentation, so it needs a
primary source before it is used as a default.

## Scope

### Phase 1 — household-level consumption response

- New parameter `gov/simulation/indirect_tax_response/consumption_elasticity.yaml`,
  defaulting to 0 (no response) until a sourced value such as UKMOD's is
  confirmed and cited in its metadata.
- New variable `consumption_response_factor` (Household, YEAR) =
  `1 + elasticity * (net_income_change / baseline_net_income)`.
- Apply the factor to the twelve COICOP categories that `consumption`
  adds up (`food_and_non_alcoholic_beverages_consumption`,
  `alcohol_and_tobacco_consumption`, `transport_consumption` and so on).
  VAT reads `consumption` (through `full_rate_vat_consumption` and
  `reduced_rate_vat_consumption`), so it picks up the change.
- The duties do not read those categories. Fuel duty reads
  `petrol_litres` and `diesel_litres`, and alcohol duty reads the
  `*_litres` inputs under `variables/input/consumption/alcohol/`. They
  need the same factor applied to their quantity inputs.

### Phase 2 — heterogeneity by category

- A single economy-wide elasticity hides that some categories (food
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
- The aggregate should track elasticity × (sum of net income change × VAT-equivalent rate)
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

- UKMOD documentation, to confirm the 0.8 consumption elasticity reported in #1114 (not yet checked).
- ONS [Living Costs and Food Survey](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/bulletins/familyspendingintheuk/latest) — income-elasticity calibration source for Phase 2.
- HMRC, [VAT annual statistics](https://www.gov.uk/government/statistics/value-added-tax-vat-annual-statistics) — calibration target for the aggregate.
- Existing infrastructure: [`consumer_incident_tax_revenue_change`](../../../policyengine_uk/variables/contrib/policyengine/consumer_incident_tax_revenue_change.py) and the broader `gov/simulation/labour_supply_response/` tree for the parallel labour-supply pattern.
- Related issue: [#1114](https://github.com/PolicyEngine/policyengine-uk/issues/1114).

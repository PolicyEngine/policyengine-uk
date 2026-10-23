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

1. **Direct effect**: the full structural change to income tax, NI, UC
   and so on under the reform.
2. **Behavioural response on labour supply**: available through two
   separate routes. `employment_income_behavioral_response` applies the
   substitution and income elasticities under
   `gov.simulation.labour_supply_responses` (both 0 by default).
   Separately, `Simulation.apply_dynamics`
   (`policyengine_uk/dynamics/labour_supply.py`) applies the OBR's
   elasticities by demographic group when
   `gov.dynamic.obr_labour_supply_assumptions` is true.
3. **Indirect-tax response**: *not modelled*. Households' consumption
   bundles are read from the dataset and don't shift in response to
   income changes.

#1114 suggests that UKMOD handles this in its indirect taxation (TCO)
extension with a consumption elasticity of 0.8, citing only a ChatGPT
conversation. UKMOD's own
[TCO technical note](https://www.microsimulation.ac.uk/wp-content/uploads/2026/01/TCO-extension-v3.pdf)
(revised October 2025) does not give 0.8. It describes three alternative
assumptions: constant income shares (an income elasticity of +1 for every
commodity), constant expenditure shares (nominal savings held fixed, so the
whole change in disposable income goes to spending) and constant quantities
(an income elasticity of 0). Any default therefore needs another primary
source.

## Scope

### Phase 1: household-level consumption response

- New parameter `gov/simulation/indirect_tax_response/consumption_elasticity.yaml`,
  defaulting to 0 (no response) until a sourced value is confirmed and
  cited in its metadata.
- New variable `consumption_response_factor` (Household, YEAR) =
  `1 + elasticity * (net_income_change / baseline_net_income)`.
- Apply the factor to the twelve COICOP categories that `consumption`
  adds up (`food_and_non_alcoholic_beverages_consumption`,
  `alcohol_and_tobacco_consumption`, `transport_consumption` and so on).
  VAT reads `consumption` (through `full_rate_vat_consumption` and
  `reduced_rate_vat_consumption`), so it picks up the change.
- The duties do not read those categories. Fuel duty reads
  `petrol_litres` and `diesel_litres`, which divide the `petrol_spending`
  and `diesel_spending` inputs by pump prices, and the `lpg_kg` and
  `natural_gas_kg` inputs. Alcohol duty reads the
  `*_litres` inputs under `variables/input/consumption/alcohol/`, and
  tobacco duty reads `cigarettes_per_week` and the `*_grams_per_week`
  inputs under `variables/input/consumption/tobacco/`. The same factor
  needs to be applied to those spending and quantity inputs.

### Phase 2: heterogeneity by category

- A single economy-wide elasticity hides that some categories (food
  staples, domestic energy) are less income-elastic than others
  (recreation, restaurants). Replace the single
  `consumption_elasticity.yaml` with a per-category set, calibrated to
  income elasticities estimated from the ONS *Living Costs and Food
  Survey*.

### Phase 3: incidence link

- Today's `consumer_incident_tax_revenue_change` distributes a
  user-specified aggregate across households using consumption shares
  (see
  [`consumer_incident_tax_revenue_change.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/contrib/policyengine/consumer_incident_tax_revenue_change.py)).
  In Phase 3 the variable derives its aggregate **from** the Phase-2
  variables so the user doesn't need to set a separate budget lever.

## Implementation outline

### Variables

- `consumption_response_factor` (Household, YEAR), Phase 1.
- `disposable_income_change` (Household, YEAR): the difference between
  reform and baseline `household_net_income`. The labour-supply module
  already computes a clipped relative version of this per person
  (`relative_income_change`, under
  `variables/gov/simulation/labour_supply_response/`); Phase 1 needs a
  household-level version in pounds.
- Optional `consumption_response_factor_by_category` (Household,
  per category), Phase 2.

### Hook points

Each `*_consumption` input variable currently reads straight from the
dataset. Two options for the hook:

1. **Decorate at the input layer**: give each input a formula that
   multiplies by `consumption_response_factor`. This ties the consumption
   inputs to indirect-tax modelling, and policyengine-core does not run a
   formula for a period the dataset already supplies, so it would not
   change dataset values.
2. **Insert a derived layer**: keep `*_consumption_baseline` (reads from
   data) and introduce `*_consumption` formulas that apply the response
   factor. This is the safer route: users who do not need the indirect
   tax response keep the pre-reform consumption as
   `*_consumption_baseline`.

Recommendation: route (2). The dataset-side variable becomes
`*_consumption_baseline`; the response factor is applied at
`*_consumption`.

### Tests

- Once Phase 3 derives `consumer_incident_tax_revenue_change` from the
  response, a reform that drops income tax for low-income households should
  produce a *positive* aggregate (more take-home pay -> more consumption ->
  more VAT). Today the variable's weighted aggregate always equals the
  `consumer_incident_tax_change` parameter.
- A reform that raises NI should produce a *negative* aggregate.
- The aggregate should track elasticity × (sum of net income change × VAT-equivalent rate)
  to within a small tolerance.

## Open questions

- Should the elasticity vary by household income decile, for example if
  lower-income households spend a larger share of extra income?
- Should saving be modelled explicitly (the residual after consumption)?
  Phase 1 implicitly assumes that whatever part of an income change is not
  consumed (a share of 1 − elasticity × consumption / net income) is
  saved.
- How does this interact with the existing labour-supply response so
  we don't double-count?

## References

- UKMOD, [Indirect Taxation (TCO) Extension technical note](https://www.microsimulation.ac.uk/wp-content/uploads/2026/01/TCO-extension-v3.pdf) (revised October 2025): its three expenditure assumptions; it does not give the 0.8 reported in #1114.
- ONS, [Family spending in the UK](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/bulletins/familyspendingintheuk/latest) (Living Costs and Food Survey): expenditure data from which Phase 2 income elasticities would be estimated.
- HMRC, [VAT annual statistics](https://www.gov.uk/government/statistics/value-added-tax-vat-annual-statistics): calibration target for the aggregate.
- Existing infrastructure: [`consumer_incident_tax_revenue_change`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/contrib/policyengine/consumer_incident_tax_revenue_change.py) and the `gov/simulation/labour_supply_responses/` parameter tree for the parallel labour-supply pattern.
- Related issue: [#1114](https://github.com/PolicyEngine/policyengine-uk/issues/1114).

# Cost-of-Living Payments and Energy Bills Rebate

In response to the 2021-23 cost-of-living crisis the UK government
announced two distinct one-off support packages. Both are modelled in
PolicyEngine UK under `gov.treasury.*` and feed into household net
income via [`gov_spending`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/gov_spending.py)
and the HBAI benefit aggregates.

## Energy Bills Rebate (winter 2022)

Announced by the Chancellor in February 2022 to help households with the
spike in domestic energy prices. Two strands:

- **£150 Council Tax Rebate** for households in Council Tax bands A–D in
  England, paid in April 2022. Equivalent payments were made by the
  devolved administrations.
- **£200 Energy Bills Credit** delivered via energy suppliers to all
  domestic electricity customers from October 2022. Originally announced
  as a repayable loan, the repayment requirement was scrapped at the May
  2022 emergency support package.

PolicyEngine models these via:

- `energy_bills_rebate` (Household, YEAR) = `ebr_council_tax_rebate` +
  `ebr_energy_bills_credit`
- Parameters at `parameters/gov/treasury/energy_bills_rebate/`:
  - `energy_bills_credit.yaml` — the £200 flat household amount
  - `council_tax_rebate/bands.yaml` — qualifying CT bands (A–D)
  - `council_tax_rebate/amount.yaml` — the £150 rebate amount

## Household Energy Payment (2026-27)

Budget 2026 (paragraph 6.24) announced a one-off £100 Household Energy
Payment for households in council tax bands A to D in England, which local
authorities pay into bank accounts from January 2027. PolicyEngine models it as
`household_energy_payment` (Household, YEAR), with parameters at
`parameters/gov/treasury/household_energy_payment/`:

- `amount.yaml`: £100 in model year 2026 (6 April 2026 to 5 April 2027),
  zero otherwise
- `bands.yaml`: qualifying bands (A to D)
- `countries.yaml`: qualifying countries (England)

It counts in `household_benefits` and `gov_spending`, as the Energy Bills
Rebate does, and in `hbai_household_net_income`: HBAI counted the 2022
Council Tax Rebate and the Energy Bills Support Scheme as miscellaneous
income ([HBAI quality and methodology report FYE 2023](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2023/households-below-average-income-series-quality-and-methodology-information-report-fye-2023)).
The devolved governments receive a Barnett share instead, which the model
does not allocate, and the model leaves out the £100 million of further
local-authority funding for targeted support.

The payment goes to the householder [liable for council tax on their main
home](https://www.gov.uk/government/news/what-the-autumn-budget-2026-means-for-your-energy-bills),
including most households exempt from council tax; full criteria are to
follow. The model pays every household in a qualifying band. Survey data
hold only main homes, so the second homes and empty properties the scheme
excludes do not arise. The model can't tell which households have a
landlord liable for council tax (council tax in the rent), so it pays them,
which slightly overstates recipients. `council_tax_band` defaults to band D, so a household with no
band recorded qualifies.

## Cost-of-Living Payments (2022-23 and 2023-24)

Two successive packages, both modelled through the variable
`cost_of_living_support_payment` at `gov/treasury/cost_of_living_support/`.
The variable returns the **sum** of three independent strands depending
on which qualifying benefits the household receives:

| Strand | 2022-23 | 2023-24 | Qualifying benefits |
|--------|---------|---------|---------------------|
| Means-tested CoL Payment | £650 (two instalments) | £900 (three instalments) | Universal Credit, Pension Credit, Housing Benefit, income-based JSA / ESA, Income Support |
| Pensioner CoL Payment    | £300 | £300 | Winter Fuel Payment recipients |
| Disability CoL Payment   | £150 | £150 | DLA, PIP, Attendance Allowance, AFCS, IIDB, SDA, child / war disability pension |

From 2024-01-01 the parameter values are explicitly reset to zero so the
one-off doesn't extrapolate forward.

### How PolicyEngine computes the payment

For each strand `s ∈ {means_tested_households, pensioners, disabled}`:

```
on_s = (sum of household's reported amounts in s.qualifying_benefits) > 0
strand_s = s.amount(period) * on_s
```

Total `cost_of_living_support_payment = means_test_bonus + pensioner_bonus + disabled_bonus`,
i.e. the strands stack — a pensioner on Pension Credit who also receives PIP
will collect all three payments. This matches the actual policy.

## References

- [HMT/DWP, May 2022 cost-of-living support package announcement](https://www.gov.uk/government/news/millions-of-most-vulnerable-households-will-receive-1200-of-help-with-cost-of-living)
- DWP, [Cost-of-Living Payments 2023-24 guidance](https://www.gov.uk/guidance/cost-of-living-payments-2023-to-2024) (means-tested, pensioner and disability strands).
- HMT, [Energy Bills Support Scheme](https://www.gov.uk/government/publications/the-energy-bills-support-scheme-explainer) and [Council Tax Energy Rebate](https://www.gov.uk/government/publications/the-council-tax-rebate-2022-23-billing-authority-guidance).
- House of Commons Library briefing [CBP-9501 — Cost of Living Payments and the energy crisis](https://commonslibrary.parliament.uk/research-briefings/cbp-9501/).

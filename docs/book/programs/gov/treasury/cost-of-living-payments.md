# Cost-of-Living Payments and Energy Bills Rebate

In response to the 2021-23 cost-of-living crisis the UK government
announced two distinct one-off support packages. Both are modelled in
PolicyEngine UK under `gov.treasury.*` and count in household net income
and in [`gov_spending`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/gov_spending.py).
Both also count in HBAI household net income, the income behind the poverty
statistics, though under different HBAI headings (see below).

## Energy Bills Rebate (winter 2022)

Announced by the Chancellor in February 2022 to help households with the
spike in domestic energy prices. Two strands:

- **£150 Council Tax Rebate** for households in Council Tax bands A–D in
  England, a one-off in 2022-23. Households qualified on their band on 1
  April 2022. The guidance asked billing authorities to pay from April and
  set 30 September 2022 as the deadline for the payments the government
  would reconcile (paragraph 7). Scotland and Wales paid their own £150
  awards to bands A–D, and also to Council Tax Reduction recipients in any
  band, which the model leaves out. Northern Ireland levies domestic rates,
  not council tax, and had no Council Tax Rebate, so the model pays none
  there whatever the household's council tax band (the enhanced FRS gives
  every Northern Ireland household band A, the default policyengine-uk-data
  assigns when the FRS records no band).
- **Energy Bills Support Scheme**, a £400 discount on domestic electricity
  bills in Great Britain, paid in six monthly instalments from October 2022
  to March 2023 (£66 for two months, then £67). Announced in February 2022
  as a repayable £200, it became a £400 grant in the May 2022 support
  package. Northern Ireland paid £600 in one go from January 2023: £400 of
  support and a £200 Alternative Fuel Payment, to each domestic electricity
  customer on 2 January 2023, whatever fuel the household heats with (EBSS
  AFP NI Direction, 23 December 2022, paragraph 3 and footnote 1). The model
  leaves out Great Britain's £200 Alternative Fuel Payment, which suppliers
  paid on electricity meters the government listed in areas off the gas grid.

PolicyEngine models these via:

- `energy_bills_rebate` (Household, YEAR) = `ebr_council_tax_rebate` +
  `ebr_energy_bills_credit` + `ebr_alternative_fuel_payment`
- Parameters at `parameters/gov/treasury/energy_bills_rebate/`:
  - `energy_bills_credit_monthly.yaml` — the Great Britain monthly
    instalments
  - `energy_bills_credit_northern_ireland.yaml` — the Northern Ireland
    £400 in January 2023
  - `alternative_fuel_payment_northern_ireland.yaml` — the Northern Ireland
    £200 Alternative Fuel Payment, paid with the £400
  - `energy_bills_credit.yaml` — a yearly top-up, zero by default, kept for
    reforms
  - `council_tax_rebate/bands.yaml` — qualifying CT bands (A–D)
  - `council_tax_rebate/amount.yaml` — £150 in 2022-23 and nothing in any
    other year

`ebr_energy_bills_credit` sums the monthly instalments within each calendar
year, so a Great Britain household on the scheme throughout gets £199 in
2022 and £201 in 2023, while HBAI counts the whole £400 in 2022-23. Each
month takes the scheme of the household's `country` in that calendar year.
A situation that sets Northern Ireland for 2022 only therefore gets the
Great Britain credit from January to March 2023, and no Alternative Fuel
Payment, because `country` is not carried forward and defaults to England.

HBAI classifies both strands as miscellaneous income, not state support,
and DWP imputes receipt because the FRS did not ask about them. So
`energy_bills_rebate` is in `hbai_household_net_income` but not in
`hbai_benefits`. No FRS income field behind `miscellaneous_income` holds
the rebates, so the model counts them once.

HBAI income takes the same calendar-year sum as household net income and
government spending. A Great Britain household in bands A to D on the
scheme throughout gets £349 in 2022 and £201 in 2023, where HBAI counts
£550 in 2022-23. A Northern Ireland household gets nothing in 2022 and £600
in 2023, though its main rollout began on 16 January 2023, in 2022-23.
The direction set 31 March 2023 as the normal deadline for providing it, and
let suppliers reissue vouchers and cheques that customers could redeem until
30 June 2023 (paragraph 12(b)). Summing the
credit by financial year would move all three measures together. `epg_subsidy` sums the Energy Price Guarantee by
calendar year in the same way; it counts in household net income and
government spending but not in HBAI income. The model keeps one timing for
both schemes for now.

### Great Britain's Alternative Fuel Payment

Electricity suppliers in Great Britain paid £200 to 1,842,760 customers,
£368.6 million in all ([DESNZ supplier data](https://www.gov.uk/government/publications/alternative-fuel-payment-gb-payments-made-by-electricity-suppliers-to-customers)),
and local authorities paid 89,750 more through the Alternative Fund
([DESNZ applications data](https://www.gov.uk/government/publications/energy-bills-support-scheme-alternative-fund-gb-ni-and-alternative-fuel-payment-alternative-fund-applications-made-by-customers)).
The model leaves out both, so it understates 2023 income and government
spending by about £387 million. The omission affects 2023 alone.

Suppliers paid whoever held the account, at the start of 1 February 2023, for
each electricity meter the Secretary of State named ([direction](https://assets.publishing.service.gov.uk/media/63ceba6fe90e071bac7eadce/alternative-fuels-payment-gb-ministerial-direction.pdf),
paragraph 6). The department built that list from postcodes not connected to
the gas grid and removed areas with high use of electric heating
([interim evaluation](https://www.gov.uk/government/publications/domestic-energy-affordability-support-schemes-in-great-britain-interim-evaluation),
page 54).

Spending on liquid and solid fuels does not pick out the households on that
list. In the Living Costs and Food Survey, about a third of Great Britain
households buying these fuels have gas central heating, and more than a third
of households with oil, solid fuel, calor gas or other gas central heating
report no purchase. The enhanced FRS 2023-24 carries neither
`liquid_fuel_consumption` nor
`solid_fuel_consumption`. PolicyEngine's Microcosm dataset carries both from
2024, and its 842,000 Great Britain households with spending on either fall 54%
short of DESNZ's count. None of the model's datasets with a 2023 year records a
household's heating fuel or gas connection.

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
which slightly overstates recipients. `council_tax_band` defaults to band D,
so a household whose survey record has no band qualifies.

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
- DWP, [HBAI quality and methodology information report, FYE 2023](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2023/households-below-average-income-series-quality-and-methodology-information-report-fye-2023) (treatment of the cost-of-living support schemes in HBAI income).
- House of Commons Library briefing [CBP-9501 — Cost of Living Payments and the energy crisis](https://commonslibrary.parliament.uk/research-briefings/cbp-9501/).

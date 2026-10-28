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
  England, a one-off in 2022-23. Eligibility was fixed on 1 April 2022 and
  billing authorities made every payment by 30 September 2022. Equivalent
  payments were made by the devolved administrations.
- **Energy Bills Support Scheme**, a £400 discount on domestic electricity
  bills in Great Britain, paid in six monthly instalments from October 2022
  to March 2023 (£66 for two months, then £67). Announced in February 2022
  as a repayable £200, it became a £400 grant in the May 2022 support
  package. Northern Ireland paid £400 in one go in January 2023, alongside
  a £200 Alternative Fuel Payment that the model does not include.

PolicyEngine models these via:

- `energy_bills_rebate` (Household, YEAR) = `ebr_council_tax_rebate` +
  `ebr_energy_bills_credit`
- Parameters at `parameters/gov/treasury/energy_bills_rebate/`:
  - `energy_bills_credit_monthly.yaml` — the Great Britain monthly
    instalments
  - `energy_bills_credit_northern_ireland.yaml` — the Northern Ireland
    payment in January 2023
  - `energy_bills_credit.yaml` — a yearly top-up, zero by default, kept for
    reforms
  - `council_tax_rebate/bands.yaml` — qualifying CT bands (A–D)
  - `council_tax_rebate/amount.yaml` — £150 in 2022-23 and nothing in any
    other year

`ebr_energy_bills_credit` sums the monthly instalments within each calendar
year, so a Great Britain household on the scheme throughout gets £199 in
2022 and £201 in 2023. `energy_bills_rebate`, its sum with the Council Tax
Rebate, counts in household net income and government spending that way.

HBAI counts both strands by financial year, all in FYE 2023, and classifies
them as miscellaneous income, not state support; DWP imputes receipt
because the FRS did not ask about them. So `hbai_household_net_income` adds
`hbai_energy_bills_rebate`, which sums the credit from April of the year to
the next March: the whole £400 (Northern Ireland's January 2023 payment
included) in 2022-23 and nothing in 2023-24. It is not in `hbai_benefits`.
No FRS income field behind `miscellaneous_income` holds the rebates, so
they are not counted twice.

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

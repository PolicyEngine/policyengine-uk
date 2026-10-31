# Company car and car fuel benefits

A car an employer makes available for an employee's private use is a
benefit in kind: its cash equivalent is taxed as employment income
([ITEPA 2003 s. 120][s120]), and so is fuel provided for its private use
([s. 149][s149]). The employer pays Class 1A National Insurance on both
([SSCBA 1992 s. 10][sscba10]). The model calculates both benefits from
2020-21.

## Inputs

Each person can have one company car. The inputs default to no car, so a
simulation that sets none of them is unchanged.

| Input | Meaning |
| --- | --- |
| `company_car_list_price` | List price of the car and its accessories; zero means no company car |
| `company_car_capital_contributions` | Capital sums the employee has contributed, this year and earlier |
| `company_car_co2_emissions` | CO2 emissions figure in g/km (0 for a car that cannot emit CO2) |
| `company_car_electric_range` | Electric range figure in miles |
| `company_car_fuel_type` | Fuel type (the `CarFuelType` enum also used for vehicle excise duty) |
| `company_car_registered_from_6_april_2020` | First registered on or after 6 April 2020 (matters in 2020-21 and 2021-22 only) |
| `company_car_availability` | Share of the tax year the car is available (default 1) |
| `company_car_private_use_payments` | Payments for private use |
| `company_car_private_fuel_provided` | Fuel provided for private use and not made good in full |

The `car_*` inputs describe the person's own car for vehicle excise duty
and play no part here.

Data that fills these inputs needs to know three things:

- **Set the CO2 figure with the list price.** The model cannot tell a
  missing figure from 0 g/km, so a car with a list price and no CO2 figure is
  taxed at the zero-emission rate. A car of the `ELECTRIC` fuel type is taken
  to emit 0 g/km whatever figure is entered.
- **Keep the benefits out of pay.** `employment_income` must not also hold
  them, or they are taxed twice and wrongly bear employee NICs. The SPI's
  EPB (expenses payments and benefits in kind) includes them, so a dataset
  that adds EPB to pay, as policyengine-uk-data's SPI records do, must take
  the car and car fuel benefits out of it.
- **Projected years.** The list price, capital contributions and payments
  for private use grow with CPI when a dataset is projected to later years.
  CPI stands in for a new-car price index, which the OBR does not forecast.

## Calculation

`company_car_appropriate_percentage` applies [s. 139][s139]: a rate for
0 g/km, rates for 1 to 50 g/km by electric range (one rate from 2028-29),
a rate for each band from 51-54 to 70-74 g/km (65-74 g/km from 2028-29),
and from 75 g/km a base rate plus one point for each full 5 g/km, up to the
maximum. A diesel car not meeting the Euro 6d (RDE2) standard adds 4 points,
within the maximum ([s. 141][s141]); a car that cannot emit CO2 takes no
supplement. In 2020-21 and 2021-22 a car first registered on or after
6 April 2020 takes the lower rates of s. 139A (Finance Act 2020 ss. 9 and
10). The appropriate percentage is zero for a person without a company car
(`has_company_car`).

`company_car_benefit` follows the steps of [s. 121][s121]: the price, less
capital contributions up to £5,000, times the appropriate percentage,
reduced in proportion to the days the car is unavailable, less payments for
private use, and never below zero. `car_fuel_benefit` is the appropriate
percentage of the car fuel benefit charge multiplier ([s. 150][s150]),
reduced in proportion to the days the car is unavailable. It is nil for a
car that cannot emit CO2. `benefits_in_kind` adds the two.

## Where the benefits go

- **Income tax.** `taxable_employment_income` adds `benefits_in_kind`, so the
  benefits reach income tax, at Scottish rates for a Scottish taxpayer, and
  adjusted net income: the personal allowance taper, the High Income Child
  Benefit Charge, and the £100,000 limits of Tax-Free Childcare and the
  extended childcare entitlement. They count as relevant UK earnings for the
  limit on pension tax relief (HMRC PTM044100).
- **Not student loan income.** Student loan repayments and the Plan 2
  interest rate leave the benefits out: Self Assessment excludes Chapter 6
  car benefits ([SI 2009/470 reg. 29(4)(e)][sl29]), and PAYE deducts
  repayments from Class 1 earnings (reg. 41).
- **Not earnings for Class 1 or the means tests.** The benefits are not in
  `employment_income` or `employment_benefits`, so employee Class 1 NICs and
  the earnings of Universal Credit ([UC Regulations 2013 reg. 55(2)(a)][uc55]),
  Housing Benefit (HB Regulations 2006 reg. 35(2)(a)) and Council Tax
  Reduction leave them out. Those tests still deduct the income tax on them,
  which is tax paid in respect of the employment (reg. 55(5)(b)) and which
  PAYE collects from pay. Universal Credit takes earnings as the lowest slice
  of income, so it deducts all of that tax. Housing Benefit and Council Tax
  Reduction deduct earnings' share of the person's tax, and count the
  benefits with pay in that share; with other income, part of the tax on the
  benefits falls on the other income, as part of the tax on pay does. The
  Childcare Offer for Wales's gross income lists its sources one by one, and
  benefits in kind are not among them.
- **Employer National Insurance.** `ni_class_1a` is the Class 1A percentage
  of `benefits_in_kind`, and `ni_employer` adds it to secondary Class 1, so it
  reaches `gov_tax`. The Class 1A percentage is the secondary percentage for
  the year, except 14.53% in 2022-23.
- **No household bears Class 1A.** `employer_cost`, and the employer NI
  incidence variables that recompute it, cover pay and secondary Class 1
  only. So the fixed-cost pay response and the capital and consumer
  channels leave out Class 1A and any change in it: it stays with employers
  as revenue. A reform that changes Class 1A, such as the 2030-31 rise below
  or a rise in the employer rate, raises `gov_tax` by more than it lowers
  household incomes. Passing Class 1A through like secondary Class 1 is
  [#2752](https://github.com/PolicyEngine/policyengine-uk/issues/2752).

## 2030-31

Finance Act 2025 s. 6 sets the rates for 2029-30 and subsequent tax years,
so the baseline keeps them for 2030-31: 9% for 0 g/km, 19% for 1 to 50 g/km
and a 39% maximum. Budget 2026 raises every rate for 2030-31 by one point, to
a maximum of 40%, to be legislated in Finance Bill 2026-27. The
`company_car_tax_rise_2030` scenario applies that rise:

```python
from policyengine_uk import Simulation
from policyengine_uk.scenarios import company_car_tax_rise_2030

reformed = Simulation(situation=situation, scenario=company_car_tax_rise_2030)
```

`policyengine_uk.scenarios.company_car_tax_rise_2030.COMPANY_CAR_TAX_RISE_2030`
holds the same changes as a parameter-changes dictionary.

The car fuel benefit charge multiplier is in the baseline for 2027-28 at the
£30,200 Budget 2026 announced, before the Treasury order is made. That is the
annual CPI uprating, which the Budget does not score, so a pre-Budget
baseline has it too; the 2030-31 rise is a policy decision Budget 2026 scores
(Table 6.1, row 86). The fuel part of the rise depends on the multiplier.

## Not modelled

- Vans and van fuel (ITEPA 2003 s. 154 onwards).
- Optional remuneration arrangements (s. 120A), shared cars (s. 148) and
  pool cars (s. 167).
- Classic cars (s. 147), cars without a CO2 emissions figure (s. 140) and
  cars first registered before 1 January 1998 (s. 142).
- Fuel provided for only part of the year (s. 152(2)).
- Other benefits in kind.

The survey data does not fill these inputs yet, so a population run scores
the company car benefits at zero until a dataset does.

[s120]: https://www.legislation.gov.uk/ukpga/2003/1/section/120
[s121]: https://www.legislation.gov.uk/ukpga/2003/1/section/121
[s139]: https://www.legislation.gov.uk/ukpga/2003/1/section/139
[s141]: https://www.legislation.gov.uk/ukpga/2003/1/section/141
[s149]: https://www.legislation.gov.uk/ukpga/2003/1/section/149
[s150]: https://www.legislation.gov.uk/ukpga/2003/1/section/150
[sscba10]: https://www.legislation.gov.uk/ukpga/1992/4/section/10
[sl29]: https://www.legislation.gov.uk/uksi/2009/470/regulation/29
[uc55]: https://www.legislation.gov.uk/uksi/2013/376/regulation/55

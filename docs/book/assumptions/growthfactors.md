# Economic assumptions

```{note}
We project economic variables using year-over-year growth rates stored in `parameters/gov/economic_assumptions/yoy_growth.yaml`. We generate index values from these rates to update household variables. We source all values from the OBR's long-term economic determinants and Economic and Fiscal Outlook ([October 2026](https://obr.uk/efo/economic-and-fiscal-outlook-october-2026/)) unless we specify otherwise. The long-term determinants provide extended forecasts beyond the standard forecast horizon.
```

## Consumer price index

```{important}
We use the OBR's CPI projections to drive most benefit and consumption variables.
```

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 9.1% | 7.3% | 2.5% | 3.4% | 3.1% | 3.4% | 2.1% | 2.1% | 2.0% | 2.0% |

We apply CPI to these variables:
- All reported benefits– `carers_allowance_reported`, `child_benefit_reported`, `child_tax_credit_reported`, `esa_contrib_reported`, `esa_income_reported`, `housing_benefit_reported`, `iidb_reported`, `incapacity_benefit_reported`, `income_support_reported`, `jsa_contrib_reported`, `jsa_income_reported`, `maternity_allowance_reported`, `pension_credit_reported`, `sda_reported`, `state_pension_reported`, `universal_credit_reported`, `winter_fuel_allowance_reported`, `working_tax_credit_reported`
- All consumption categories EXCEPT energy– `alcohol_and_tobacco_consumption`, `clothing_and_footwear_consumption`, `communication_consumption`, `education_consumption`, `food_and_non_alcoholic_beverages_consumption`, `health_consumption`, `household_furnishings_consumption`, `housing_water_and_electricity_consumption`, `miscellaneous_consumption`, `recreation_consumption`, `restaurants_and_hotels_consumption`, `transport_consumption`

`domestic_energy_consumption`, `electricity_consumption` and `gas_consumption` are deliberately excluded. The data build calibrates them to NEED mean kWh and converts to pounds at Ofgem Q2 2026 unit rates, so the stored values already carry FY26/27 price levels; uprating them from the dataset's data year would re-apply price changes that are already included. See PolicyEngine/policyengine-uk#1867. `liquid_fuel_consumption` and `solid_fuel_consumption` (heating oil, LPG, coal and wood) are not covered by Ofgem's price cap, so they are CPI-uprated from the data year like other LCFS spending.

- Other variables– `afcs_reported`, `bsp_reported`, `childcare_expenses`, `free_school_fruit_veg`, `free_school_meals`, `free_school_milk`, `maintenance_expenses`, `statutory_maternity_pay`, `statutory_paternity_pay`, `statutory_sick_pay`, `state_pension`, `war_widows_pension_reported`, `widowed_parents_allowance_reported`

`bsp_reported` stays nominally flat when a dataset explicitly supplies both
`war_widows_pension_reported` and `widowed_parents_allowance_reported` in
the same source year, including all-zero columns. Datasets with either
column missing and household situations retain CPI uprating. See the
[bereavement-benefit split guide](https://github.com/PolicyEngine/policyengine-uk/blob/main/docs/engineering/skills/dataset-sources.md#bereavement-benefit-split).

## Road fuel volume

We use HMRC road-fuel clearances and OBR-implied forecast volumes for petrol and diesel spending, because PolicyEngine converts these spending fields into litres by dividing by pump prices.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 6.3% | -0.6% | -0.1% | -1.3% | -2.3% | -3.1% | -3.1% | -4.0% | -5.4% | -6.5% |

We apply this to: `diesel_spending`, `petrol_spending`

The pump prices that turn spending into litres (`household.consumption.fuel.prices.petrol` and `.diesel`) are DESNZ calendar-year averages (Quarterly Energy Prices tables 4.1.1 and 4.1.2), the same basis Microcosm UK uses to price household fuel spending. The spending growth rates (`petrol_spending_litre_proxy`, `diesel_spending_litre_proxy`) are derived from those prices, so that weighted litres follow the volume path above: (1 + growth) = (1 + volume growth) × price<sub>t</sub> / price<sub>t−1</sub> ÷ (1 + population growth). Whenever the prices change, re-derive the growth rates; a test checks that they match.

## Benefit uprating (September CPI)

Most benefit rates rise each April by the CPI 12-month rate for the
September before, as in the annual review under Social Security
Administration Act 1992 s150 ([written statement HCWS1101](https://questions-statements.parliament.uk/written-statements/detail/2025-11-26/hcws1101):
3.8% for April 2026). Published September figures come from ONS series D7G7
(3.5% for September 2026, which sets April 2027); later years use the OBR's
September CPI forecast and, after the EFO horizon, calendar-year CPI. Each
figure is rounded to 0.1 percentage points, and a fall in prices leaves rates
unchanged. Parameters with `uprating: gov.benefit_uprating_cpi` rise by these
rates after their last published value.

## Average earnings

```{note}
We apply the OBR's wage growth forecasts to employment-related variables.
```

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 6.1% | 6.2% | 5.1% | 4.1% | 3.7% | 3.0% | 2.1% | 2.3% | 2.5% | 2.6% |

We use average earnings for these variables: `employee_pension_contributions`, `employer_pension_contributions`, `employment_income`, `employment_income_before_lsr`, `personal_pension_contributions`, `student_loan_repayments`

### Newly assigned student loan plans

Dataset projection holds ages fixed, so a person of a given age represents a
later university intake in each projected year. When projection adds a loan
to a tertiary-educated person without one, it uses current household region
as a proxy for the funding nation, because the dataset does not record the
funding agency. This proxy cannot identify people who moved between nations.

The [official repayment-plan rules](https://www.gov.uk/repaying-your-student-loan/which-repayment-plan-you-are-on)
give SAAS borrowers Plan 4 and Student Finance Northern Ireland borrowers
Plan 1. For undergraduate loans, England uses Plan 1 before the 2012 intake,
Plan 2 for 2012–2022, and Plan 5 from 2023; Wales uses Plan 1 before 2012 and
Plan 2 from 2012. New assignments follow these routes; an unknown region
leaves the person without an assigned loan. New holders from the 2023 and
later intakes are added only in England: Plan 5 is the only plan that did not
exist in the base year, while the other nations' plans for those intakes are
already in the data. Plan 1 loans first paid before September 2006 (the 2005
and earlier intakes) are written off at 65, later ones about 29 years after
the course started. Take-up remains a fixed 40%
probability with a draw keyed on person ID. This funding-nation routing
applies to newly assigned loans; the existing-holder relabelling and
write-off approximations are unchanged.

## Lagged average earnings

We lag earnings growth by one year and use that to uprate housing service charges (including ground rent).

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 5.9% | 6.1% | 6.2% | 5.1% | 4.1% | 3.7% | 3.0% | 2.1% | 2.3% | 2.5% |

## Per capita GDP

We derive these rates as calendar-year nominal GDP growth from the OBR's October 2026 EFO divided by population growth: (1 + GDP growth) / (1 + population growth) − 1.

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 10.0% | 5.2% | 4.0% | 4.6% | 4.0% | 3.1% | 3.4% | 3.6% | 3.4% | 3.3% |

We use per capita GDP for these variables: `benunit_reported_capital`, `capital_gains`, `capital_gains_badr`, `capital_gains_before_response`, `capital_gains_carried_interest`, `capital_gains_residential_property`, `cash_isa`, `cash_isa_balance`, `corporate_wealth`, `directly_held_shares`, `dividend_income`, `gross_financial_wealth`, `household_lifetime_isa_balance`, `lifetime_isa_balance`, `lump_sum_income`, `main_residence_value`, `maintenance_income`, `miscellaneous_income`, `mortgage_capital_repayment`, `net_financial_wealth`, `non_residential_property_value`, `other_residential_property_value`, `owned_land`, `pension_credit_reported_capital`, `pension_income`, `private_pension_wealth`, `private_transfer_income`, `property_income`, `property_rental_income`, `savings`, `spousal_maintenance_income`, `stocks_and_shares_isa`, `stocks_and_shares_isa_balance`, `sublet_income`, `uc_reported_capital`, `unit_and_investment_trusts`

## Savings income

When we project a dataset to later years (up to 2032-33), we grow savings income by the path the dataset says its savings income was calibrated to. A dataset that declares the `obr_savings_income_2022_2025` projection grows it by the OBR's savings income forecast per person from 2022-23 to 2025-26 and by per capita GDP in other years. A dataset that declares nothing grows it by per capita GDP in every year, as before. The OBR's series is the "Savings income" row of its receipts table "Self-employed income streams: growth rates" (October 2026 EFO, Table 4.5, from 2024-25; earlier years from the March 2026 and October 2024 EFOs), divided by population growth.

| Fiscal year | 2022 | 2023 | 2024 | 2025 |
|-------------|------|------|------|------|
| OBR savings income | 50.4% | 129.9% | 35.0% | 0.6% |
| Per person | 48.9% | 126.9% | 33.5% | 0.4% |

From 2023-24 to 2025-26 the OBR's savings income rises 35.8%, where per capita GDP and population growth would give 10.3%. After 2025-26 these variables follow per capita GDP under either rule.

The declaration matters because a dataset's savings income is fitted to targets its builder moved forward along some path. Growing it by a different path would miss those targets. Datasets store the declaration in the H5 root attribute `policyengine_uk.savings_income_projection`.

We apply this to `non_cash_isa_cash_interest`, `other_investment_income` and `savings_interest_income`, and to ISA interest in datasets whose ISA income contract projects it additively. Datasets with the legacy gross contract grow gross interest, ISA interest included, and hold the ISA part flat. Inputs given directly to a calculation, and years after the dataset projection, use the index each variable declares: household interest income (ONS D.41) for interest and per capita GDP for other investment income.

## Council tax

We project each country's council tax receipts, net of council tax reduction, with the OBR's figures (October 2026 EFO, Expenditure Table 5.1) from 2025-26, and official outturns before then: MHCLG's council tax requirement for England, the Scottish Government's net amount billed and the Welsh Government's net collectable debit.

| Fiscal year | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|
| England | 6.6% | 6.5% | 7.0% | 6.1% | 5.2% | 5.6% | 5.5% | 5.4% | 5.3% |
| Scotland | 6.4% | 2.4% | 3.9% | 3.9% | 3.9% | 3.9% | 3.9% | 3.9% | 3.9% |
| Wales | 7.1% | 9.9% | 7.7% | 7.4% | 7.4% | 7.4% | 7.4% | 7.4% | 7.4% |

Receipts are the Band D level times the tax base, the number of Band D equivalent dwellings, so they grow with the number of homes as well as with bills. Household weights grow with population, so each household's `council_tax` grows by its country's receipts growth divided by population growth: (1 + receipts growth) / (1 + population growth) − 1. Each country's weighted total then grows with its receipts. Northern Ireland has no council tax (it has domestic rates), so any `council_tax` a dataset gives its households is held flat.

## Mortgage interest

We use the OBR's mortgage interest rate index growth rates.

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 14.6% | 52.2% | 27.3% | 9.5% | 6.2% | 11.6% | 6.7% | 4.8% | 5.5% | 5.5% |

We apply this to: `mortgage_interest_repayment`, `property_finance_costs`, `property_finance_costs_brought_forward`

## Private pension index

We use RPI year-on-year change from the previous year, capped at 5%.

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 5.0% | 5.0% | 5.0% | 3.6% | 4.1% | 3.6% | 4.3% | 3.0% | 3.0% | 2.3% |

We apply this to: `private_pension_income`

## Rent

We use the OBR's rental growth projections.

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 3.5% | 5.8% | 7.2% | 5.4% | 3.6% | 3.2% | 2.7% | 2.6% | 2.5% | 2.8% |

We apply this to: `rent`

## Per capita mixed income

We derive these rates as calendar-year mixed income growth from the OBR's October 2026 EFO (Table 1.12) divided by population growth, in the same way.

| Year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 2.8% | -0.6% | 2.8% | 0.5% | 3.0% | 3.2% | 3.5% | 3.8% | 4.0% | 4.0% |

We apply this to: `self_employment_income`

## Population

We use the OBR's October 2026 population forecast to 2031-32, read from its economy tables (Table 1.1 real GDP over Table 1.5 real GDP per person, at Q2), and after that the population growth in the OBR's [long-term economic determinants for the March 2026 EFO](https://obr.uk/supplementary-forecast-information-release-long-term-economic-determinants-march-2026/), which follows the principal projection of the [ONS 2024-based national population projections](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationprojections/bulletins/nationalpopulationprojections/2024based). On the March 2026 EFO the same reading of the tables reproduces the determinants' forecast years, so the October determinants, once published, should change only the later years.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|-------------|------|------|------|------|------|------|------|------|------|------|
| Growth rate | 1.1% | 1.3% | 1.0% | 0.3% | 0.2% | 0.1% | 0.2% | 0.2% | 0.2% | 0.2% |

We apply this to: `household_weight`

# Economic assumptions

We project economic variables using year-over-year growth rates stored in `parameters/gov/economic_assumptions/yoy_growth.yaml`. We generate index values from these rates to update household variables. We source all values from the OBR's Economic and Fiscal Outlook ([March 2025](https://obr.uk/efo/economic-and-fiscal-outlook-march-2025/)) unless we specify otherwise.

## Consumer price index

We use the OBR's CPI projections to drive most benefit and consumption variables.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 10.0% | 5.7% | 2.3% | 3.2% | 1.9% | 2.0% | 2.0% | 2.0% |

We apply CPI to these variables:
- All reported benefits– `attendance_allowance_reported`, `carers_allowance_reported`, `child_benefit_reported`, `child_tax_credit_reported`, `dla_m_reported`, `dla_sc_reported`, `esa_contrib_reported`, `esa_income_reported`, `housing_benefit_reported`, `iidb_reported`, `incapacity_benefit_reported`, `income_support_reported`, `jsa_contrib_reported`, `jsa_income_reported`, `maternity_allowance_reported`, `pension_credit_reported`, `pip_dl_reported`, `pip_m_reported`, `sda_reported`, `state_pension_reported`, `universal_credit_reported`, `winter_fuel_allowance_reported`, `working_tax_credit_reported`
- All consumption categories– `alcohol_and_tobacco_consumption`, `clothing_and_footwear_consumption`, `communication_consumption`, `domestic_energy_consumption`, `education_consumption`, `food_and_non_alcoholic_beverages_consumption`, `health_consumption`, `household_furnishings_consumption`, `housing_water_and_electricity_consumption`, `miscellaneous_consumption`, `recreation_consumption`, `restaurants_and_hotels_consumption`, `transport_consumption`
- Other variables– `afcs_reported`, `bsp_reported`, `childcare_expenses`, `diesel_spending`, `free_school_fruit_veg`, `free_school_meals`, `free_school_milk`, `maintenance_expenses`, `petrol_spending`, `statutory_maternity_pay`, `statutory_paternity_pay`, `statutory_sick_pay`, `state_pension`

## Average earnings

We apply the OBR's wage growth forecasts to employment-related variables.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 6.4% | 6.9% | 4.7% | 3.7% | 2.2% | 2.1% | 2.3% | 2.5% |

We use average earnings for these variables: `employee_pension_contributions`, `employer_pension_contributions`, `employment_income`, `employment_income_before_lsr`, `personal_pension_contributions`, `student_loan_repayments`

## Lagged average earnings

We lag earnings growth by one year and use that to uprate housing service charges (including ground rent).

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 5.9% | 6.4% | 6.9% | 4.7% | 3.7% | 2.2% | 2.1% | 2.3% |

## Per capita GDP

We derive these rates from OBR GDP growth and ONS population projections.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 9.2% | 5.0% | 3.8% | 2.8% | 2.8% | 3.1% | 3.3% | 3.3% |

We use per capita GDP for these variables: `capital_gains`, `capital_gains_before_response`, `corporate_wealth`, `dividend_income`, `gross_financial_wealth`, `lump_sum_income`, `main_residence_value`, `maintenance_income`, `miscellaneous_income`, `mortgage_capital_repayment`, `net_financial_wealth`, `non_residential_property_value`, `other_investment_income`, `other_residential_property_value`, `owned_land`, `pension_income`, `private_transfer_income`, `property_income`, `savings`, `savings_interest_income`, `sublet_income`

## Council tax

We use the OBR's Council Tax receipts and projections.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 5.3% | 5.6% | 6.4% | 4.6% | 4.5% | 4.6% | 4.5% | 4.5% |

We apply this to: `council_tax`

## Mortgage interest

We use the OBR's mortgage interest rate index growth rates.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 26.2% | 48.5% | 22.1% | 13.6% | 12.6% | 8.2% | 4.2% | 4.7% |

We apply this to: `mortgage_interest_repayment`

## Private pension index

We use RPI year-on-year change from the previous year, capped at 5%.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 5.0% | 5.0% | 5.0% | 4.7% | 3.7% | 2.2% | 2.1% | 2.3% |

We apply this to: `private_pension_income`

## Rent

We use the OBR's rental growth projections.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 4.0% | 6.3% | 7.4% | 5.7% | 3.6% | 2.7% | 2.3% | 2.4% |

We apply this to: `rent`

## Per capita mixed income

We derive these rates from OBR mixed income growth and ONS population projections.

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 6.3% | 2.4% | 4.8% | 4.7% | 3.1% | 3.1% | 3.6% | 3.8% |

We apply this to: `self_employment_income`

## Population

We use ONS population [projections](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationprojections/bulletins/nationalpopulationprojections/2022based).

| Fiscal year | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 | 2028 | 2029 |
|-------------|------|------|------|------|------|------|------|------|
| Growth rate | 0.3% | 1.4% | 1.0% | 1.1% | 0.7% | 0.8% | 0.4% | 0.5% |

We apply this to: `household_weight`
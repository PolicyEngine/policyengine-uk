# HBAI

PolicyEngine UK includes variables that match to the Households Below Average Income (HBAI) income concepts. These are:

- `hbai_household_net_income`: Household net income, before housing costs
- `hbai_household_net_income_ahc`: Household net income, after housing costs
- `equiv_hbai_household_net_income`: Equivalised household net income, before housing costs (BHC)
- `equiv_hbai_household_net_income_ahc`: Equivalised household net income, after housing costs (AHC)

These variables are used in the HBAI income distribution and poverty [statistics](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2024/households-below-average-income-an-analysis-of-the-uk-income-distribution-fye-1995-to-fye-2024), which are published by the Department for Work and Pensions (DWP) in the UK. The HBAI income concepts are defined [here](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2023/households-below-average-income-series-quality-and-methodology-information-report-fye-2023#income-definition).

The table below shows how the HBAI income components map to PolicyEngine variables. The HBAI income definition is based on the income of all members of a household, and includes various sources of income, subtractions, and housing costs (for the AHC variant).

| HBAI component | PolicyEngine variable/notes |
|------|-------------|
| **Income** |  |
| Usual net earnings from employment |`employment_income` |
| Profit or loss from self-employment (losses are treated as a negative income) | `self_employment_income`|
| Income received from dividends (from FYE 2022) |`dividend_income`|
| State support - all benefits and tax credits |`hbai_benefits`|
| Income from occupational and private pensions |`private_pension_income` (includes occupational pension income)|
| Investment income |`dividend_income`, `savings_interest_income`, `property_income`|
| Maintenance payments |`maintenance_income`|
| Income from educational grants and scholarships (including, for students, student loans and parental contributions) |`student_payments`|
| The cash value of certain forms of income in kind (free school meals, free school breakfast, free school milk, free school fruit and vegetables, Healthy Start vouchers and free TV licences for those aged 75 and over who receive Pension Credit) |`free_school_meals`, `free_school_fruit_veg`, `free_school_milk`, `healthy_start_vouchers`, `free_tv_licence_value`|
| **Subtractions** | |
| Income tax payments |`income_tax`|
| National Insurance contributions |`national_insurance`|
| Domestic rates/council tax |`council_tax` and `domestic_rates`|
| Contributions to occupational pension schemes (including all additional voluntary contributions (AVCs) to occupational pension schemes, and any contributions to stakeholder and personal pensions) |`employee_pension_contributions`, `personal_pension_contributions`|
| All maintenance and child support payments, which are deducted from the income of the person making the payment |`maintenance_expenses`|
| Parental contributions to students living away from home | `external_child_payments`|
| Student loan repayments | `student_loan_repayments`|
| **Housing costs** | |
| Rent (gross of housing benefit) | `rent`|
| Water rates, community water charges and council water charges | `water_and_sewerage_charges`|
| Mortgage interest payments | `mortgage_interest_repayment`|
| Structural insurance premiums (for owner occupiers) | `structural_insurance_payments` |
| Ground rent and service charges |`housing_service_charges`|

## Nowcasting/forecasting


Each of the variables above is either derived from other variables, or is a direct input variable. Direct input variables are uprated in future years according to economic indices, specified in the table below.

| Variable | Index | Notes |
|----------|-------|-------|
| `employment_income` | gov.obr.per_capita.employment_income | Uprated based on OBR per capita employment income projections |
| `self_employment_income` | gov.obr.per_capita.mixed_income | Uprated based on OBR per capita mixed income projections |
| `dividend_income` | gov.economic_assumptions.indices.obr.per_capita.gdp | Uprated based on OBR per capita GDP projections |
| `hbai_benefits` | Various | Different benefits use different uprating indices, mostly gov.obr.consumer_price_index |
| `private_pension_income` | gov.obr.private_pension_index | Uprated based on OBR private pension index |
| `savings_interest_income` | gov.economic_assumptions.indices.obr.per_capita.gdp | Uprated based on OBR per capita GDP projections |
| `property_income` | gov.economic_assumptions.indices.obr.per_capita.gdp | Uprated based on OBR per capita GDP projections |
| `maintenance_income` | gov.economic_assumptions.indices.obr.per_capita.gdp | Uprated based on OBR per capita GDP projections |
| `student_payments` | Not uprated directly | Currently no specific uprating for student payments |
| `free_school_meals` |gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `free_school_fruit_veg` | gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `free_school_milk` | gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `free_tv_licence_value` | Not directly uprated | Depends on policy parameters |
| `income_tax` | Derived | Calculated based on income and tax policy |
| `national_insurance` | Derived | Calculated based on income and NI policy |
| `council_tax` | gov.obr.council_tax | Uprated based on OBR council tax revenue projections |
| `domestic_rates` | gov.obr.council_tax | Uprated with council tax as proxy |
| `employee_pension_contributions` | gov.obr.per_capita.employment_income | Uprated based on per capita employment income growth |
| `personal_pension_contributions` | gov.obr.per_capita.employment_income | Uprated based on per capita employment income growth |
| `maintenance_expenses` | gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `student_loan_repayments` | gov.economic_assumptions.indices.obr.average_earnings | Uprated based on OBR average earnings projections |
| `rent` | gov.obr.rent | Uprated based on OBR rent projections |
| `water_and_sewerage_charges` | gov.obr.consumer_price_index | Uprated based on CPI as proxy |
| `mortgage_interest_repayment` | gov.obr.mortgage_interest | Uprated based on OBR mortgage interest projections |
| `housing_service_charges` | gov.obr.consumer_price_index | Uprated based on CPI as proxy |
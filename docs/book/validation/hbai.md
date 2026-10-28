# HBAI

```{note}
PolicyEngine UK includes variables that match to the Households Below Average Income (HBAI) income concepts.
```

These are:

- `hbai_household_net_income`: Household net income, before housing costs, with a negative figure reset to zero
- `hbai_household_net_income_before_reset_to_zero`: The same income before a negative figure is reset to zero
- `hbai_household_net_income_ahc`: Household net income, after housing costs
- `equiv_hbai_household_net_income`: Equivalised household net income, before housing costs (BHC)
- `equiv_hbai_household_net_income_ahc`: Equivalised household net income, after housing costs (AHC)

These variables are used in the HBAI income distribution and poverty [statistics](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025), which are published by the Department for Work and Pensions (DWP) in the UK. The HBAI income concepts are defined in the [FYE 2025 background information and methodology report](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#housing-costs).

```{important}
The table below shows how the HBAI income components map to PolicyEngine variables. The HBAI income definition is based on the income of all members of a household, and includes various sources of income, subtractions, and housing costs (for the AHC variant).
```

| HBAI component | PolicyEngine variable/notes |
|------|-------------|
| **Income** |  |
| Usual net earnings from employment |`employment_income` |
| Profit or loss from self-employment (losses are treated as a negative income) | `self_employment_income`|
| Income received from dividends (from FYE 2022) |`dividend_income`|
| State support - all benefits and tax credits |`hbai_benefits`|
| Income from occupational and private pensions |`private_pension_income` (includes occupational pension income)|
| Investment income |`dividend_income`, `savings_interest_income`, `property_income_after_finance_costs`|
| Maintenance payments |`maintenance_income`, `spousal_maintenance_income`|
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

## Property income

HBAI income counts a landlord's profit after mortgage interest. The Family Resources Survey asks for rent from property "AFTER paying for any of the things on this card", and show card K6 lists mortgage payments and interest on a loan to buy the property ([FRS 2023–24 question instructions](https://doc.ukdataservice.ac.uk/doc/9367/mrdoc/pdf/9367_frs_2023-24_question_instructions_final.pdf), question PropRent, page 302). PolicyEngine's `property_income` is the profit before those finance costs, because income tax no longer deducts them (ITTOIA 2005 s. 272A(4)) and relieves them with a tax reduction instead (s. 274A). So `hbai_household_net_income`, `market_income` and `household_market_income` count `property_income_after_finance_costs`: `property_income` less `property_finance_costs`, and nil where the costs exceed a positive profit. The tax reduction itself is in `income_tax`. Interest on a let property is not a housing cost; only the household's own `mortgage_interest_repayment` is deducted after housing costs.

## Negative incomes

HBAI resets a negative income before housing costs to zero: "Negative incomes BHC are reset to zero, but negative AHC incomes calculated from the adjusted BHC incomes are possible. Where incomes have been adjusted to zero BHC, income AHC is derived from the adjusted BHC income." ([HBAI Background Information and Methodology report FYE 2025](https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#negative-incomes)).

PolicyEngine does the same. `hbai_household_net_income` is `hbai_household_net_income_before_reset_to_zero` reset to zero when negative, and `hbai_household_net_income_ahc` subtracts all five housing costs listed above from the reset figure, so it can be negative. The equivalised incomes, `household_income_decile`, the poverty flags and the poverty gaps all use the reset figure. A household whose income was negative is below every absolute poverty line, and its before-housing-costs poverty gap is the whole line. It is below the relative line while the median person's income is positive; if half or more of people had BHC income at or below zero, the reset would make the BHC median, and so the BHC relative line, zero. Households with equal incomes share the rank at the top of their group, so households at zero are in the bottom decile while they hold at most a tenth of people. On the enhanced FRS under 1% of people have an income at or below zero before the reset, so both conditions hold. The labour supply responses use the figure before the reset, which is the household's actual budget constraint.
`hbai_household_net_income_ahc` deducts all five housing-cost rows above from the reset `hbai_household_net_income`. Ground rent and service charges (`housing_service_charges`) are the fifth cost. Housing costs can exceed income, leaving negative AHC income. The equivalised AHC income and AHC poverty measures use that result; `household_income_decile` uses BHC income.

## Income deciles

`household_income_decile` ranks households by equivalised BHC income.
`household_income_decile_ahc` ranks them by
`equiv_hbai_household_net_income_ahc`. Both use household survey weight multiplied
by household size, so the distribution counts people. Calculate the decile on the
population to be ranked; a single-household calculation does not locate that
household in the national income distribution.

The AHC decile follows the existing BHC ranking conventions: it resets negative
values to zero for ranking, and equal values share the cumulative rank at the top
of their group. A tied group can therefore span a decile boundary without being
split. This ranking adjustment leaves AHC income and AHC poverty measures
unchanged, including their negative values. It is a model ranking convention,
not a claim to reproduce DWP's published AHC decile groups exactly.

In FRS-based datasets, `housing_service_charges` contains the annualised property charges recorded in `CHRGAMT1`–`CHRGAMT9`: ground rent, chief rent, service charges, regular maintenance, caravan site rent, factoring charges, other regular charges and combined charges. `CHRGAMT2`, historically feu duty, is unused in the FRS 2024–25 dictionary. The combined-charge question is an alternative to recording individual amounts. Water and sewerage and rent are separate inputs; calculator users should supply each cost once, with service charges additional to the other housing-cost inputs. See the [FRS 2024–25 question instructions](https://doc.ukdataservice.ac.uk/doc/9563/mrdoc/pdf/9563_frs_2024-25_question_instructions_final.pdf), property charges section (pages 98–99), and its [variable dictionaries](https://doc.ukdataservice.ac.uk/doc/9563/mrdoc/ukda_data_dictionaries.zip).

## Normalized squared poverty gaps

`squared_poverty_gap_bhc` and `squared_poverty_gap_ahc` are annual household, dimensionless components of the Foster–Greer–Thorbecke poverty-severity measure (FGT2). Each is the square of its existing nonnegative `poverty_gap_bhc` or `poverty_gap_ahc`, divided by the matching positive `poverty_line_bhc` or `poverty_line_ahc` **before squaring**:

$$
s_h = \left(\frac{\max(z_h-y_h,0)}{z_h}\right)^2, \qquad z_h>0.
$$

For example, income at or above the line gives zero, income halfway to the line gives 0.25, and zero income gives one. Scaling income and its line by the same positive factor leaves the component unchanged. These are normalized components, not GBP-squared poverty gaps or sums.

The statistical definition follows the [World Bank PIP methodology, section 4.1](https://worldbank.github.io/PIP-Methodology-2022-05/surveyestimates.html#monetarypoverty). The variables retain the UK HBAI basis described above: negative BHC income is reset to zero, while AHC income can be negative. The AHC component can therefore exceed one. PIP's own negative-welfare preprocessing is not reproduced here, and these components are not an official DWP severity estimate.

For a person-based population index, map each household's component to every person and take the existing survey-weighted **mean**, not a sum or a household-weighted mean. Given an already configured `Microsimulation` named `sim`:

```python
component = sim.calculate("squared_poverty_gap_bhc", 2025, map_to="person")
fgt2 = component.mean(skipna=False)
```

For example, a one-person household with survey weight 2 and component 0.25, plus a three-person household with survey weight 1 and component 1, gives `(2 * 0.25 + 3 * 1) / (2 + 3) = 0.7`. A household-weighted mean would instead give 0.5. This tiny synthetic example is not a national estimate.

A zero or negative poverty line has an undefined normalized component, returned as `NaN`. The explicit `skipna=False` preserves that invalid-domain signal in a weighted mean rather than silently dropping people; alternatively validate that all included poverty lines are positive before aggregation. No new income, poverty-line, equivalence, survey-weight or dataset assumptions are introduced.

## Nowcasting/forecasting


```{tip}
Each of the variables above is either derived from other variables, or is a direct input variable. Direct input variables are uprated in future years according to economic indices, specified in the table below.
```

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
| `spousal_maintenance_income` | gov.economic_assumptions.indices.obr.per_capita.gdp | Uprated based on OBR per capita GDP projections |
| `student_payments` | Not uprated directly | Currently no specific uprating for student payments |
| `free_school_meals` |gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `free_school_fruit_veg` | gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `free_school_milk` | gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `free_tv_licence_value` | Not directly uprated | Depends on policy parameters |
| `income_tax` | Derived | Calculated based on income and tax policy |
| `national_insurance` | Derived | Calculated based on income and NI policy |
| `council_tax` | gov.economic_assumptions.yoy_growth.obr.council_tax | Uprated by each country's council tax receipts growth (official outturns to 2024-25, then OBR forecasts) divided by population growth, so each country's weighted total tracks its receipts; held flat in Northern Ireland |
| `domestic_rates` | gov.economic_assumptions.yoy_growth.finance_ni.domestic_rates | Uprated by growth in Northern Ireland's combined regional and district domestic rate poundage to 2026-27, then by an assumed 4.33% a year (2026-27's growth) |
| `employee_pension_contributions` | gov.obr.per_capita.employment_income | Uprated based on per capita employment income growth |
| `personal_pension_contributions` | gov.obr.per_capita.employment_income | Uprated based on per capita employment income growth |
| `maintenance_expenses` | gov.obr.consumer_price_index | Uprated based on CPI inflation |
| `student_loan_repayments` | gov.economic_assumptions.indices.obr.average_earnings | Uprated based on OBR average earnings projections |
| `rent` | gov.obr.rent | Social rents uprated by CPI+1%, private rents uprated with outturn data by region to 2025, then with backed-out private rent level growth from OBR aggregate rent forecasts (assuming social rent grows at CPI+1%) |
| `water_and_sewerage_charges` | gov.economic_assumptions.yoy_growth.ofwat.water_bills (England and Wales), gov.economic_assumptions.yoy_growth.scottish_water.water_bills (Scotland) | Uprated by each country's published bill increases, then projections; Northern Ireland has no domestic water charges and is held flat |
| `mortgage_interest_repayment` | gov.obr.mortgage_interest | Uprated based on outturn Ofwat data to 2025, then Ofwat projections onwards |
| `housing_service_charges` | gov.economic_assumptions.indices.obr.lagged_average_earnings | Uprated based on lagged average earnings as proxy |

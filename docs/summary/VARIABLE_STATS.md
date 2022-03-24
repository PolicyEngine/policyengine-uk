# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2020) 2019-20 Family Resources Survey, with simulation turned on.


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3,555.9
  - Median: 0.0
  - Stddev: 6,773.8
  - Non-zero count: 22,795,289.12019348


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 871.6
  - Median: 0.0
  - Stddev: 3,945.1
  - Non-zero count: 11,334,335.792037964


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 350.2
  - Median: 0.0
  - Stddev: 1,605.5
  - Non-zero count: 2,352,373.4512889385


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2,684.3
  - Median: 0.0
  - Stddev: 5,231.5
  - Non-zero count: 19,532,398.743988037


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 32.5
  - Median: 35.0
  - Stddev: 31.4
  - Non-zero count: 17,457,935.691912055


- claims_all_entitled_benefits:
  - Type: bool
  - Entity: benunit
  - Description: Claims all eligible benefits
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- claims_legacy_benefits:
  - Type: bool
  - Entity: benunit
  - Description: Claims legacy benefits
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 14,087,437.037007257


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1,332.5
  - Median: 0.0
  - Stddev: 4,983.2
  - Non-zero count: 12,100,209.717765808


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 796.4
  - Median: 0.0
  - Stddev: 3,105.0
  - Non-zero count: 9,324,307.109794617


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 7,651.1
  - Median: 4,213.0
  - Stddev: 10,102.6
  - Non-zero count: 17,908,260.573806763


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 6,755,573.978881836


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,590,278.30052185


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 14,073,343.781025708


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,369,280.385392189


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 14,019,077.485054284


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 12,981,342.029133111


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -871.6
  - Median: 0.0
  - Stddev: 3,945.1
  - Non-zero count: 4,798,723.378730774


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,223.4
  - Median: 0.0
  - Stddev: 4,294.6
  - Non-zero count: 15,375,638.431549072


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1,887.8
  - Median: 0.0
  - Stddev: 4,032.6
  - Non-zero count: 13,454,363.279830933


- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: -1,326.6
  - Median: -241.1
  - Stddev: 3,740.1
  - Non-zero count: 0.0


- hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income
  - Mean: -1,326.6
  - Median: -241.1
  - Stddev: 3,740.1
  - Non-zero count: 0.0


- hbai_excluded_income_change:
  - Type: float
  - Entity: household
  - Description: Change in HBAI-excluded income
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- in_deep_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), after housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,263,063.2293014526


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 881,743.2391433716


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,735,875.1565933228


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,977,349.880004883


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 645.3
  - Median: 0.0
  - Stddev: 2,113.9
  - Non-zero count: 3,735,875.1565933228


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 578.9
  - Median: 0.0
  - Stddev: 1,905.5
  - Non-zero count: 3,977,349.880004883


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 13,766.3
  - Median: 13,876.2
  - Stddev: 5,719.5
  - Non-zero count: 28,092,421.269058228


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 16,294.5
  - Median: 16,195.3
  - Stddev: 5,552.8
  - Non-zero count: 28,092,421.269058228


- base_net_income:
  - Type: float
  - Entity: person
  - Description: Existing net income for the person to use as a base in microsimulation
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- capital_income:
  - Type: float
  - Entity: person
  - Description: Income from savings or dividends
  - Mean: 248.5
  - Median: 0.0
  - Stddev: 2,145.3
  - Non-zero count: 21,670,285.62224579


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 15,490.0
  - Median: 8,579.9
  - Stddev: 26,078.0
  - Non-zero count: 37,555,291.37547302


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 32,632.6
  - Median: 29,223.4
  - Stddev: 21,605.7
  - Non-zero count: 27,972,357.637786865


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 30,845.1
  - Median: 27,364.0
  - Stddev: 22,372.0
  - Non-zero count: 27,772,577.50140381


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 31,247.8
  - Median: 27,981.5
  - Stddev: 20,642.2
  - Non-zero count: 27,895,218.02496338


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 19,542.8
  - Median: 16,025.2
  - Stddev: 26,177.1
  - Non-zero count: 47,727,965.527267456


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 33,700.3
  - Median: 28,758.5
  - Stddev: 27,090.1
  - Non-zero count: 27,972,357.637786865


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 31,107.9
  - Median: 25,811.1
  - Stddev: 27,311.3
  - Non-zero count: 27,772,577.50140381


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 954.3
  - Median: 520.0
  - Stddev: 1,034.5
  - Non-zero count: 30,650,651.69935608


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 41,725.7
  - Median: 33,482.6
  - Stddev: 41,432.6
  - Non-zero count: 28,024,327.281341553


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 34,074.5
  - Median: 25,665.1
  - Stddev: 44,457.9
  - Non-zero count: 24,095,330.00766754


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 32,373.6
  - Median: 27,269.1
  - Stddev: 26,199.5
  - Non-zero count: 27,895,218.02496338


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 30,654,622.432510376


- is_apprentice:
  - Type: bool
  - Entity: person
  - Description: In an apprenticeship programme
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- lump_sum_income:
  - Type: float
  - Entity: person
  - Description: Lump sum income
  - Mean: 88.0
  - Median: -1.0
  - Stddev: 1,944.1
  - Non-zero count: 248,919.96118164062


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 27.0
  - Median: 0.0
  - Stddev: 515.9
  - Non-zero count: 530,043.4014587402


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 15,986.9
  - Median: 9,351.8
  - Stddev: 26,574.0
  - Non-zero count: 40,038,253.89922333


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.9
  - Median: 8.7
  - Stddev: 1.7
  - Non-zero count: 59,876,255.938705444


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 41.0
  - Median: 0.0
  - Stddev: 828.2
  - Non-zero count: 655,234.8271789551


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 16,439.6
  - Median: 15,199.0
  - Stddev: 17,747.5
  - Non-zero count: 47,727,965.527267456


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: 124.3
  - Median: 0.0
  - Stddev: 1,219.7
  - Non-zero count: 1,106,014.1096191406


- sublet_income:
  - Type: float
  - Entity: person
  - Description: Income received from sublet agreements
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- weekly_hours:
  - Type: float
  - Entity: person
  - Description: Weekly hours
  - Mean: 18.4
  - Median: 10.0
  - Stddev: 19.9
  - Non-zero count: 30,650,651.69935608


- corporate_tax_incidence:
  - Type: float
  - Entity: household
  - Description: Corporate tax incidence
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- corporate_wealth:
  - Type: float
  - Entity: household
  - Description: Corporate wealth
  - Mean: 136,050.5
  - Median: 19,720.2
  - Stddev: 379,696.8
  - Non-zero count: 19,439,238.115867615


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 19,439,238.115867615


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 168,873.6
  - Median: 130,000.0
  - Stddev: 241,917.5
  - Non-zero count: 18,067,576.031471252


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 1,603.5
  - Median: 0.0
  - Stddev: 34,377.7
  - Non-zero count: 181,736.76919555664


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 7,456.4
  - Median: 0.0
  - Stddev: 64,683.9
  - Non-zero count: 1,227,986.830368042


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 193,840.7
  - Median: 133,210.2
  - Stddev: 322,277.5
  - Non-zero count: 18,449,374.058158875


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 176,330.0
  - Median: 130,000.0
  - Stddev: 262,398.8
  - Non-zero count: 18,180,123.219459534


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 62,572.7
  - Median: 9,069.8
  - Stddev: 174,623.5
  - Non-zero count: 19,439,238.115867615


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 153,391.5
  - Median: 105,412.9
  - Stddev: 255,049.3
  - Non-zero count: 18,449,374.058158875


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 215,964.2
  - Median: 141,656.1
  - Stddev: 355,138.0
  - Non-zero count: 23,141,902.50200653


- owned_land:
  - Type: float
  - Entity: household
  - Description: Owned land
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- carbon_consumption:
  - Type: float
  - Entity: household
  - Description: Carbon consumption
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- alcohol_and_tobacco_consumption:
  - Type: float
  - Entity: household
  - Description: Alcohol and tobacco
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- clothing_and_footwear_consumption:
  - Type: float
  - Entity: household
  - Description: Clothing and footwear
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- communication_consumption:
  - Type: float
  - Entity: household
  - Description: Communication
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- education_consumption:
  - Type: float
  - Entity: household
  - Description: Education
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- food_and_non_alcoholic_beverages_consumption:
  - Type: float
  - Entity: household
  - Description: Food and alcoholic beverages
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- health_consumption:
  - Type: float
  - Entity: household
  - Description: Health
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- household_furnishings_consumption:
  - Type: float
  - Entity: household
  - Description: Household furnishings
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- housing_water_and_electricity_consumption:
  - Type: float
  - Entity: household
  - Description: Housing, water and electricity
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- miscellaneous_consumption:
  - Type: float
  - Entity: household
  - Description: Miscellaneous
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- recreation_consumption:
  - Type: float
  - Entity: household
  - Description: Recreation
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- restaurants_and_hotels_consumption:
  - Type: float
  - Entity: household
  - Description: Restaurants and hotels
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- transport_consumption:
  - Type: float
  - Entity: household
  - Description: Transport
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- additional_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (additional)
  - Mean: 7,456.4
  - Median: 0.0
  - Stddev: 64,683.9
  - Non-zero count: 1,227,986.830368042


- cumulative_non_residential_rent:
  - Type: float
  - Entity: household
  - Description: Cumulative non-residential rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- cumulative_residential_rent:
  - Type: float
  - Entity: household
  - Description: Cumulative residential rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- main_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (main)
  - Mean: 168,873.6
  - Median: 130,000.0
  - Stddev: 241,917.5
  - Non-zero count: 18,067,576.031471252


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,373,183.79914093


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 1,603.5
  - Median: 0.0
  - Stddev: 34,377.7
  - Non-zero count: 181,736.76919555664


- non_residential_rent:
  - Type: float
  - Entity: household
  - Description: Non-residential rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- property_purchased:
  - Type: bool
  - Entity: household
  - Description: All property bought this year
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,092,421.269058228


- property_sale_rate:
  - Type: float
  - Entity: state
  - Description: Residential property sale rate
  - Mean: 0.1
  - Median: 0.1
  - Stddev: 0.0
  - Non-zero count: 2.0


- rent:
  - Type: float
  - Entity: household
  - Description: Rent
  - Mean: 2,592.4
  - Median: -52.0
  - Stddev: 4,221.4
  - Non-zero count: 10,067,608.547340393


- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2,265.2
  - Median: -52.0
  - Stddev: 3,968.6
  - Non-zero count: 9,177,681.268699765


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 85.3
  - Median: 0.0
  - Stddev: 881.8
  - Non-zero count: 1,796,354.5325927734


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,411.2
  - Median: 1,347.6
  - Stddev: 751.4
  - Non-zero count: 27,443,887.987365723


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,292.3
  - Median: 1,311.1
  - Stddev: 859.0
  - Non-zero count: 25,806,276.245788574


- employer_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Employer pension contributions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- family_rent:
  - Type: float
  - Entity: benunit
  - Description: Gross rent for the family
  - Mean: 2,265.2
  - Median: -52.0
  - Stddev: 3,968.6
  - Non-zero count: 9,177,681.268699765


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 2,592.4
  - Median: -52.0
  - Stddev: 4,221.4
  - Non-zero count: 10,067,608.547340393


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 75.7
  - Median: 0.0
  - Stddev: 339.3
  - Non-zero count: 2,629,456.374687195


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 45.5
  - Median: 0.0
  - Stddev: 621.9
  - Non-zero count: 759,847.8211364746


- mortgage:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- mortgage_capital_repayment:
  - Type: float
  - Entity: household
  - Description: Mortgage payments
  - Mean: 2,038.8
  - Median: 0.0
  - Stddev: 5,618.7
  - Non-zero count: 7,782,082.711456299


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 785.5
  - Median: -52.0
  - Stddev: 2,093.5
  - Non-zero count: 7,757,128.283172607


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 452.1
  - Median: 0.0
  - Stddev: 1,299.7
  - Non-zero count: 17,552,897.128219604


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,216.3
  - Median: 0.0
  - Stddev: 3,035.7
  - Non-zero count: 10,067,608.547340393


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 29.3
  - Median: 0.0
  - Stddev: 172.5
  - Non-zero count: 1,916,755.9627227783


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 374.6
  - Median: 358.8
  - Stddev: 252.8
  - Non-zero count: 27,257,830.610717773


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 1.6
  - Median: 0.0
  - Stddev: 17.0
  - Non-zero count: 1,796,354.5325927734


- weekly_rent:
  - Type: float
  - Entity: household
  - Description: Weekly average rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- BRMA:
  - Type: Categorical
  - Entity: household
  - Description: Broad Rental Market Area


- local_authority:
  - Type: Categorical
  - Entity: household
  - Description: The Local Authority for the household


- age:
  - Type: int
  - Entity: person
  - Description: Age
  - Mean: 40.8
  - Median: 40.0
  - Stddev: 23.6
  - Non-zero count: 59,226,830.266326904


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 38,325,669.98610687


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,080,700.434761047


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,469,885.517837524


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1,980.2
  - Median: 1,981.0
  - Stddev: 23.6
  - Non-zero count: 59,876,255.938705444


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 82.8
  - Median: 100.0
  - Stddev: 41.2
  - Non-zero count: 59,876,255.938705444


- current_education:
  - Type: Categorical
  - Entity: person
  - Description: Current education


- gender:
  - Type: Categorical
  - Entity: person
  - Description: Gender of the person


- highest_education:
  - Type: Categorical
  - Entity: person
  - Description: Highest status education completed


- in_FE:
  - Type: bool
  - Entity: person
  - Description: Whether this person is in Further Education
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- in_HE:
  - Type: bool
  - Entity: person
  - Description: In higher education
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- in_social_housing:
  - Type: bool
  - Entity: person
  - Description: Whether this person lives in social housing
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,280,157.419120789


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 38,867,148.359451294


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 49,406,370.42086792


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 6,037,844.156723022


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 34,791,036.69581604


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,469,885.517837524


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 6,529,924.531326294


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 29,916,717.063468933


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 28,092,421.269058228


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 29,959,538.87523651


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,375,782.5305786133


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 8,094,102.987258911


- marital_status:
  - Type: Categorical
  - Entity: person
  - Description: Marital status


- over_16:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 16
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 50,767,708.56518555


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 59,876,255.938705444


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 9,593,146.9
  - Median: 9,577,221.9
  - Stddev: 5,543,055.9
  - Non-zero count: 59,876,255.938705444


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight (region-adjusted)
  - Mean: 1,509.6
  - Median: 1,054.0
  - Stddev: 752.1
  - Non-zero count: 59,876,255.938705444


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 2,380.4
  - Median: 1,872.0
  - Stddev: 858.6
  - Non-zero count: 59,876,255.938705444


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 9,593,127.8
  - Median: 9,577,201.9
  - Stddev: 5,543,020.5
  - Non-zero count: 59,876,255.938705444


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 9,593,011.6
  - Median: 9,577,001.8
  - Stddev: 5,543,019.5
  - Non-zero count: 59,876,255.938705444


- role:
  - Type: Categorical
  - Entity: person
  - Description: Role (adult/child)


- accommodation_type:
  - Type: Categorical
  - Entity: household
  - Description: Type of accommodation


- country:
  - Type: Categorical
  - Entity: household
  - Description: Country of the UK


- household_equivalisation_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, after housing costs
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 28,092,421.269058228


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 28,092,421.269058228


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 9,573,672.6
  - Median: 9,574,022.4
  - Stddev: 5,545,521.5
  - Non-zero count: 28,092,421.269058228


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.2
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 28,092,421.269058228


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.1
  - Median: 2.0
  - Stddev: 1.3
  - Non-zero count: 28,092,421.269058228


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 1,499.0
  - Median: 1,062.1
  - Stddev: 749.3
  - Non-zero count: 28,092,421.269058228


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,092,421.269058228


- is_renting:
  - Type: bool
  - Entity: household
  - Description: Is renting
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- is_shared_accommodation:
  - Type: bool
  - Entity: household
  - Description: Whether the household is shared accommodation
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_bedrooms:
  - Type: int
  - Entity: household
  - Description: The number of bedrooms in the house
  - Mean: 2.6
  - Median: 3.0
  - Stddev: 1.0
  - Non-zero count: 28,092,421.269058228


- ons_tenure_type:
  - Type: Categorical
  - Entity: household
  - Description: ONS tenure type


- region:
  - Type: Categorical
  - Entity: household
  - Description: Region


- tenure_type:
  - Type: Categorical
  - Entity: household
  - Description: Tenure type of the household


- benunit_id:
  - Type: int
  - Entity: benunit
  - Description: ID for the family
  - Mean: 9,573,782.5
  - Median: 9,574,220.4
  - Stddev: 5,535,726.0
  - Non-zero count: 28,092,421.266079992


- benunit_is_renting:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is renting
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- benunit_tenure_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Tenure type of the family's household


- benunit_weight:
  - Type: float
  - Entity: benunit
  - Description: Weight factor for the benefit unit
  - Mean: 1,337.7
  - Median: 949.1
  - Stddev: 666.9
  - Non-zero count: 28,092,421.266079992


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 50.9
  - Median: 51.0
  - Stddev: 18.7
  - Non-zero count: 28,092,421.266079992


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 5,377,689.612174034


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,092,421.266079992


- family_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Family composition


- is_married:
  - Type: bool
  - Entity: benunit
  - Description: Married
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_adults:
  - Type: int
  - Entity: benunit
  - Description: The number of adults in the family
  - Mean: 1.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 27,919,271.87140283


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.9
  - Non-zero count: 5,825,346.636925697


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 49.1
  - Median: 49.0
  - Stddev: 18.6
  - Non-zero count: 28,092,421.266079992


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: inf
  - Stddev: nan
  - Non-zero count: 27,462,317.328168005


- state_id:
  - Type: int
  - Entity: state
  - Description: State ID
  - Mean: 11.5
  - Median: 11.5
  - Stddev: 0.7
  - Non-zero count: 2.0


- state_weight:
  - Type: float
  - Entity: state
  - Description: State weight
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 2.0


- benunit_has_carer:
  - Type: bool
  - Entity: benunit
  - Description: Benefit unit has a carer
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 397,313.61613321304


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 27.6
  - Median: 0.0
  - Stddev: 284.0
  - Non-zero count: 397,313.61613321304


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 500,395.9826889038


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 397,313.61613321304


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 164.4
  - Median: 0.0
  - Stddev: 637.7
  - Non-zero count: 2,125,115.244156122


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 23.1
  - Non-zero count: 2,632.128631591797


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,539,559.693687439


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 2,696.1790771484375


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,001,321.3397293091


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,125,115.244156122


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 7,846.374843597412


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 2,632.128631591797


- num_enhanced_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_severely_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 851,747.3666460514


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 3,071.5229148864746


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 158.1
  - Median: 0.0
  - Stddev: 1,041.2
  - Non-zero count: 851,747.3666460514


- bi_maximum:
  - Type: float
  - Entity: person
  - Description: Basic income before phase-outs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- basic_income:
  - Type: float
  - Entity: person
  - Description: Basic income
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- bi_phaseout:
  - Type: float
  - Entity: person
  - Description: Basic income phase-out
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ebr_energy_bills_credit:
  - Type: float
  - Entity: household
  - Description: Energy bills credit (EBR)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ebr_council_tax_rebate:
  - Type: float
  - Entity: household
  - Description: Council Tax Rebate (EBR)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- energy_bills_rebate:
  - Type: float
  - Entity: household
  - Description: Energy Bills Rebate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- CTC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit child element
  - Mean: 1,035.3
  - Median: 0.0
  - Stddev: 2,447.4
  - Non-zero count: 5,534,097.1634225845


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.7
  - Median: 0.0
  - Stddev: 64.0
  - Non-zero count: 5,727.315673828125


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 22.0
  - Median: 0.0
  - Stddev: 128.6
  - Non-zero count: 1,134,143.1594429016


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 1,058.1
  - Median: 0.0
  - Stddev: 2,518.3
  - Non-zero count: 5,534,097.1634225845


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 15.9
  - Non-zero count: 1,638.0720825195312


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 66.5
  - Median: 0.0
  - Stddev: 507.0
  - Non-zero count: 614,159.9206428528


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 9.5
  - Median: 0.0
  - Stddev: 283.4
  - Non-zero count: 113,135.74792480469


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 20.1
  - Median: 0.0
  - Stddev: 219.0
  - Non-zero count: 276,141.2924423218


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 4.3
  - Median: 0.0
  - Stddev: 138.3
  - Non-zero count: 37,376.29712295532


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 19.2
  - Median: 0.0
  - Stddev: 249.3
  - Non-zero count: 263,497.57319259644


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 132.0
  - Median: 0.0
  - Stddev: 1,081.3
  - Non-zero count: 614,159.9206428528


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 53.7
  - Non-zero count: 24,529.226123809814


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 11.3
  - Median: 0.0
  - Stddev: 103.5
  - Non-zero count: 383,242.2122268677


- baseline_has_child_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Tax Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 961,896.3875312805


- baseline_has_working_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Working Tax Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 484,952.5986404419


- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit
  - Mean: 191.0
  - Median: 0.0
  - Stddev: 1,411.3
  - Non-zero count: 961,896.3875312805


- child_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit pre-minimum
  - Mean: 340.7
  - Median: 0.0
  - Stddev: 1,713.8
  - Non-zero count: 1,989,142.874680519


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 105.7
  - Median: 0.0
  - Stddev: 1,165.8
  - Non-zero count: 1,275,339.1542663574


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit child limit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 56,665,915.07962036


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,134,143.1594429016


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 614,159.9206428528


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,590,278.30052185


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 399.2
  - Median: 0.0
  - Stddev: 2,060.9
  - Non-zero count: 2,092,851.344590187


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 32,442.4
  - Median: 24,719.6
  - Stddev: 39,775.4
  - Non-zero count: 25,347,114.61185962


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 10,327.1
  - Median: 6,895.1
  - Stddev: 15,544.0
  - Non-zero count: 23,682,263.11110145


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 58.5
  - Median: 0.0
  - Stddev: 652.0
  - Non-zero count: 484,952.5986404419


- working_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit pre-minimum
  - Mean: 58.5
  - Median: 0.0
  - Stddev: 652.0
  - Non-zero count: 484,952.5986404419


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 30.3
  - Median: 0.0
  - Stddev: 440.5
  - Non-zero count: 792,710.1897277832


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,008,131.137295812


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 27,660,460.87739286


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 16.7
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 195,917.82421875


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 16.7
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 195,917.82421875


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 11,084.580688476562


- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 11,084.580688476562


- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 11.5
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 28,313.573608398438


- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 11.5
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 28,313.573608398438


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: nan
  - Median: 13,399.9
  - Stddev: nan
  - Non-zero count: 28,092,421.266079992


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,195,114.8888964653


- PIP:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 126.1
  - Median: 0.0
  - Stddev: 952.6
  - Non-zero count: 1,466,802.148147583


- PIP_DL:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 86.2
  - Median: 0.0
  - Stddev: 634.2
  - Non-zero count: 1,392,952.7093353271


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 86.2
  - Median: 0.0
  - Stddev: 634.2
  - Non-zero count: 1,392,952.7093353271


- PIP_M:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 39.9
  - Median: 0.0
  - Stddev: 373.6
  - Non-zero count: 1,034,654.728805542


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 39.9
  - Median: 0.0
  - Stddev: 373.6
  - Non-zero count: 1,034,654.728805542


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,539,222.061416626


- state_pension:
  - Type: float
  - Entity: person
  - Description: State Pension
  - Mean: 1,530.7
  - Median: 0.0
  - Stddev: 3,532.6
  - Non-zero count: 11,102,558.218399048


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 59,876,255.938705444


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,530.7
  - Median: 0.0
  - Stddev: 3,532.6
  - Non-zero count: 11,102,558.218399048


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 59,876,255.938705444


- DLA:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 83.5
  - Median: 0.0
  - Stddev: 770.4
  - Non-zero count: 1,077,625.705329895


- DLA_M:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 34.2
  - Median: 0.0
  - Stddev: 350.5
  - Non-zero count: 778,417.1420211792


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 34.2
  - Median: 0.0
  - Stddev: 350.5
  - Non-zero count: 778,417.1420211792


- DLA_SC:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 49.3
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 940,993.9589004517


- DLA_SC_middle_plus:
  - Type: bool
  - Entity: person
  - Description: Receives at least DLA (self-care) middle rate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 940,993.9589004517


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 49.3
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 940,993.9589004517


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 8,545.0
  - Median: 7,778.7
  - Stddev: 2,320.1
  - Non-zero count: 28,092,421.266079992


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 1.5
  - Median: 1.0
  - Stddev: 1.1
  - Non-zero count: 28,092,421.266079992


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 1,864.7
  - Median: -52.0
  - Stddev: 2,912.0
  - Non-zero count: 9,177,681.268699765


- LHA_category:
  - Type: Categorical
  - Entity: benunit
  - Description: LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms


- LHA_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for Local Housing Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ESA_contrib:
  - Type: float
  - Entity: person
  - Description: ESA (contribution-based)
  - Mean: 27.7
  - Median: 0.0
  - Stddev: 513.4
  - Non-zero count: 263,950.1912918091


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 27.7
  - Median: 0.0
  - Stddev: 513.4
  - Non-zero count: 263,950.1912918091


- incapacity_benefit:
  - Type: float
  - Entity: person
  - Description: Incapacity Benefit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- incapacity_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Incapacity Benefit (reported)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- carers_allowance:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance
  - Mean: 28.6
  - Median: 0.0
  - Stddev: 366.3
  - Non-zero count: 500,395.9826889038


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 28.6
  - Median: 0.0
  - Stddev: 366.3
  - Non-zero count: 500,395.9826889038


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 500,395.9826889038


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 8.5
  - Median: 0.0
  - Stddev: 206.8
  - Non-zero count: 150,270.0536956787


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 8.5
  - Median: 0.0
  - Stddev: 206.8
  - Non-zero count: 150,270.0536956787


- SDA:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 18,648.00030517578


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 18,648.00030517578


- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 111.7
  - Median: 0.0
  - Stddev: 292.0
  - Non-zero count: 3,744,643.413277149


- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 55.8
  - Median: 0.0
  - Stddev: 217.0
  - Non-zero count: 3,965,834.141479492


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 81.9
  - Median: 0.0
  - Stddev: 261.1
  - Non-zero count: 4,177,125.4310302734


- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 101.6
  - Median: 0.0
  - Stddev: 548.8
  - Non-zero count: 1,982,211.0823431015


- baseline_has_housing_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Housing Benefit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,807,896.166847229


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 281.0
  - Median: 0.0
  - Stddev: 1,088.5
  - Non-zero count: 1,807,896.166847229


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 691.2
  - Median: 0.0
  - Stddev: 2,759.7
  - Non-zero count: 2,062,073.7079906464


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 25,784.2
  - Median: 21,456.5
  - Stddev: 23,844.4
  - Non-zero count: 26,791,058.199464023


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,062,073.7079906464


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 219.3
  - Median: 0.0
  - Stddev: 1,103.3
  - Non-zero count: 2,760,301.7188034058


- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,092,421.266079992


- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 4.5
  - Median: 0.0
  - Stddev: 261.5
  - Non-zero count: 31,727.058715820312


- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 6.1
  - Median: 0.0
  - Stddev: 143.3
  - Non-zero count: 74,220.50521850586


- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 52.5
  - Non-zero count: 19,816.086944580078


- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 41.0
  - Median: 0.0
  - Stddev: 630.1
  - Non-zero count: 458,884.9896850586


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 246.2
  - Median: 0.0
  - Stddev: 1,334.3
  - Non-zero count: 1,431,643.3071594238


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 52.0
  - Median: 0.0
  - Stddev: 710.7
  - Non-zero count: 558,112.798034668


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 4.5
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 55,657.41680908203


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 4.5
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 55,657.41680908203


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 11.4
  - Median: 0.0
  - Stddev: 240.3
  - Non-zero count: 78,994.99809265137


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 8.4
  - Median: 0.0
  - Stddev: 213.8
  - Non-zero count: 56,432.37016296387


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 8.9
  - Median: 0.0
  - Stddev: 224.0
  - Non-zero count: 58,529.71684265137


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 25,281.0
  - Median: 20,742.1
  - Stddev: 25,322.0
  - Non-zero count: 25,379,804.428799927


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 58,529.71684265137


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 11.7
  - Median: 0.0
  - Stddev: 243.0
  - Non-zero count: 182,841.09809875488


- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 136,148.54418945312


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 1.7
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 26,808.029022216797


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 1.7
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 26,808.029022216797


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 89.5
  - Median: 0.0
  - Stddev: 1,024.6
  - Non-zero count: 376,525.5848207474


- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 376,525.5848207474


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 50.6
  - Median: 0.0
  - Stddev: 739.9
  - Non-zero count: 470,448.34870910645


- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 193,526.79188346863


- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 376,525.5848207474


- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 72.0
  - Median: 0.0
  - Stddev: 111.1
  - Non-zero count: 8,725,848.752082825


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 33.8
  - Median: 0.0
  - Stddev: 74.7
  - Non-zero count: 11,244,194.193183899


- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 326.4
  - Median: 0.0
  - Stddev: 1,291.7
  - Non-zero count: 2,144,565.928066492


- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 4,132,269.6755218506


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 14,460.4
  - Median: 2,971.7
  - Stddev: 25,921.2
  - Non-zero count: 30,539,385.690460205


- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 27.7
  - Median: 0.0
  - Stddev: 284.8
  - Non-zero count: 397,313.61613321304


- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1,011.0
  - Median: 0.0
  - Stddev: 2,429.8
  - Non-zero count: 5,825,346.636925697


- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 131.3
  - Median: 0.0
  - Stddev: 1,029.8
  - Non-zero count: 1,146,646.0910902023


- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 14,638,078.25081575


- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 329.9
  - Median: 0.0
  - Stddev: 1,329.8
  - Non-zero count: 2,144,565.928066492


- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 18,904.2
  - Median: 14,803.1
  - Stddev: 24,905.2
  - Non-zero count: 17,746,323.89029491


- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1,319.0
  - Median: 0.0
  - Stddev: 2,752.5
  - Non-zero count: 6,457,009.677861333


- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 15,111.9
  - Median: 12,303.6
  - Stddev: 17,716.5
  - Non-zero count: 24,516,338.96036583


- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 517.5
  - Median: 0.0
  - Stddev: 1,273.1
  - Non-zero count: 9,999,096.330795288


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 0.8
  - Median: 0.0
  - Stddev: 44.9
  - Non-zero count: 32,026.66973876953


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 74.2
  - Median: 0.0
  - Stddev: 216.5
  - Non-zero count: 4,899,729.108123779


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 1.6
  - Median: 0.0
  - Stddev: 103.2
  - Non-zero count: 20,462.967895507812


- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 8,791.2
  - Median: 7,159.0
  - Stddev: 4,882.7
  - Non-zero count: 28,092,222.296765417


- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8,340.8
  - Median: 7,756.2
  - Stddev: 1,884.9
  - Non-zero count: 28,092,421.266079992


- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 14,308.8
  - Median: 15,870.4
  - Stddev: 3,172.6
  - Non-zero count: 59,876,255.938705444


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 4,247,424.279891968


- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 93.3
  - Median: 0.0
  - Stddev: 477.4
  - Non-zero count: 2,288,622.8792604804


- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 5,972.3
  - Median: 5,887.2
  - Stddev: 1,189.6
  - Non-zero count: 28,092,421.266079992


- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 3,202.2
  - Median: 12.4
  - Stddev: 11,298.5
  - Non-zero count: 16,231,279.322051942


- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1,485.6
  - Median: 0.0
  - Stddev: 2,593.3
  - Non-zero count: 7,671,045.263600588


- baseline_has_universal_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Universal Credit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,907,425.6306681633


- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 20,908,645.53451225


- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 7,671,045.263600588


- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,259,544.658752441


- is_in_startup_period:
  - Type: bool
  - Entity: person
  - Description: In a start-up period
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- legacy_benefits:
  - Type: float
  - Entity: benunit
  - Description: Legacy benefits
  - Mean: 655.5
  - Median: 0.0
  - Stddev: 2,616.6
  - Non-zero count: 3,025,482.519932747


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,539,559.693687439


- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 5,825,346.636925697


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 1,404.3
  - Median: 0.0
  - Stddev: 4,226.8
  - Non-zero count: 5,239,215.256049186


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 167.5
  - Median: 0.0
  - Stddev: 1,446.9
  - Non-zero count: 1,210,824.3150634766


- would_claim_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 23,694,254.72731504


- baseline_has_pension_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Pension Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 644,364.6105289459


- guarantee_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 28,417.4
  - Median: 23,558.6
  - Stddev: 25,827.9
  - Non-zero count: 26,963,400.569173038


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 44.2
  - Median: 0.0
  - Stddev: 389.2
  - Non-zero count: 644,364.6105289459


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 36.0
  - Median: 0.0
  - Stddev: 365.6
  - Non-zero count: 404,141.5760746002


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 447.8
  - Median: 0.0
  - Stddev: 1,990.2
  - Non-zero count: 1,262,389.0961551666


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 8.2
  - Median: 0.0
  - Stddev: 109.5
  - Non-zero count: 366,071.89389038086


- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,047,755.088157058


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 69.0
  - Median: 0.0
  - Stddev: 578.8
  - Non-zero count: 1,413,822.377067566


- savings_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Savings Credit
  - Mean: 28,245.3
  - Median: 23,318.9
  - Stddev: 25,888.8
  - Non-zero count: 26,929,752.695759952


- would_claim_PC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,329,832.48843956


- baseline_has_income_support:
  - Type: bool
  - Entity: benunit
  - Description: Receives Income Support (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 139,353.55506896973


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 27.2
  - Median: 0.0
  - Stddev: 609.6
  - Non-zero count: 139,353.55506896973


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 36.2
  - Median: 0.0
  - Stddev: 798.9
  - Non-zero count: 144,116.52680969238


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 25,281.0
  - Median: 20,742.1
  - Stddev: 25,322.0
  - Non-zero count: 25,379,804.428799927


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 144,116.52680969238


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 16.6
  - Median: 0.0
  - Stddev: 382.1
  - Non-zero count: 263,406.03368377686


- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,092,421.266079992


- AA:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 58.6
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 890,308.0251922607


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 58.6
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 890,308.0251922607


- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 111.4
  - Median: 16.1
  - Stddev: 311.0
  - Non-zero count: 19,439,238.115867615


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 111.4
  - Median: 16.1
  - Stddev: 311.0
  - Non-zero count: 19,439,238.115867615


- corporate_sdlt_change_incidence:
  - Type: float
  - Entity: household
  - Description: Corporate Stamp Duty
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected)
  - Mean: 177.3
  - Median: 22.6
  - Stddev: 802.2
  - Non-zero count: 19,765,385.926994324


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 24,845,880.935256958


- sdlt_on_non_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on non-residential property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- sdlt_on_non_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on non-residential property
  - Mean: 37.4
  - Median: 0.0
  - Stddev: 1,251.2
  - Non-zero count: 96,044.61138916016


- sdlt_on_rent:
  - Type: float
  - Entity: household
  - Description: SDLT on property rental
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- sdlt_on_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on residential property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- sdlt_on_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on residential property
  - Mean: 1,279.8
  - Median: 0.0
  - Stddev: 13,658.0
  - Non-zero count: 2,834,169.150138855


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 1,317.2
  - Median: 0.0
  - Stddev: 13,803.2
  - Non-zero count: 2,878,722.4076156616


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 1,219.5
  - Median: 0.0
  - Stddev: 12,676.5
  - Non-zero count: 2,616,067.035636902


- baseline_has_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Benefit (baseline)
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,092,421.266079992


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 243.6
  - Median: 0.0
  - Stddev: 701.3
  - Non-zero count: 4,363,232.991959572


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 229.9
  - Median: 0.0
  - Stddev: 681.7
  - Non-zero count: 4,201,694.480545998


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 125.7
  - Median: 0.0
  - Stddev: 537.8
  - Non-zero count: 4,881,404.336135864


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 150.4
  - Median: 0.0
  - Stddev: 388.0
  - Non-zero count: 9,590,278.30052185


- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,559,127.837574005


- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 1,129.6
  - Median: 163.7
  - Stddev: 3,152.6
  - Non-zero count: 19,439,238.115867615


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,129.6
  - Median: 163.7
  - Stddev: 3,152.6
  - Non-zero count: 19,439,238.115867615


- business_rates_change_incidence:
  - Type: float
  - Entity: household
  - Description: Business rates changes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- benunit_tax:
  - Type: float
  - Entity: benunit
  - Description: Benefit unit tax paid
  - Mean: 5,805.2
  - Median: 2,568.3
  - Stddev: 14,004.0
  - Non-zero count: 20,056,853.108722985


- household_tax:
  - Type: float
  - Entity: household
  - Description: Taxes
  - Mean: 9,352.0
  - Median: 6,082.0
  - Stddev: 16,796.9
  - Non-zero count: 27,953,980.130088806


- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,103.2
  - Median: 200.2
  - Stddev: 9,388.3
  - Non-zero count: 31,740,857.963806152


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,103.2
  - Median: 200.2
  - Stddev: 9,388.3
  - Non-zero count: 31,740,857.963806152


- tax_reported:
  - Type: float
  - Entity: person
  - Description: Reported tax paid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 8.5
  - Median: 0.0
  - Stddev: 33.8
  - Non-zero count: 3,209,250.3647460938


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 8.5
  - Median: 0.0
  - Stddev: 33.8
  - Non-zero count: 3,209,250.3647460938


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 19,647,769.434936523


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 920.4
  - Median: 0.0
  - Stddev: 1,563.6
  - Non-zero count: 23,347,024.632232666


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,238.5
  - Median: 0.0
  - Stddev: 2,917.4
  - Non-zero count: 23,802,478.31640625


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,238.5
  - Median: 0.0
  - Stddev: 2,917.4
  - Non-zero count: 23,802,478.31640625


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,231.8
  - Median: 0.0
  - Stddev: 4,365.8
  - Non-zero count: 26,786,767.591430664


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 72.1
  - Median: 0.0
  - Stddev: 487.7
  - Non-zero count: 2,849,275.794494629


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 920.4
  - Median: 0.0
  - Stddev: 1,563.6
  - Non-zero count: 23,347,024.632232666


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 993.3
  - Median: 0.0
  - Stddev: 1,602.0
  - Non-zero count: 26,139,419.104888916


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 80.6
  - Median: 0.0
  - Stddev: 510.7
  - Non-zero count: 3,209,250.3647460938


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 116.3
  - Median: 0.0
  - Stddev: 8,396.0
  - Non-zero count: 124,075.99499511719


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 52.3
  - Median: 0.0
  - Stddev: 3,775.5
  - Non-zero count: 124,075.99499511719


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 21.4
  - Non-zero count: 1,320.951171875


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7,545.8
  - Median: 0.0
  - Stddev: 11,526.0
  - Non-zero count: 29,006,156.331939697


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,509.2
  - Median: 0.0
  - Stddev: 2,305.9
  - Non-zero count: 29,006,156.331939697


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 9.4
  - Median: 0.0
  - Stddev: 404.9
  - Non-zero count: 81,586.84869384766


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 15.7
  - Median: 0.0
  - Stddev: 419.5
  - Non-zero count: 507,287.9750061035


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 20.1
  - Median: 0.0
  - Stddev: 463.2
  - Non-zero count: 733,426.3788146973


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,080.8
  - Median: 0.0
  - Stddev: 8,148.3
  - Non-zero count: 29,006,156.331939697


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 8,950.3
  - Median: 0.0
  - Stddev: 23,434.8
  - Non-zero count: 29,006,156.331939697


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 1,288.2
  - Median: 0.0
  - Stddev: 11,068.1
  - Non-zero count: 2,997,694.490966797


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 515.3
  - Median: 0.0
  - Stddev: 4,426.2
  - Non-zero count: 2,997,694.490966797


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 1.1
  - Median: 0.0
  - Stddev: 210.4
  - Non-zero count: 12,287.21435546875


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2,109.9
  - Median: 0.0
  - Stddev: 8,256.9
  - Non-zero count: 29,302,713.950012207


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,103.1
  - Median: 0.0
  - Stddev: 8,229.7
  - Non-zero count: 29,302,713.950012207


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 34,791,036.69581604


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,290,700.893951416


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 2.3
  - Median: 0.0
  - Stddev: 129.7
  - Non-zero count: 88,939.7349243164


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,989.0
  - Median: 5,000.0
  - Stddev: 191.2
  - Non-zero count: 59,834,330.64640808


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 121.0
  - Median: 0.0
  - Stddev: 1,814.4
  - Non-zero count: 733,426.3788146973


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 9,081.8
  - Median: 0.0
  - Stddev: 23,679.2
  - Non-zero count: 29,302,713.950012207


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 10.5
  - Median: 0.0
  - Stddev: 497.4
  - Non-zero count: 88,939.7349243164


- ISA_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount received in interest from Individual Savings Accounts
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- SMP:
  - Type: float
  - Entity: person
  - Description: Statutory Maternity Pay
  - Mean: 17.8
  - Median: 0.0
  - Stddev: 378.5
  - Non-zero count: 142,048.86807250977


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 6.8
  - Median: 0.0
  - Stddev: 170.3
  - Non-zero count: 108,290.98146057129


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17,017.3
  - Median: 12,276.0
  - Stddev: 25,692.2
  - Non-zero count: 45,482,116.81967163


- capital_allowances:
  - Type: float
  - Entity: person
  - Description: Full relief from capital expenditure allowances
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- deficiency_relief:
  - Type: float
  - Entity: person
  - Description: Deficiency relief
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- employment_benefits:
  - Type: float
  - Entity: person
  - Description: Employment benefits
  - Mean: 24.5
  - Median: 0.0
  - Stddev: 417.2
  - Non-zero count: 249,633.79972839355


- employment_deductions:
  - Type: float
  - Entity: person
  - Description: Deductions from employment income
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- employment_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of expenses necessarily incurred and reimbursed by employment
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- loss_relief:
  - Type: float
  - Entity: person
  - Description: Tax relief from trading losses
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- pension_contributions:
  - Type: float
  - Entity: person
  - Description: Amount contributed to registered pension schemes paid by the individual (not the employer)
  - Mean: 481.5
  - Median: 0.0
  - Stddev: 1,319.8
  - Non-zero count: 18,730,079.222808838


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,830.8
  - Median: 432.3
  - Stddev: 2,065.8
  - Non-zero count: 29,976,638.57208252


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 36.7
  - Median: 0.0
  - Stddev: 380.0
  - Non-zero count: 8,639,620.944915771


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 157.4
  - Median: 0.0
  - Stddev: 1,944.9
  - Non-zero count: 3,279,365.0158081055


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 12,264.7
  - Median: 52.0
  - Stddev: 22,898.1
  - Non-zero count: 31,475,130.03616333


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 41.0
  - Median: 0.0
  - Stddev: 828.2
  - Non-zero count: 655,234.8271789551


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1,319.0
  - Median: 0.0
  - Stddev: 6,889.5
  - Non-zero count: 8,754,985.381484985


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 184.9
  - Median: 0.0
  - Stddev: 2,039.8
  - Non-zero count: 1,467,340.1133422852


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 54.4
  - Median: 0.0
  - Stddev: 590.1
  - Non-zero count: 20,862,928.372428894


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1,407.3
  - Median: 0.0
  - Stddev: 11,744.1
  - Non-zero count: 3,990,600.023422241


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,588.7
  - Median: 0.0
  - Stddev: 3,555.8
  - Non-zero count: 11,861,384.4294281


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17,469.8
  - Median: 12,319.2
  - Stddev: 26,420.0
  - Non-zero count: 43,227,345.47755432


- trading_loss:
  - Type: float
  - Entity: person
  - Description: Loss from trading in the current year.
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- dividend_income:
  - Type: float
  - Entity: person
  - Description: Income from dividends
  - Mean: 157.4
  - Median: 0.0
  - Stddev: 1,944.9
  - Non-zero count: 3,279,365.0158081055


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 12,707.5
  - Median: 0.0
  - Stddev: 23,698.4
  - Non-zero count: 26,235,250.23677063


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1,319.0
  - Median: 0.0
  - Stddev: 6,889.5
  - Non-zero count: 8,754,985.381484985


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 101.6
  - Median: -108.1
  - Stddev: 2,138.6
  - Non-zero count: 1,849,672.801750183


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 91.1
  - Median: 0.0
  - Stddev: 758.1
  - Non-zero count: 20,862,928.372428894


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 1,463.5
  - Median: 0.0
  - Stddev: 11,885.6
  - Non-zero count: 4,132,269.6755218506


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,588.7
  - Median: 0.0
  - Stddev: 3,555.8
  - Non-zero count: 11,861,384.4294281


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 161.8
  - Median: 0.0
  - Stddev: 422.9
  - Non-zero count: 8,119,189.067260742


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 56,689,530.86955261


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 278.9
  - Median: 0.0
  - Stddev: 5,831.3
  - Non-zero count: 12,035,421.87097168


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 4,628.6
  - Median: 224.0
  - Stddev: 5,641.9
  - Non-zero count: 30,312,319.41685486


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,433.5
  - Median: 12,500.0
  - Stddev: 1,156.3
  - Non-zero count: 59,660,162.92539978


- blind_persons_allowance:
  - Type: float
  - Entity: person
  - Description: Blind Person's Allowance for the year (not simulated)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- charitable_investment_gifts:
  - Type: float
  - Entity: person
  - Description: Gifts of qualifying investment or property to charities
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- covenanted_payments:
  - Type: float
  - Entity: person
  - Description: Covenanted payments to charities
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- dividend_allowance:
  - Type: float
  - Entity: person
  - Description: Dividend allowance for the person
  - Mean: 2,000.0
  - Median: 2,000.0
  - Stddev: 0.0
  - Non-zero count: 59,876,255.938705444


- gift_aid:
  - Type: float
  - Entity: person
  - Description: Expenditure under Gift Aid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- married_couples_allowance:
  - Type: float
  - Entity: person
  - Description: Married Couples' allowance for the year
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- married_couples_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction from Married Couples' allowance for the year
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- other_deductions:
  - Type: float
  - Entity: person
  - Description: All other tax deductions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- pension_annual_allowance:
  - Type: float
  - Entity: person
  - Description: Annual Allowance for pension contributions
  - Mean: 39,987.6
  - Median: 40,000.0
  - Stddev: 1,290.1
  - Non-zero count: 59,876,255.938705444


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,433.5
  - Median: 12,500.0
  - Stddev: 1,156.3
  - Non-zero count: 59,660,162.92539978


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 59,876,255.938705444


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: -83.3
  - Median: -108.1
  - Stddev: 180.0
  - Non-zero count: 1,849,672.801750183


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 972.3
  - Median: 1,000.0
  - Stddev: 136.4
  - Non-zero count: 59,751,272.67979431


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 59,876,255.938705444


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 56.3
  - Median: 0.0
  - Stddev: 615.9
  - Non-zero count: 4,132,269.6755218506


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 6.7
  - Median: 0.0
  - Stddev: 125.4
  - Non-zero count: 400,849.404296875


- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 13.1
  - Median: 0.0
  - Stddev: 460.9
  - Non-zero count: 391,463.59912109375


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 243.4
  - Median: 0.0
  - Stddev: 8,539.0
  - Non-zero count: 391,463.59912109375


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,730,697.2336425781


- lbtt_on_non_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LBTT on non-residential property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- lbtt_on_non_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on non-residential property transactions
  - Mean: 34.7
  - Median: 0.0
  - Stddev: 1,215.4
  - Non-zero count: 96,044.61138916016


- lbtt_on_rent:
  - Type: float
  - Entity: household
  - Description: LBTT on property rental
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- lbtt_on_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LBTT on residential property rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- lbtt_on_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on residential property
  - Mean: 4,525.2
  - Median: 0.0
  - Stddev: 21,318.9
  - Non-zero count: 7,297,493.767539978


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 4,560.0
  - Median: 0.0
  - Stddev: 21,473.6
  - Non-zero count: 7,318,052.414268494


- expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (expected)
  - Mean: 6.7
  - Median: 0.0
  - Stddev: 186.4
  - Non-zero count: 333,779.65423583984


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 123.3
  - Median: 0.0
  - Stddev: 3,453.7
  - Non-zero count: 333,779.65423583984


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,515,843.1001586914


- ltt_on_non_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LTT on non-residential property rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ltt_on_non_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on non-residential property transactions
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 124.4
  - Non-zero count: 6,777.738037109375


- ltt_on_rent:
  - Type: float
  - Entity: household
  - Description: LTT on property rental
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ltt_on_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LTT on residential property rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ltt_on_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on residential property
  - Mean: 3,518.3
  - Median: 0.0
  - Stddev: 18,137.6
  - Non-zero count: 7,297,493.767539978


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 3,520.2
  - Median: 0.0
  - Stddev: 18,137.9
  - Non-zero count: 7,301,952.366539001


# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2020) 2019-20 Family Resources Survey, with simulation turned on.


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3,393.2
  - Median: 0.0
  - Stddev: 6,773.8
  - Non-zero count: 23,675,632.63911438


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 609.2
  - Median: 0.0
  - Stddev: 3,945.1
  - Non-zero count: 11,969,883.281951904


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 370.7
  - Median: 0.0
  - Stddev: 1,605.5
  - Non-zero count: 2,482,052.3710803986


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2,784.0
  - Median: 0.0
  - Stddev: 5,231.5
  - Non-zero count: 21,923,201.132217407


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 33.2
  - Median: 36.0
  - Stddev: 31.4
  - Non-zero count: 18,168,681.777121544


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
  - Non-zero count: 14,644,653.826180458


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1,339.6
  - Median: 0.0
  - Stddev: 4,983.2
  - Non-zero count: 13,369,573.442932129


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 959.0
  - Median: 0.0
  - Stddev: 3,105.0
  - Non-zero count: 12,582,321.062561035


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 7,789.8
  - Median: 4,128.0
  - Stddev: 10,102.6
  - Non-zero count: 19,411,050.363998413


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,038,771.41885376


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,997,365.380493164


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 15,177,202.64338398


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,825,871.2057886124


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 13,734,762.460568428


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 12,371,247.97512722


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -609.2
  - Median: 0.0
  - Stddev: 3,945.1
  - Non-zero count: 6,889,008.992279053


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,053.6
  - Median: 0.0
  - Stddev: 4,294.6
  - Non-zero count: 15,539,219.055160522


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1,825.0
  - Median: 0.0
  - Stddev: 4,032.6
  - Non-zero count: 13,950,635.109207153


- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: -1,355.8
  - Median: -202.4
  - Stddev: 3,512.1
  - Non-zero count: 0.0


- hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income
  - Mean: -1,355.8
  - Median: -202.4
  - Stddev: 3,512.1
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
  - Non-zero count: 1,169,352.2942810059


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 703,707.49609375


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,716,771.0956115723


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 4,164,309.609161377


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 647.5
  - Median: 0.0
  - Stddev: 2,113.9
  - Non-zero count: 3,716,771.0956115723


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 573.8
  - Median: 0.0
  - Stddev: 1,905.5
  - Non-zero count: 4,164,309.609161377


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 14,253.1
  - Median: 13,876.2
  - Stddev: 5,719.5
  - Non-zero count: 28,911,965.107925415


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 16,817.8
  - Median: 16,195.3
  - Stddev: 5,552.8
  - Non-zero count: 28,911,965.107925415


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
  - Mean: 1,008.9
  - Median: 0.0
  - Stddev: 2,145.3
  - Non-zero count: 22,839,082.694641113


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 15,480.3
  - Median: 5,720.0
  - Stddev: 26,078.0
  - Non-zero count: 37,898,471.16407776


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 34,003.9
  - Median: 28,781.3
  - Stddev: 21,605.7
  - Non-zero count: 28,753,396.73851013


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 32,123.2
  - Median: 26,911.4
  - Stddev: 22,372.0
  - Non-zero count: 28,573,718.14390564


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 32,682.8
  - Median: 27,715.8
  - Stddev: 20,679.2
  - Non-zero count: 28,694,706.610458374


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 20,386.5
  - Median: 14,567.8
  - Stddev: 26,177.1
  - Non-zero count: 48,739,245.00135803


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 36,564.5
  - Median: 29,598.2
  - Stddev: 27,090.1
  - Non-zero count: 28,753,396.73851013


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 34,032.9
  - Median: 26,723.2
  - Stddev: 27,311.3
  - Non-zero count: 28,573,718.14390564


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 898.7
  - Median: 0.0
  - Stddev: 1,034.5
  - Non-zero count: 31,891,557.02645874


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 46,412.3
  - Median: 34,374.9
  - Stddev: 41,432.6
  - Non-zero count: 28,813,841.707504272


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 38,622.5
  - Median: 26,637.7
  - Stddev: 44,457.9
  - Non-zero count: 24,231,909.82344055


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 35,208.7
  - Median: 28,575.0
  - Stddev: 26,235.2
  - Non-zero count: 28,694,706.610458374


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 31,892,454.255218506


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
  - Mean: 83.5
  - Median: -1.0
  - Stddev: 1,944.1
  - Non-zero count: 252,695.38507080078


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 36.3
  - Median: 0.0
  - Stddev: 515.9
  - Non-zero count: 744,174.6753845215


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 16,993.3
  - Median: 7,259.2
  - Stddev: 26,574.0
  - Non-zero count: 40,784,862.36000061


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.7
  - Median: 8.7
  - Stddev: 1.7
  - Non-zero count: 65,711,194.14491272


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 60.9
  - Median: 0.0
  - Stddev: 828.2
  - Non-zero count: 872,490.9592895508


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 16,687.1
  - Median: 14,066.8
  - Stddev: 17,747.5
  - Non-zero count: 48,739,245.00135803


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: 86.6
  - Median: 0.0
  - Stddev: 1,219.7
  - Non-zero count: 801,082.5107116699


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
  - Mean: 17.3
  - Median: 0.0
  - Stddev: 19.9
  - Non-zero count: 31,891,557.02645874


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
  - Mean: 141,773.5
  - Median: 17,706.4
  - Stddev: 379,696.8
  - Non-zero count: 19,754,560.831863403


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 19,754,560.831863403


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 186,403.4
  - Median: 135,000.0
  - Stddev: 241,917.5
  - Non-zero count: 18,513,761.279571533


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 2,034.4
  - Median: 0.0
  - Stddev: 34,377.7
  - Non-zero count: 217,408.7152709961


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 10,694.2
  - Median: 0.0
  - Stddev: 64,683.9
  - Non-zero count: 1,429,464.1913757324


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 220,761.2
  - Median: 139,999.0
  - Stddev: 322,277.5
  - Non-zero count: 18,899,320.63571167


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 197,097.6
  - Median: 135,000.0
  - Stddev: 262,398.8
  - Non-zero count: 18,630,739.037139893


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 60,799.0
  - Median: 7,593.3
  - Stddev: 162,834.6
  - Non-zero count: 19,754,560.831863403


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 149,043.4
  - Median: 94,518.1
  - Stddev: 217,597.2
  - Non-zero count: 18,899,320.63571167


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 209,842.4
  - Median: 124,899.8
  - Stddev: 313,357.5
  - Non-zero count: 23,591,220.93309021


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
  - Mean: 10,694.2
  - Median: 0.0
  - Stddev: 64,683.9
  - Non-zero count: 1,429,464.1913757324


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
  - Mean: 186,403.4
  - Median: 135,000.0
  - Stddev: 241,917.5
  - Non-zero count: 18,513,761.279571533


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,398,008.286743164


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 2,034.4
  - Median: 0.0
  - Stddev: 34,377.7
  - Non-zero count: 217,408.7152709961


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
  - Non-zero count: 28,911,965.107925415


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
  - Mean: 2,531.6
  - Median: -52.0
  - Stddev: 4,221.4
  - Non-zero count: 10,218,780.624267578


- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2,306.3
  - Median: -52.0
  - Stddev: 3,968.6
  - Non-zero count: 9,514,608.44004631


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 102.8
  - Median: 0.0
  - Stddev: 881.8
  - Non-zero count: 2,594,939.3011169434


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,439.9
  - Median: 1,386.7
  - Stddev: 751.4
  - Non-zero count: 27,767,170.35961914


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,296.1
  - Median: 1,334.0
  - Stddev: 859.0
  - Non-zero count: 25,813,108.92807007


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
  - Mean: 2,306.3
  - Median: -52.0
  - Stddev: 3,968.6
  - Non-zero count: 9,514,608.44004631


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 2,531.6
  - Median: -52.0
  - Stddev: 4,221.4
  - Non-zero count: 10,218,780.624267578


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 72.3
  - Median: 0.0
  - Stddev: 339.3
  - Non-zero count: 2,822,922.3428344727


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 36.6
  - Median: 0.0
  - Stddev: 621.9
  - Non-zero count: 689,313.8066711426


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
  - Mean: 2,349.0
  - Median: 0.0
  - Stddev: 5,618.7
  - Non-zero count: 8,529,131.011413574


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 896.1
  - Median: -52.0
  - Stddev: 2,093.5
  - Non-zero count: 8,504,181.418762207


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 430.7
  - Median: 0.0
  - Stddev: 1,299.7
  - Non-zero count: 18,102,600.12069702


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,113.9
  - Median: 0.0
  - Stddev: 3,035.7
  - Non-zero count: 10,218,780.624267578


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 30.4
  - Median: 0.0
  - Stddev: 172.5
  - Non-zero count: 2,159,188.5717163086


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 372.3
  - Median: 358.8
  - Stddev: 252.8
  - Non-zero count: 27,506,041.062927246


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 17.0
  - Non-zero count: 2,594,939.3011169434


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
  - Mean: 38.9
  - Median: 38.0
  - Stddev: 23.6
  - Non-zero count: 64,872,721.58442688


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 38,845,169.27163696


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,737,070.02268982


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 15,128,954.850585938


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1,982.1
  - Median: 1,983.0
  - Stddev: 23.6
  - Non-zero count: 65,711,194.14491272


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 77.3
  - Median: 100.0
  - Stddev: 41.2
  - Non-zero count: 65,711,194.14491272


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
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,767,996.920379639


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 39,468,537.69869995


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 50,582,239.29432678


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,473,443.216644287


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 34,964,548.49809265


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 15,128,954.850585938


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 9,091,382.238830566


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 33,312,546.642456055


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 28,911,965.107925415


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 32,398,647.502456665


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,597,864.013671875


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,531,090.836914062


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
  - Non-zero count: 52,502,282.70765686


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65,711,194.14491272


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 9,580,577.3
  - Median: 9,504,121.8
  - Stddev: 5,543,055.9
  - Non-zero count: 65,711,194.14491272


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight (region-adjusted)
  - Mean: 2,017.8
  - Median: 1,329.3
  - Stddev: 977.2
  - Non-zero count: 65,711,194.14491272


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 2,192.1
  - Median: 1,765.0
  - Stddev: 858.6
  - Non-zero count: 65,711,194.14491272


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 9,580,557.2
  - Median: 9,504,101.0
  - Stddev: 5,543,020.5
  - Non-zero count: 65,711,194.14491272


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 9,580,444.3
  - Median: 9,504,001.0
  - Stddev: 5,543,019.5
  - Non-zero count: 65,711,194.14491272


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
  - Non-zero count: 28,911,965.107925415


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 28,911,965.107925415


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 9,553,685.3
  - Median: 9,507,001.8
  - Stddev: 5,545,521.5
  - Non-zero count: 28,911,965.107925415


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.2
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 28,911,965.107925415


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.3
  - Median: 2.0
  - Stddev: 1.3
  - Non-zero count: 28,911,965.107925415


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 1,893.1
  - Median: 1,295.4
  - Stddev: 926.5
  - Non-zero count: 28,911,965.107925415


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,911,965.107925415


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
  - Mean: 2.7
  - Median: 3.0
  - Stddev: 1.0
  - Non-zero count: 28,911,965.107925415


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
  - Mean: 9,553,793.6
  - Median: 9,507,101.8
  - Stddev: 5,535,726.0
  - Non-zero count: 28,911,965.103952408


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
  - Mean: 1,722.5
  - Median: 1,174.3
  - Stddev: 831.2
  - Non-zero count: 28,911,965.103952408


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 51.5
  - Median: 52.0
  - Stddev: 18.7
  - Non-zero count: 28,911,965.103952408


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7,693,233.7809352875


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,911,965.103952408


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
  - Median: 2.0
  - Stddev: 0.5
  - Non-zero count: 28,702,626.325255394


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.9
  - Non-zero count: 8,195,191.299530983


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 49.6
  - Median: 49.0
  - Stddev: 18.6
  - Non-zero count: 28,911,965.103952408


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: inf
  - Stddev: nan
  - Non-zero count: 28,092,575.067987442


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
  - Non-zero count: 425,052.6935195923


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 28.7
  - Median: 0.0
  - Stddev: 284.0
  - Non-zero count: 425,052.6935195923


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 513,856.8141784668


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 425,052.6935195923


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 167.5
  - Median: 0.0
  - Stddev: 637.7
  - Non-zero count: 2,237,391.241334915


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 23.1
  - Non-zero count: 4,194.042724609375


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,658,249.3999176025


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 4,194.042724609375


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,122,289.3464660645


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,237,391.241334915


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 10,930.395538330078


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 4,194.042724609375


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
  - Non-zero count: 974,969.6818599701


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 4,894.720642089844


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 174.4
  - Median: 0.0
  - Stddev: 1,041.2
  - Non-zero count: 974,969.6818599701


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
  - Mean: 1,466.5
  - Median: 0.0
  - Stddev: 2,447.4
  - Non-zero count: 7,887,433.521061897


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.9
  - Median: 0.0
  - Stddev: 64.0
  - Non-zero count: 7,915.993804931641


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 33.0
  - Median: 0.0
  - Stddev: 128.6
  - Non-zero count: 1,753,012.7880325317


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 1,500.6
  - Median: 0.0
  - Stddev: 2,518.3
  - Non-zero count: 7,887,433.521061897


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 15.9
  - Non-zero count: 2,626.8327026367188


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 106.2
  - Median: 0.0
  - Stddev: 507.0
  - Non-zero count: 1,010,253.0668907166


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 10.7
  - Median: 0.0
  - Stddev: 283.4
  - Non-zero count: 170,213.98989868164


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 31.5
  - Median: 0.0
  - Stddev: 219.0
  - Non-zero count: 445,759.3232269287


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 5.2
  - Median: 0.0
  - Stddev: 138.3
  - Non-zero count: 46,367.88262939453


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 33.9
  - Median: 0.0
  - Stddev: 249.3
  - Non-zero count: 479,337.87733078003


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 206.1
  - Median: 0.0
  - Stddev: 1,081.3
  - Non-zero count: 1,010,253.0668907166


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 1.4
  - Median: 0.0
  - Stddev: 53.7
  - Non-zero count: 29,898.438507080078


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 17.2
  - Median: 0.0
  - Stddev: 103.5
  - Non-zero count: 601,793.8654632568


- baseline_has_child_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Tax Credit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,534,632.603302002


- baseline_has_working_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Working Tax Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 862,505.7742881775


- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit
  - Mean: 307.9
  - Median: 0.0
  - Stddev: 1,411.3
  - Non-zero count: 1,534,632.603302002


- child_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit pre-minimum
  - Mean: 459.6
  - Median: 0.0
  - Stddev: 1,713.8
  - Non-zero count: 2,577,008.7405672073


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 154.0
  - Median: 0.0
  - Stddev: 1,165.8
  - Non-zero count: 1,934,894.9606628418


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit child limit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 61,297,004.65986633


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,753,012.7880325317


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,010,253.0668907166


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,997,365.380493164


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 555.0
  - Median: 0.0
  - Stddev: 2,060.9
  - Non-zero count: 2,716,676.070839882


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 37,237.7
  - Median: 24,909.5
  - Stddev: 39,775.4
  - Non-zero count: 26,581,080.197249413


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 12,020.7
  - Median: 6,939.4
  - Stddev: 15,544.0
  - Non-zero count: 24,801,249.844441414


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 95.4
  - Median: 0.0
  - Stddev: 652.0
  - Non-zero count: 862,505.7742881775


- working_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit pre-minimum
  - Mean: 95.4
  - Median: 0.0
  - Stddev: 652.0
  - Non-zero count: 862,505.7742881775


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 42.0
  - Median: 0.0
  - Stddev: 440.5
  - Non-zero count: 1,240,432.037902832


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,794,797.699716568


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 28,291,911.57909584


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 16.1
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 205,800.5352783203


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 16.1
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 205,800.5352783203


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.0
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 8,943.712951660156


- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.0
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 8,943.712951660156


- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 9.5
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 25,825.583984375


- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 9.5
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 25,825.583984375


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: nan
  - Median: 13,399.9
  - Stddev: nan
  - Non-zero count: 28,911,965.103952408


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,648,081.991306305


- PIP:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 117.6
  - Median: 0.0
  - Stddev: 952.6
  - Non-zero count: 1,472,261.7880859375


- PIP_DL:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 79.9
  - Median: 0.0
  - Stddev: 634.2
  - Non-zero count: 1,404,365.5942382812


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 79.9
  - Median: 0.0
  - Stddev: 634.2
  - Non-zero count: 1,404,365.5942382812


- PIP_M:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 37.7
  - Median: 0.0
  - Stddev: 373.6
  - Non-zero count: 1,067,428.8192443848


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 37.7
  - Median: 0.0
  - Stddev: 373.6
  - Non-zero count: 1,067,428.8192443848


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,113,701.595626831


- state_pension:
  - Type: float
  - Entity: person
  - Description: State Pension
  - Mean: 1,491.1
  - Median: 0.0
  - Stddev: 3,532.6
  - Non-zero count: 11,734,882.066818237


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 65,711,194.14491272


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,491.1
  - Median: 0.0
  - Stddev: 3,532.6
  - Non-zero count: 11,734,882.066818237


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65,711,194.14491272


- DLA:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 86.6
  - Median: 0.0
  - Stddev: 770.4
  - Non-zero count: 1,192,372.5951080322


- DLA_M:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 33.8
  - Median: 0.0
  - Stddev: 350.5
  - Non-zero count: 866,501.6745758057


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 33.8
  - Median: 0.0
  - Stddev: 350.5
  - Non-zero count: 866,501.6745758057


- DLA_SC:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 52.8
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 1,054,241.2776031494


- DLA_SC_middle_plus:
  - Type: bool
  - Entity: person
  - Description: Receives at least DLA (self-care) middle rate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,054,241.2776031494


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 52.8
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 1,054,241.2776031494


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 8,694.2
  - Median: 7,778.7
  - Stddev: 2,320.1
  - Non-zero count: 28,911,965.103952408


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 1.6
  - Median: 1.0
  - Stddev: 1.1
  - Non-zero count: 28,911,965.103952408


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 1,898.8
  - Median: -52.0
  - Stddev: 2,912.0
  - Non-zero count: 9,514,608.44004631


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
  - Mean: 17.2
  - Median: 0.0
  - Stddev: 513.4
  - Non-zero count: 184,647.60177612305


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 17.2
  - Median: 0.0
  - Stddev: 513.4
  - Non-zero count: 184,647.60177612305


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
  - Mean: 26.6
  - Median: 0.0
  - Stddev: 366.3
  - Non-zero count: 513,856.8141784668


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 26.6
  - Median: 0.0
  - Stddev: 366.3
  - Non-zero count: 513,856.8141784668


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 513,856.8141784668


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 6.7
  - Median: 0.0
  - Stddev: 206.8
  - Non-zero count: 128,894.39431762695


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 6.7
  - Median: 0.0
  - Stddev: 206.8
  - Non-zero count: 128,894.39431762695


- SDA:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 1.4
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 22,961.987182617188


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 1.4
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 22,961.987182617188


- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 136.7
  - Median: 0.0
  - Stddev: 292.0
  - Non-zero count: 4,563,659.769268036


- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 63.3
  - Median: 0.0
  - Stddev: 217.0
  - Non-zero count: 4,778,407.078491211


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 73.1
  - Median: 0.0
  - Stddev: 261.1
  - Non-zero count: 4,083,687.2286987305


- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 93.5
  - Median: 0.0
  - Stddev: 548.8
  - Non-zero count: 1,898,113.700422287


- baseline_has_housing_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Housing Benefit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,825,368.330728531


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 442.7
  - Median: 0.0
  - Stddev: 1,088.5
  - Non-zero count: 2,825,368.330728531


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 1,071.8
  - Median: 0.0
  - Stddev: 2,759.7
  - Non-zero count: 3,102,018.3853855133


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 27,270.8
  - Median: 21,568.1
  - Stddev: 23,844.4
  - Non-zero count: 27,940,661.475087166


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,102,018.3853855133


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 292.6
  - Median: 0.0
  - Stddev: 1,103.3
  - Non-zero count: 4,005,052.6485595703


- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,911,965.103952408


- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 2.5
  - Median: 0.0
  - Stddev: 261.5
  - Non-zero count: 26,448.863525390625


- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 4.0
  - Median: 0.0
  - Stddev: 143.3
  - Non-zero count: 52,834.82293701172


- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 52.5
  - Non-zero count: 28,678.328735351562


- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 28.7
  - Median: 0.0
  - Stddev: 630.1
  - Non-zero count: 370,778.5451660156


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 155.6
  - Median: 0.0
  - Stddev: 1,334.3
  - Non-zero count: 1,054,817.5879516602


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 35.7
  - Median: 0.0
  - Stddev: 710.7
  - Non-zero count: 466,926.89154052734


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 4.0
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 49,525.937255859375


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 4.0
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 49,525.937255859375


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 12.3
  - Median: 0.0
  - Stddev: 240.3
  - Non-zero count: 81,561.10483837128


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 9.6
  - Median: 0.0
  - Stddev: 213.8
  - Non-zero count: 60,995.03647899628


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 10.0
  - Median: 0.0
  - Stddev: 224.0
  - Non-zero count: 61,994.21592235565


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 26,591.0
  - Median: 20,506.3
  - Stddev: 25,322.0
  - Non-zero count: 26,564,647.90506649


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 61,994.21592235565


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 10.2
  - Median: 0.0
  - Stddev: 243.0
  - Non-zero count: 173,689.5987548828


- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 147,721.1253118515


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 25,874.857788085938


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 25,874.857788085938


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 109.3
  - Median: 0.0
  - Stddev: 1,024.6
  - Non-zero count: 410,155.6478366852


- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 410,155.6478366852


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 55.1
  - Median: 0.0
  - Stddev: 739.9
  - Non-zero count: 493,232.3385620117


- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 228,979.21827983856


- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 410,155.6478366852


- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 77.8
  - Median: 0.0
  - Stddev: 111.1
  - Non-zero count: 9,618,035.123428345


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 34.2
  - Median: 0.0
  - Stddev: 74.7
  - Non-zero count: 11,839,624.808700562


- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 338.7
  - Median: 0.0
  - Stddev: 1,291.7
  - Non-zero count: 2,267,402.9735736847


- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,956,053.0205993652


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 14,866.2
  - Median: 0.0
  - Stddev: 25,921.2
  - Non-zero count: 31,964,718.531829834


- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 28.7
  - Median: 0.0
  - Stddev: 284.8
  - Non-zero count: 425,052.6935195923


- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1,425.1
  - Median: 0.0
  - Stddev: 2,429.8
  - Non-zero count: 8,195,191.299530983


- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 160.2
  - Median: 0.0
  - Stddev: 1,029.8
  - Non-zero count: 1,562,650.7014160156


- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 14,827,491.465907097


- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 344.4
  - Median: 0.0
  - Stddev: 1,329.8
  - Non-zero count: 2,267,402.9735736847


- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 19,994.0
  - Median: 14,931.7
  - Stddev: 24,905.2
  - Non-zero count: 18,258,056.937083244


- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1,323.4
  - Median: 0.0
  - Stddev: 2,752.5
  - Non-zero count: 6,530,781.848247528


- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 16,847.3
  - Median: 12,366.5
  - Stddev: 17,716.5
  - Non-zero count: 24,840,103.265452385


- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 677.6
  - Median: 0.0
  - Stddev: 1,273.1
  - Non-zero count: 14,373,663.184753418


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 44.9
  - Non-zero count: 50,662.7158203125


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 62.3
  - Median: 0.0
  - Stddev: 216.5
  - Non-zero count: 4,518,180.7966918945


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 2.3
  - Median: 0.0
  - Stddev: 103.2
  - Non-zero count: 31,814.554321289062


- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 9,319.3
  - Median: 7,159.0
  - Stddev: 4,882.7
  - Non-zero count: 28,911,965.103952408


- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8,609.1
  - Median: 7,756.2
  - Stddev: 1,884.9
  - Non-zero count: 28,911,965.103952408


- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 13,941.4
  - Median: 15,870.4
  - Stddev: 3,172.6
  - Non-zero count: 65,711,194.14491272


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,110,329.042739868


- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 80.7
  - Median: 0.0
  - Stddev: 477.4
  - Non-zero count: 2,068,074.2258930206


- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 6,037.5
  - Median: 7,159.0
  - Stddev: 1,189.6
  - Non-zero count: 28,911,965.103952408


- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 4,251.0
  - Median: 11.7
  - Stddev: 11,298.5
  - Non-zero count: 16,688,561.452951431


- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1,903.9
  - Median: 0.0
  - Stddev: 2,593.3
  - Non-zero count: 10,043,024.447314262


- baseline_has_universal_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Universal Credit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,582,372.8899273872


- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 20,984,509.948332787


- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 10,043,024.447314262


- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,714,765.36553955


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
  - Mean: 995.5
  - Median: 0.0
  - Stddev: 2,616.6
  - Non-zero count: 4,477,391.585942268


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,658,249.3999176025


- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 8,195,191.299530983


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 1,184.7
  - Median: 0.0
  - Stddev: 4,226.8
  - Non-zero count: 3,662,837.157816887


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 99.0
  - Median: 0.0
  - Stddev: 1,446.9
  - Non-zero count: 707,350.4859619141


- would_claim_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 23,849,804.518263817


- baseline_has_pension_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Pension Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,375,212.783203125


- guarantee_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 31,826.1
  - Median: 24,518.2
  - Stddev: 25,827.9
  - Non-zero count: 28,212,126.6044178


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 100.0
  - Median: 0.0
  - Stddev: 389.2
  - Non-zero count: 1,375,212.783203125


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 81.2
  - Median: 0.0
  - Stddev: 365.6
  - Non-zero count: 857,662.5760192871


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 792.4
  - Median: 0.0
  - Stddev: 1,990.2
  - Non-zero count: 2,281,603.9191627502


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 18.8
  - Median: 0.0
  - Stddev: 109.5
  - Non-zero count: 770,012.0218200684


- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,778,616.014831543


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 117.5
  - Median: 0.0
  - Stddev: 578.8
  - Non-zero count: 2,499,233.1461486816


- savings_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Savings Credit
  - Mean: 31,610.9
  - Median: 23,999.7
  - Stddev: 25,888.8
  - Non-zero count: 28,186,003.524827957


- would_claim_PC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,335,138.277267456


- baseline_has_income_support:
  - Type: bool
  - Entity: benunit
  - Description: Receives Income Support (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 187,855.24718475342


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 30.6
  - Median: 0.0
  - Stddev: 609.6
  - Non-zero count: 187,855.24718475342


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 39.7
  - Median: 0.0
  - Stddev: 798.9
  - Non-zero count: 194,128.29320526123


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 26,591.0
  - Median: 20,506.3
  - Stddev: 25,322.0
  - Non-zero count: 26,564,647.90506649


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 194,128.29320526123


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 16.3
  - Median: 0.0
  - Stddev: 382.1
  - Non-zero count: 292,528.08474731445


- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,911,965.103952408


- AA:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 56.1
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 941,657.3074951172


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 56.1
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 941,657.3074951172


- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 108.3
  - Median: 13.5
  - Stddev: 290.0
  - Non-zero count: 19,754,560.831863403


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 108.3
  - Median: 13.5
  - Stddev: 290.0
  - Non-zero count: 19,754,560.831863403


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
  - Mean: 221.6
  - Median: 18.6
  - Stddev: 791.0
  - Non-zero count: 20,117,734.807052612


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 24,912,723.681655884


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
  - Mean: 48.5
  - Median: 0.0
  - Stddev: 1,251.2
  - Non-zero count: 130,279.23223876953


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
  - Mean: 2,253.7
  - Median: 0.0
  - Stddev: 13,658.0
  - Non-zero count: 3,472,284.089782715


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 2,302.2
  - Median: 0.0
  - Stddev: 13,803.2
  - Non-zero count: 3,523,950.799102783


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 2,098.7
  - Median: 0.0
  - Stddev: 12,676.5
  - Non-zero count: 3,105,894.013671875


- baseline_has_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Benefit (baseline)
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,911,965.103952408


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 360.7
  - Median: 0.0
  - Stddev: 701.3
  - Non-zero count: 6,551,450.8882808685


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 323.2
  - Median: 0.0
  - Stddev: 681.7
  - Non-zero count: 6,038,458.9831905365


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 172.2
  - Median: 0.0
  - Stddev: 537.8
  - Non-zero count: 7,158,474.705871582


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 198.5
  - Median: 0.0
  - Stddev: 388.0
  - Non-zero count: 13,997,365.380493164


- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 6,737,631.404943466


- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 1,097.6
  - Median: 137.1
  - Stddev: 2,939.6
  - Non-zero count: 19,754,560.831863403


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,097.6
  - Median: 137.1
  - Stddev: 2,939.6
  - Non-zero count: 19,754,560.831863403


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
  - Mean: 7,558.9
  - Median: 2,622.9
  - Stddev: 14,004.0
  - Non-zero count: 20,503,912.60080242


- household_tax:
  - Type: float
  - Entity: household
  - Description: Taxes
  - Mean: 11,203.6
  - Median: 6,025.5
  - Stddev: 16,701.2
  - Non-zero count: 28,668,210.452468872


- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,699.3
  - Median: 0.0
  - Stddev: 9,388.3
  - Non-zero count: 32,707,441.207763672


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,699.3
  - Median: 0.0
  - Stddev: 9,388.3
  - Non-zero count: 32,707,441.207763672


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
  - Mean: 6.9
  - Median: 0.0
  - Stddev: 33.8
  - Non-zero count: 2,844,367.298522949


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 6.9
  - Median: 0.0
  - Stddev: 33.8
  - Non-zero count: 2,844,367.298522949


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 24,322,613.03288269


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 902.7
  - Median: 0.0
  - Stddev: 1,563.6
  - Non-zero count: 24,426,694.505371094


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,313.3
  - Median: 0.0
  - Stddev: 2,917.4
  - Non-zero count: 25,013,201.098114014


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,313.3
  - Median: 0.0
  - Stddev: 2,917.4
  - Non-zero count: 25,013,201.098114014


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,272.1
  - Median: 0.0
  - Stddev: 4,365.8
  - Non-zero count: 27,637,681.229278564


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 59.5
  - Median: 0.0
  - Stddev: 487.7
  - Non-zero count: 2,453,660.691101074


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 902.7
  - Median: 0.0
  - Stddev: 1,563.6
  - Non-zero count: 24,426,694.505371094


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 958.9
  - Median: 0.0
  - Stddev: 1,602.0
  - Non-zero count: 26,790,469.823547363


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 66.3
  - Median: 0.0
  - Stddev: 510.7
  - Non-zero count: 2,844,367.298522949


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 615.9
  - Median: 0.0
  - Stddev: 8,396.0
  - Non-zero count: 444,526.3962402344


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 277.2
  - Median: 0.0
  - Stddev: 3,775.5
  - Non-zero count: 444,526.3962402344


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 21.4
  - Non-zero count: 3,928.903564453125


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7,052.5
  - Median: 0.0
  - Stddev: 11,526.0
  - Non-zero count: 29,230,887.313293457


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,410.5
  - Median: 0.0
  - Stddev: 2,305.9
  - Non-zero count: 29,230,887.313293457


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 7.2
  - Median: 0.0
  - Stddev: 404.9
  - Non-zero count: 72,558.6669921875


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 12.6
  - Median: 0.0
  - Stddev: 419.5
  - Non-zero count: 499,596.4690551758


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 180.0
  - Median: 0.0
  - Stddev: 463.2
  - Non-zero count: 2,369,618.8528442383


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,541.9
  - Median: 0.0
  - Stddev: 8,148.3
  - Non-zero count: 29,230,887.313293457


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 9,787.2
  - Median: 0.0
  - Stddev: 23,434.8
  - Non-zero count: 29,230,887.313293457


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 2,118.8
  - Median: 0.0
  - Stddev: 11,068.1
  - Non-zero count: 3,774,146.2572631836


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 847.5
  - Median: 0.0
  - Stddev: 4,426.2
  - Non-zero count: 3,774,146.2572631836


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 210.4
  - Non-zero count: 4,768.873046875


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2,740.5
  - Median: 0.0
  - Stddev: 8,256.9
  - Non-zero count: 30,142,934.106140137


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,723.5
  - Median: 0.0
  - Stddev: 8,229.7
  - Non-zero count: 30,142,934.106140137


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 34,964,548.49809265


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,342,256.117919922


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 1.6
  - Median: 0.0
  - Stddev: 129.7
  - Non-zero count: 78,597.95288085938


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,990.8
  - Median: 5,000.0
  - Stddev: 191.2
  - Non-zero count: 65,670,184.60084534


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 847.8
  - Median: 0.0
  - Stddev: 1,814.4
  - Non-zero count: 2,369,618.8528442383


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 10,642.5
  - Median: 0.0
  - Stddev: 23,679.2
  - Non-zero count: 30,142,934.106140137


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 7.5
  - Median: 0.0
  - Stddev: 497.4
  - Non-zero count: 78,597.95288085938


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
  - Mean: 20.0
  - Median: 0.0
  - Stddev: 378.5
  - Non-zero count: 176,821.06112670898


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 6.8
  - Median: 0.0
  - Stddev: 170.3
  - Non-zero count: 119,723.27923583984


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,025.5
  - Median: 10,682.4
  - Stddev: 25,692.2
  - Non-zero count: 47,208,113.33821106


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
  - Mean: 26.8
  - Median: 0.0
  - Stddev: 417.2
  - Non-zero count: 295,496.8730773926


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
  - Mean: 461.1
  - Median: 0.0
  - Stddev: 1,319.8
  - Non-zero count: 19,481,368.55682373


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,731.6
  - Median: 0.0
  - Stddev: 2,065.8
  - Non-zero count: 31,217,685.64199829


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 28.9
  - Median: 0.0
  - Stddev: 380.0
  - Non-zero count: 8,746,712.427490234


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 931.7
  - Median: 0.0
  - Stddev: 1,944.9
  - Non-zero count: 4,892,996.383728027


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 12,685.4
  - Median: 0.0
  - Stddev: 22,898.1
  - Non-zero count: 32,657,585.70352173


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 60.9
  - Median: 0.0
  - Stddev: 828.2
  - Non-zero count: 872,490.9592895508


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 944.4
  - Median: 0.0
  - Stddev: 6,889.5
  - Non-zero count: 7,776,879.277694702


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 424.7
  - Median: 0.0
  - Stddev: 2,039.8
  - Non-zero count: 2,272,576.3924865723


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 48.3
  - Median: 0.0
  - Stddev: 590.1
  - Non-zero count: 21,673,531.91357422


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1,393.5
  - Median: 0.0
  - Stddev: 11,744.1
  - Non-zero count: 3,788,382.600982666


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,536.4
  - Median: 0.0
  - Stddev: 3,555.8
  - Non-zero count: 12,423,800.287582397


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,443.4
  - Median: 10,698.3
  - Stddev: 26,420.0
  - Non-zero count: 45,109,936.690719604


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
  - Mean: 931.7
  - Median: 0.0
  - Stddev: 1,944.9
  - Non-zero count: 4,892,996.383728027


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 13,106.4
  - Median: 0.0
  - Stddev: 23,698.4
  - Non-zero count: 27,630,920.47998047


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 944.4
  - Median: 0.0
  - Stddev: 6,889.5
  - Non-zero count: 7,776,879.277694702


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 356.9
  - Median: -108.1
  - Stddev: 2,138.6
  - Non-zero count: 2,696,198.9169006348


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 77.2
  - Median: 0.0
  - Stddev: 758.1
  - Non-zero count: 21,673,531.91357422


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 1,429.4
  - Median: 0.0
  - Stddev: 11,885.6
  - Non-zero count: 3,956,053.0205993652


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,536.4
  - Median: 0.0
  - Stddev: 3,555.8
  - Non-zero count: 12,423,800.287582397


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 152.6
  - Median: 0.0
  - Stddev: 422.9
  - Non-zero count: 8,356,366.312438965


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 61,300,958.98890686


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: -101.9
  - Median: 0.0
  - Stddev: 5,831.3
  - Non-zero count: 13,143,191.803192139


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5,064.0
  - Median: 1,817.6
  - Stddev: 5,641.9
  - Non-zero count: 35,367,320.4433136


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,332.1
  - Median: 12,500.0
  - Stddev: 1,156.3
  - Non-zero count: 65,021,615.58522034


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
  - Non-zero count: 65,711,194.14491272


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
  - Mean: 39,912.2
  - Median: 40,000.0
  - Stddev: 1,290.1
  - Non-zero count: 65,711,194.14491272


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,332.1
  - Median: 12,500.0
  - Stddev: 1,156.3
  - Non-zero count: 65,021,615.58522034


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 65,711,194.14491272


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: -67.9
  - Median: -108.1
  - Stddev: 180.0
  - Non-zero count: 2,696,198.9169006348


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 963.0
  - Median: 1,000.0
  - Stddev: 136.4
  - Non-zero count: 65,255,126.31361389


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 65,711,194.14491272


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 35.9
  - Median: 0.0
  - Stddev: 615.9
  - Non-zero count: 3,956,053.0205993652


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 17.0
  - Median: 0.0
  - Stddev: 125.4
  - Non-zero count: 903,990.2489013672


- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 30.3
  - Median: 0.0
  - Stddev: 460.9
  - Non-zero count: 680,928.8559875488


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 561.1
  - Median: 0.0
  - Stddev: 8,539.0
  - Non-zero count: 680,928.8559875488


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,589,934.305847168


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
  - Mean: 45.0
  - Median: 0.0
  - Stddev: 1,215.4
  - Non-zero count: 130,279.23223876953


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
  - Mean: 6,411.7
  - Median: 0.0
  - Stddev: 21,318.9
  - Non-zero count: 8,142,352.621520996


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 6,456.8
  - Median: 0.0
  - Stddev: 21,473.6
  - Non-zero count: 8,160,351.338562012


- expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (expected)
  - Mean: 6.4
  - Median: 0.0
  - Stddev: 186.4
  - Non-zero count: 305,387.84814453125


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 118.6
  - Median: 0.0
  - Stddev: 3,453.7
  - Non-zero count: 305,387.84814453125


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,409,307.1204223633


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
  - Mean: 1.6
  - Median: 0.0
  - Stddev: 124.4
  - Non-zero count: 5,667.17626953125


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
  - Mean: 5,073.2
  - Median: 0.0
  - Stddev: 18,137.6
  - Non-zero count: 8,142,352.621520996


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 5,074.8
  - Median: 0.0
  - Stddev: 18,137.9
  - Non-zero count: 8,146,348.040710449


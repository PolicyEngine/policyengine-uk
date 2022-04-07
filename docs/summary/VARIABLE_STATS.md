# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2020) 2019-20 Family Resources Survey, with simulation turned on.


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3,434.3
  - Median: 0.0
  - Stddev: 5,207.5
  - Non-zero count: 26,102,296.57203296


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 557.9
  - Median: 0.0
  - Stddev: 3,350.800048828125
  - Non-zero count: 13,834,298.32628858


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 441.5
  - Median: 0.0
  - Stddev: 1,680.5
  - Non-zero count: 2,816,139.986817181


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2,876.5
  - Median: 0.0
  - Stddev: 5,231.7998046875
  - Non-zero count: 22,615,303.661769897


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 32.5
  - Median: 35.0
  - Stddev: 31.399999618530273
  - Non-zero count: 17,650,955.508020252


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
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 4,462,032.563521385


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1,235.7
  - Median: 0.0
  - Stddev: 2,656.89990234375
  - Non-zero count: 14,805,501.560266048


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 982.5
  - Median: 0.0
  - Stddev: 3,104.699951171875
  - Non-zero count: 11,473,490.068819553


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 8,206.2
  - Median: 6,448.5
  - Stddev: 8,236.7998046875
  - Non-zero count: 20,008,046.027900666


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,180,480.351083279


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,726,878.757801533


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 15,771,229.128755808


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,893,758.86311841


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 12,626,632.112122


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 11,153,412.077039897


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -557.9
  - Median: 0.0
  - Stddev: 3,350.800048828125
  - Non-zero count: 7,079,685.93421343


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,198.6
  - Median: 0.0
  - Stddev: 4,317.10009765625
  - Non-zero count: 17,055,616.66657594


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1,893.9
  - Median: 0.0
  - Stddev: 4,034.10009765625
  - Non-zero count: 15,101,576.829185039


- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
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
  - Stddev: 0.1
  - Non-zero count: 1,273,112.8127450943


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 672,449.0207452774


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 4,125,252.500572443


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,714,607.8954343796


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 774.9
  - Median: 0.0
  - Stddev: 1,741.5
  - Non-zero count: 4,125,252.500572443


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 552.3
  - Median: 0.0
  - Stddev: 1,430.0
  - Non-zero count: 3,714,607.8954343796


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 14,696.5
  - Median: 13,786.6
  - Stddev: 5,682.0
  - Non-zero count: 28,397,861.239144295


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 17,204.2
  - Median: 16,090.7
  - Stddev: 5,517.2001953125
  - Non-zero count: 28,397,861.239144295


- poverty_threshold_bhc:
  - Type: float
  - Entity: household
  - Description: Poverty threshold (BHC)
  - Mean: 16,090.7
  - Median: 16,090.7
  - Stddev: 0.0
  - Non-zero count: 28,397,861.239144295


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
  - Mean: 1,034.1
  - Median: 0.0
  - Stddev: 25,273.30078125
  - Non-zero count: 22,945,289.76787603


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 16,334.0
  - Median: 7,240.3
  - Stddev: 28,490.30078125
  - Non-zero count: 40,145,173.373889714


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 36,243.4
  - Median: 29,707.5
  - Stddev: 35,204.0
  - Non-zero count: 28,333,661.788921326


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 34,260.1
  - Median: 28,066.7
  - Stddev: 37,095.80078125
  - Non-zero count: 28,107,144.182849854


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 36,243.4
  - Median: 29,707.5
  - Stddev: 35,204.0
  - Non-zero count: 28,333,661.788921326


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 21,226.0
  - Median: 15,049.4
  - Stddev: 39,389.80078125
  - Non-zero count: 51,287,033.864952475


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 39,480.5
  - Median: 30,916.8
  - Stddev: 41,417.3984375
  - Non-zero count: 28,333,661.788921326


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 36,815.7
  - Median: 28,248.8
  - Stddev: 41,612.19921875
  - Non-zero count: 28,107,144.182849854


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 872.9
  - Median: 0.0
  - Stddev: 1,034.5
  - Non-zero count: 31,879,392.475227475


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 50,348.4
  - Median: 35,992.4
  - Stddev: 63,028.6015625
  - Non-zero count: 28,366,532.112438172


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 42,142.3
  - Median: 28,289.0
  - Stddev: 64,438.0
  - Non-zero count: 25,114,470.42472765


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 39,480.5
  - Median: 30,916.8
  - Stddev: 41,417.3984375
  - Non-zero count: 28,333,661.788921326


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 33,312,417.816262633


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
  - Mean: 75.6
  - Median: -1.0
  - Stddev: 1,944.800048828125
  - Non-zero count: 242,468.1622543335


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 35.7
  - Median: 0.0
  - Stddev: 515.7000122070312
  - Non-zero count: 746,752.8058598042


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 17,791.6
  - Median: 8,076.6
  - Stddev: 39,495.6015625
  - Non-zero count: 44,749,600.26081374


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.7
  - Median: 8.7
  - Stddev: 1.7000000476837158
  - Non-zero count: 67,264,792.51037088


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 43.1
  - Median: 0.0
  - Stddev: 828.5
  - Non-zero count: 776,042.7286429405


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 17,246.3
  - Median: 14,543.0
  - Stddev: 25,595.099609375
  - Non-zero count: 51,287,033.864952475


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: 104.9
  - Median: 0.0
  - Stddev: 1,219.300048828125
  - Non-zero count: 1,108,639.6627731323


- real_household_net_income:
  - Type: float
  - Entity: household
  - Description: Real household net income
  - Mean: 35,832.2
  - Median: 28,059.9
  - Stddev: 37,590.1015625
  - Non-zero count: 28,333,661.788921326


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
  - Mean: 16.8
  - Median: 0.0
  - Stddev: 19.899999618530273
  - Non-zero count: 31,879,392.475227475


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
  - Mean: 266,942.6
  - Median: 80,000.0
  - Stddev: 1,338,179.375
  - Non-zero count: 22,477,960.783508748


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 22,477,960.783508748


- total_wealth:
  - Type: float
  - Entity: household
  - Description: Total wealth
  - Mean: 534,230.5
  - Median: 305,724.4
  - Stddev: 1,509,346.875
  - Non-zero count: 24,823,635.43744251


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 203,553.2
  - Median: 139,000.0
  - Stddev: 320,399.0
  - Non-zero count: 17,893,101.434858263


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 9,022.6
  - Median: 0.0
  - Stddev: 107,346.703125
  - Non-zero count: 1,029,535.9482631683


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 28,768.5
  - Median: 0.0
  - Stddev: 164,971.203125
  - Non-zero count: 3,343,844.0210351944


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 267,288.0
  - Median: 165,000.0
  - Stddev: 469,988.90625
  - Non-zero count: 19,126,878.09858316


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 232,321.7
  - Median: 150,000.0
  - Stddev: 393,889.1875
  - Non-zero count: 18,510,922.947545946


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 61,899.7
  - Median: 18,550.7
  - Stddev: 310,302.1875
  - Non-zero count: 22,477,960.783508748


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 162,083.8
  - Median: 94,154.3
  - Stddev: 342,709.0
  - Non-zero count: 19,331,470.053551614


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 223,983.5
  - Median: 130,640.0
  - Stddev: 500,838.90625
  - Non-zero count: 24,871,013.163288802


- owned_land:
  - Type: float
  - Entity: household
  - Description: Owned land
  - Mean: 10,342.2
  - Median: 0.0
  - Stddev: 146,552.59375
  - Non-zero count: 1,468,068.7545609474


- carbon_consumption:
  - Type: float
  - Entity: household
  - Description: Carbon consumption
  - Mean: 19.2
  - Median: 14.3
  - Stddev: 19.899999618530273
  - Non-zero count: 28,388,804.893868417


- alcohol_and_tobacco_consumption:
  - Type: float
  - Entity: household
  - Description: Alcohol and tobacco
  - Mean: 764.1
  - Median: 227.5
  - Stddev: 1,407.5
  - Non-zero count: 17,520,739.283840626


- clothing_and_footwear_consumption:
  - Type: float
  - Entity: household
  - Description: Clothing and footwear
  - Mean: 1,467.8
  - Median: 487.6
  - Stddev: 3,286.0
  - Non-zero count: 19,007,326.063055634


- communication_consumption:
  - Type: float
  - Entity: household
  - Description: Communication
  - Mean: 763.0
  - Median: 408.2
  - Stddev: 2,094.5
  - Non-zero count: 23,328,315.47642654


- diesel_spending:
  - Type: float
  - Entity: household
  - Description: Diesel spending
  - Mean: 603.1
  - Median: 0.0
  - Stddev: 1,236.5
  - Non-zero count: 8,920,278.795108736


- education_consumption:
  - Type: float
  - Entity: household
  - Description: Education
  - Mean: 566.3
  - Median: 0.0
  - Stddev: 5,245.7001953125
  - Non-zero count: 2,770,251.853920698


- food_and_non_alcoholic_beverages_consumption:
  - Type: float
  - Entity: household
  - Description: Food and alcoholic beverages
  - Mean: 3,449.3
  - Median: 2,946.9
  - Stddev: 2,363.699951171875
  - Non-zero count: 28,191,694.207987756


- health_consumption:
  - Type: float
  - Entity: household
  - Description: Health
  - Mean: 530.3
  - Median: 49.9
  - Stddev: 2,216.60009765625
  - Non-zero count: 17,275,971.053601086


- household_furnishings_consumption:
  - Type: float
  - Entity: household
  - Description: Household furnishings
  - Mean: 2,561.5
  - Median: 753.7
  - Stddev: 6,007.10009765625
  - Non-zero count: 27,072,779.806850404


- housing_water_and_electricity_consumption:
  - Type: float
  - Entity: household
  - Description: Housing, water and electricity
  - Mean: 4,914.5
  - Median: 2,556.0
  - Stddev: 7,340.39990234375
  - Non-zero count: 28,336,069.32198426


- miscellaneous_consumption:
  - Type: float
  - Entity: household
  - Description: Miscellaneous
  - Mean: 3,447.7
  - Median: 1,698.3
  - Stddev: 6,712.89990234375
  - Non-zero count: 27,978,087.467287034


- petrol_spending:
  - Type: float
  - Entity: household
  - Description: Petrol spending
  - Mean: 829.7
  - Median: 0.0
  - Stddev: 1,238.9000244140625
  - Non-zero count: 14,094,198.226631463


- recreation_consumption:
  - Type: float
  - Entity: household
  - Description: Recreation
  - Mean: 5,247.9
  - Median: 2,128.6
  - Stddev: 9,953.599609375
  - Non-zero count: 28,173,828.129013985


- restaurants_and_hotels_consumption:
  - Type: float
  - Entity: household
  - Description: Restaurants and hotels
  - Mean: 3,512.4
  - Median: 1,972.7
  - Stddev: 5,023.2998046875
  - Non-zero count: 25,306,853.751206845


- transport_consumption:
  - Type: float
  - Entity: household
  - Description: Transport
  - Mean: 5,970.6
  - Median: 3,081.3
  - Stddev: 10,692.900390625
  - Non-zero count: 25,547,521.62643358


- additional_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (additional)
  - Mean: 28,768.5
  - Median: 0.0
  - Stddev: 164,971.203125
  - Non-zero count: 3,343,844.0210351944


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
  - Mean: 203,553.2
  - Median: 139,000.0
  - Stddev: 320,399.0
  - Non-zero count: 17,893,101.434858263


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,534,812.5801950395


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 9,022.6
  - Median: 0.0
  - Stddev: 107,346.703125
  - Non-zero count: 1,029,535.9482631683


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
  - Non-zero count: 28,397,861.239144295


- property_sale_rate:
  - Type: float
  - Entity: state
  - Description: Residential property sale rate
  - Mean: 0.1
  - Median: 0.1
  - Stddev: nan
  - Non-zero count: 1.0


- rent:
  - Type: float
  - Entity: household
  - Description: Rent
  - Mean: 2,664.8
  - Median: -52.0
  - Stddev: 4,220.89990234375
  - Non-zero count: 10,216,378.29003644


- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2,301.4
  - Median: -52.0
  - Stddev: 3,968.800048828125
  - Non-zero count: 9,253,730.809152842


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 104.4
  - Median: 0.0
  - Stddev: 882.0999755859375
  - Non-zero count: 2,425,796.8594563007


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,441.4
  - Median: 1,406.8
  - Stddev: 751.4000244140625
  - Non-zero count: 27,305,731.43427512


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,308.1
  - Median: 1,367.4
  - Stddev: 859.0
  - Non-zero count: 25,518,166.014158934


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
  - Mean: 2,301.4
  - Median: -52.0
  - Stddev: 3,968.800048828125
  - Non-zero count: 9,253,730.809152842


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 2,664.8
  - Median: -52.0
  - Stddev: 4,220.89990234375
  - Non-zero count: 10,216,378.29003644


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 64.3
  - Median: 0.0
  - Stddev: 339.29998779296875
  - Non-zero count: 2,499,741.7501295805


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 37.4
  - Median: 0.0
  - Stddev: 621.7999877929688
  - Non-zero count: 700,398.3895874023


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
  - Mean: 2,204.1
  - Median: 0.0
  - Stddev: 5,618.7001953125
  - Non-zero count: 8,078,999.959984779


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 848.6
  - Median: -52.0
  - Stddev: 2,093.800048828125
  - Non-zero count: 8,054,139.729485512


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 440.1
  - Median: 0.0
  - Stddev: 1,295.9000244140625
  - Non-zero count: 17,835,212.906062603


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,125.0
  - Median: 0.0
  - Stddev: 3,035.300048828125
  - Non-zero count: 10,216,378.29003644


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 28.4
  - Median: 0.0
  - Stddev: 172.60000610351562
  - Non-zero count: 2,079,886.1911296844


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 376.4
  - Median: 358.8
  - Stddev: 252.8000030517578
  - Non-zero count: 27,066,932.850072354


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 17.0
  - Non-zero count: 2,425,796.8594563007


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
  - Mean: 39.1
  - Median: 39.0
  - Stddev: 23.6
  - Non-zero count: 66,552,191.223160416


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 40,508,916.38011539


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,895,993.80668667


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 14,859,882.323568821


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1,981.9
  - Median: 1,982.0
  - Stddev: 23.6
  - Non-zero count: 67,264,792.51037088


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 78.3
  - Median: 100.0
  - Stddev: 41.2
  - Non-zero count: 67,264,792.51037088


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
  - Non-zero count: 10,650,856.014761686


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 41,367,538.42520833


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 52,404,910.18680206


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 7,892,695.010504961


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 35,868,496.54262373


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 14,859,882.323568821


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,425,145.948216677


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 33,977,697.44652149


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 28,397,861.239144295


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 33,287,095.06384939


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,367,430.1794216633


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,492,452.144147158


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
  - Non-zero count: 54,250,298.13455787


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,264,792.51037088


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 96,218,368.2
  - Median: 96,301,200.6
  - Stddev: 55,430,399.4
  - Non-zero count: 67,264,792.51037088


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight (region-adjusted)
  - Mean: 2,048.9
  - Median: 1,794.7
  - Stddev: 803.0
  - Non-zero count: 67,264,792.51037088


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 1,902.9
  - Median: 1,666.0
  - Stddev: 784.0
  - Non-zero count: 63,515,817.15948486


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 96,218,163.2
  - Median: 96,301,000.0
  - Stddev: 55,430,400.0
  - Non-zero count: 67,264,792.51037088


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 96,216,994.2
  - Median: 96,300,004.8
  - Stddev: 55,430,400.0
  - Non-zero count: 67,264,792.51037088


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
  - Mean: 1.1
  - Median: 1.0
  - Stddev: 0.4000000059604645
  - Non-zero count: 28,397,861.239144295


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.1
  - Median: 1.0
  - Stddev: 0.30000001192092896
  - Non-zero count: 28,397,861.239144295


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 95,969,863.2
  - Median: 95,870,000.2
  - Stddev: 55,454,854.1
  - Non-zero count: 28,397,861.239144295


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.3
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 28,397,861.239144295


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.4
  - Median: 2.0
  - Stddev: 1.3
  - Non-zero count: 28,397,861.239144295


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 1,955.9
  - Median: 1,707.7
  - Stddev: 765.7000122070312
  - Non-zero count: 28,397,861.239144295


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.239144295


- is_renting:
  - Type: bool
  - Entity: household
  - Description: Is renting
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,436,957.180482179


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
  - Mean: 2.8
  - Median: 3.0
  - Stddev: 1.0
  - Non-zero count: 28,397,861.239144295


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
  - Mean: 95,970,970.5
  - Median: 95,871,000.2
  - Stddev: 55,356,955.9
  - Non-zero count: 28,397,861.240877807


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
  - Mean: 1,716.2
  - Median: 1,530.2
  - Stddev: 662.0999755859375
  - Non-zero count: 28,397,861.240877807


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 50.9
  - Median: 51.0
  - Stddev: 18.700000762939453
  - Non-zero count: 28,397,861.240877807


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7,199,203.3221821785


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.240877807


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
  - Mean: 1.6
  - Median: 2.0
  - Stddev: 0.5
  - Non-zero count: 28,217,323.306823432


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.9
  - Non-zero count: 7,547,397.831964016


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 48.9
  - Median: 49.0
  - Stddev: 18.600000381469727
  - Non-zero count: 28,397,861.240877807


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: inf
  - Stddev: nan
  - Non-zero count: 27,716,369.60984105


- state_id:
  - Type: int
  - Entity: state
  - Description: State ID
  - Mean: 1.0
  - Median: 1.0
  - Stddev: nan
  - Non-zero count: 1.0


- state_weight:
  - Type: float
  - Entity: state
  - Description: State weight
  - Mean: 1.0
  - Median: 1.0
  - Stddev: nan
  - Non-zero count: 1.0


- benunit_has_carer:
  - Type: bool
  - Entity: benunit
  - Description: Benefit unit has a carer
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 527,441.4348181486


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 36.2
  - Median: 0.0
  - Stddev: 284.0
  - Non-zero count: 527,441.4348181486


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 657,481.827270627


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 527,441.4348181486


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 196.3
  - Median: 0.0
  - Stddev: 637.5
  - Non-zero count: 2,550,998.1684330106


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 13.7
  - Median: 0.0
  - Stddev: 130.6999969482422
  - Non-zero count: 363,597.0181427002


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,149,542.6521868706


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 407,086.0536804199


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,301,191.5867350101


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,550,998.1684330106


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 14,270.757537841797


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 363,597.0181427002


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
  - Non-zero count: 1,069,104.8617416024


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 5,926.1011962890625


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 195.4
  - Median: 0.0
  - Stddev: 1,041.199951171875
  - Non-zero count: 1,069,104.8617416024


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
  - Mean: 1,407.6
  - Median: 0.0
  - Stddev: 2,447.699951171875
  - Non-zero count: 7,198,026.271358013


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.9
  - Median: 0.0
  - Stddev: 45.29999923706055
  - Non-zero count: 7,899.462677001953


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 33.8
  - Median: 0.0
  - Stddev: 92.4000015258789
  - Non-zero count: 1,759,607.146289587


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 1,442.5
  - Median: 0.0
  - Stddev: 2,483.0
  - Non-zero count: 7,198,026.271358013


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 11.300000190734863
  - Non-zero count: 2,970.5634155273438


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 112.9
  - Median: 0.0
  - Stddev: 361.20001220703125
  - Non-zero count: 1,054,266.432361126


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 18.8
  - Median: 0.0
  - Stddev: 200.5
  - Non-zero count: 213,812.44254922867


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 33.9
  - Median: 0.0
  - Stddev: 155.39999389648438
  - Non-zero count: 470,063.6859064102


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 7.7
  - Median: 0.0
  - Stddev: 97.80000305175781
  - Non-zero count: 68,326.06192779541


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 36.5
  - Median: 0.0
  - Stddev: 177.0
  - Non-zero count: 506,962.6308693886


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 229.5
  - Median: 0.0
  - Stddev: 769.5999755859375
  - Non-zero count: 1,054,266.432361126


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 2.1
  - Median: 0.0
  - Stddev: 38.0
  - Non-zero count: 42,548.05642700195


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 17.5
  - Median: 0.0
  - Stddev: 73.5
  - Non-zero count: 603,922.9836435318


- baseline_child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Baseline Child Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_has_child_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Tax Credit (baseline)
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.240877807


- baseline_has_working_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Working Tax Credit (baseline)
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.240877807


- baseline_working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Baseline Working Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit
  - Mean: 323.2
  - Median: 0.0
  - Stddev: 753.7000122070312
  - Non-zero count: 1,557,225.338057518


- child_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit pre-minimum
  - Mean: 550.8
  - Median: 0.0
  - Stddev: 1,237.199951171875
  - Non-zero count: 2,903,263.7125594616


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 162.4
  - Median: 0.0
  - Stddev: 829.0
  - Non-zero count: 1,988,947.4519594908


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit child limit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 63,192,648.06704584


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,759,607.146289587


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,054,266.432361126


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,726,878.757801533


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 661.6
  - Median: 0.0
  - Stddev: 1,374.800048828125
  - Non-zero count: 3,049,925.46484828


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 39,688.2
  - Median: 26,397.5
  - Stddev: 58,341.19921875
  - Non-zero count: 25,527,052.704087764


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 13,184.3
  - Median: 7,548.2
  - Stddev: 23,383.400390625
  - Non-zero count: 23,823,019.826592


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 110.9
  - Median: 0.0
  - Stddev: 339.8999938964844
  - Non-zero count: 883,315.7986822128


- working_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit pre-minimum
  - Mean: 110.9
  - Median: 0.0
  - Stddev: 339.8999938964844
  - Non-zero count: 883,315.7986822128


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 46.3
  - Median: 0.0
  - Stddev: 312.0
  - Non-zero count: 1,299,398.772114277


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,859,829.9030225277


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,184,146.129310131


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 10.9
  - Median: 0.0
  - Stddev: 383.8999938964844
  - Non-zero count: 153,549.71931791306


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 10.9
  - Median: 0.0
  - Stddev: 383.8999938964844
  - Non-zero count: 153,549.71931791306


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 11,387.04753112793


- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 11,387.04753112793


- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 9.1
  - Median: 0.0
  - Stddev: 496.29998779296875
  - Non-zero count: 24,900.334619522095


- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 9.1
  - Median: 0.0
  - Stddev: 496.29998779296875
  - Non-zero count: 24,900.334619522095


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: nan
  - Median: 13,399.9
  - Stddev: nan
  - Non-zero count: 28,397,861.240877807


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,836,555.840707898


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,037,371.76159373


- state_pension:
  - Type: float
  - Entity: person
  - Description: State Pension
  - Mean: 1,523.0
  - Median: 0.0
  - Stddev: 3,532.800048828125
  - Non-zero count: 12,096,936.418187052


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 67,264,792.51037088


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,523.0
  - Median: 0.0
  - Stddev: 3,532.800048828125
  - Non-zero count: 12,096,936.418187052


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,264,792.51037088


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 45.5
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 777,882.9158256352


- aa_category:
  - Type: Categorical
  - Entity: person
  - Description: Attendance Allowance category


- attendance_allowance:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 46.3
  - Median: 0.0
  - Stddev: 494.29998779296875
  - Non-zero count: 777,882.9158256352


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 8,798.0
  - Median: 7,778.7
  - Stddev: 2,320.5
  - Non-zero count: 28,397,861.240877807


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 1.6
  - Median: 1.0
  - Stddev: 1.100000023841858
  - Non-zero count: 28,397,861.240877807


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 1,913.3
  - Median: -52.0
  - Stddev: 2,911.89990234375
  - Non-zero count: 9,253,730.809152842


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
  - Mean: 31.4
  - Median: 0.0
  - Stddev: 513.2999877929688
  - Non-zero count: 336,487.64014816284


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 31.4
  - Median: 0.0
  - Stddev: 513.2999877929688
  - Non-zero count: 336,487.64014816284


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
  - Mean: 34.2
  - Median: 0.0
  - Stddev: 373.20001220703125
  - Non-zero count: 657,481.827270627


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 33.5
  - Median: 0.0
  - Stddev: 366.1000061035156
  - Non-zero count: 657,481.827270627


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 657,481.827270627


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 7.5
  - Median: 0.0
  - Stddev: 206.8000030517578
  - Non-zero count: 153,170.4757398367


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 7.5
  - Median: 0.0
  - Stddev: 206.8000030517578
  - Non-zero count: 153,170.4757398367


- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 123.4
  - Median: 0.0
  - Stddev: 292.0
  - Non-zero count: 4,198,763.867655069


- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 56.3
  - Median: 0.0
  - Stddev: 217.10000610351562
  - Non-zero count: 4,491,651.035011321


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 86.3
  - Median: 0.0
  - Stddev: 279.1000061035156
  - Non-zero count: 5,857,850.438636571


- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 123.6
  - Median: 0.0
  - Stddev: 601.9000244140625
  - Non-zero count: 2,720,212.195229292


- baseline_has_housing_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Housing Benefit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 2,737,012.8899612427


- baseline_housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit (baseline)
  - Mean: 394.8
  - Median: 0.0
  - Stddev: 576.0999755859375
  - Non-zero count: 2,737,012.8899612427


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 394.5
  - Median: 0.0
  - Stddev: 575.7000122070312
  - Non-zero count: 2,737,012.8899612427


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 944.7
  - Median: 0.0
  - Stddev: 1,899.800048828125
  - Non-zero count: 3,023,521.7643461227


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 29,473.7
  - Median: 23,201.3
  - Stddev: 27,813.80078125
  - Non-zero count: 27,301,702.82139772


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,023,521.7643461227


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 275.2
  - Median: 0.0
  - Stddev: 789.2000122070312
  - Non-zero count: 3,886,512.796108246


- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.240877807


- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 3.6
  - Median: 0.0
  - Stddev: 271.79998779296875
  - Non-zero count: 34,120.01580810547


- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 4.8
  - Median: 0.0
  - Stddev: 149.0
  - Non-zero count: 64,688.19387817383


- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 1.1
  - Median: 0.0
  - Stddev: 54.599998474121094
  - Non-zero count: 52,551.04342651367


- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 37.0
  - Median: 0.0
  - Stddev: 655.2999877929688
  - Non-zero count: 454,621.24590301514


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 221.8
  - Median: 0.0
  - Stddev: 1,386.4000244140625
  - Non-zero count: 1,403,067.5680217743


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 46.5
  - Median: 0.0
  - Stddev: 738.5999755859375
  - Non-zero count: 575,886.8082809448


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.9
  - Median: 0.0
  - Stddev: 77.0999984741211
  - Non-zero count: 14,535.661651611328


- sda:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 1.0
  - Median: 0.0
  - Stddev: 83.69999694824219
  - Non-zero count: 14,535.661651611328


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 4.0
  - Median: 0.0
  - Stddev: 192.3000030517578
  - Non-zero count: 53,684.06995010376


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 4.0
  - Median: 0.0
  - Stddev: 192.3000030517578
  - Non-zero count: 53,684.06995010376


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 15.7
  - Median: 0.0
  - Stddev: 153.1999969482422
  - Non-zero count: 107,224.60419464111


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 12.4
  - Median: 0.0
  - Stddev: 106.4000015258789
  - Non-zero count: 82,225.57688140869


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 13.0
  - Median: 0.0
  - Stddev: 158.1999969482422
  - Non-zero count: 83,890.6621017456


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 28,560.9
  - Median: 22,283.6
  - Stddev: 28,576.69921875
  - Non-zero count: 25,559,170.808781892


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 83,890.6621017456


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 15.0
  - Median: 0.0
  - Stddev: 171.89999389648438
  - Non-zero count: 255,211.42880249023


- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 195,114.3953514099


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 1.7
  - Median: 0.0
  - Stddev: 79.9000015258789
  - Non-zero count: 29,697.706817626953


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 1.7
  - Median: 0.0
  - Stddev: 79.9000015258789
  - Non-zero count: 29,697.706817626953


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 98.8
  - Median: 0.0
  - Stddev: 727.9000244140625
  - Non-zero count: 413,014.81997299194


- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 413,014.81997299194


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 51.5
  - Median: 0.0
  - Stddev: 524.7000122070312
  - Non-zero count: 528,425.8446960449


- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 413,014.81997299194


- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 413,014.81997299194


- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 71.4
  - Median: 0.0
  - Stddev: 111.0999984741211
  - Non-zero count: 9,051,658.09612152


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 30.1
  - Median: 0.0
  - Stddev: 74.69999694824219
  - Non-zero count: 12,202,686.117177755


- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 394.8
  - Median: 0.0
  - Stddev: 1,291.699951171875
  - Non-zero count: 2,586,254.827071011


- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 4,840,140.619937897


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 15,020.3
  - Median: 0.0
  - Stddev: 27,093.0
  - Non-zero count: 33,290,615.656076342


- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 36.3
  - Median: 0.0
  - Stddev: 284.79998779296875
  - Non-zero count: 527,441.4348181486


- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1,404.8
  - Median: 0.0
  - Stddev: 2,430.300048828125
  - Non-zero count: 7,547,397.831964016


- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 177.9
  - Median: 0.0
  - Stddev: 1,040.5999755859375
  - Non-zero count: 1,489,546.2673780918


- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 15,071,619.939631462


- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 401.0
  - Median: 0.0
  - Stddev: 1,329.9000244140625
  - Non-zero count: 2,586,254.827071011


- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 20,658.0
  - Median: 13,993.9
  - Stddev: 27,406.099609375
  - Non-zero count: 17,866,218.720789343


- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1,327.1
  - Median: 0.0
  - Stddev: 2,751.800048828125
  - Non-zero count: 6,389,015.868989706


- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 18,954.8
  - Median: 12,943.3
  - Stddev: 41,242.3984375
  - Non-zero count: 24,494,166.791476995


- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 642.5
  - Median: 0.0
  - Stddev: 1,273.300048828125
  - Non-zero count: 13,971,232.706328869


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 45.0
  - Non-zero count: 57,048.73114013672


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 72.8
  - Median: 0.0
  - Stddev: 215.3000030517578
  - Non-zero count: 5,404,805.651796579


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 2.2
  - Median: 0.0
  - Stddev: 103.19999694824219
  - Non-zero count: 30,780.743911743164


- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 9,449.8
  - Median: 7,159.0
  - Stddev: 4,891.39990234375
  - Non-zero count: 28,397,162.862116516


- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8,624.5
  - Median: 7,756.2
  - Stddev: 1,884.9000244140625
  - Non-zero count: 28,397,861.240877807


- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 13,983.5
  - Median: 15,870.4
  - Stddev: 3,171.89990234375
  - Non-zero count: 67,264,792.51037088


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,198,356.300641686


- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 104.8
  - Median: 0.0
  - Stddev: 475.6000061035156
  - Non-zero count: 2,527,386.6029536724


- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 6,102.5
  - Median: 7,159.0
  - Stddev: 1,189.9000244140625
  - Non-zero count: 28,397,861.240877807


- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 5,940.3
  - Median: 13.0
  - Stddev: 39,384.6015625
  - Non-zero count: 16,480,688.161676675


- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1,823.7
  - Median: 0.0
  - Stddev: 2,593.39990234375
  - Non-zero count: 9,646,083.40521413


- baseline_has_universal_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Universal Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,015,134.9827990532


- baseline_universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit (baseline)
  - Mean: 434.5
  - Median: 0.0
  - Stddev: 2,396.39990234375
  - Non-zero count: 1,015,134.9827990532


- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 21,525,487.50300905


- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 9,646,083.40521413


- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,787,737.880243778


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
  - Mean: 975.8
  - Median: 0.0
  - Stddev: 1,499.699951171875
  - Non-zero count: 4,462,032.563521385


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,149,542.6521868706


- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 7,547,397.831964016


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 952.7
  - Median: 0.0
  - Stddev: 2,799.89990234375
  - Non-zero count: 3,069,014.7228623927


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 187.7
  - Median: 0.0
  - Stddev: 2,213.5
  - Non-zero count: 1,317,979.20964849


- would_claim_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 19,936,292.687026426


- baseline_has_pension_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Pension Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,297,274.160601616


- baseline_pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (baseline)
  - Mean: 99.1
  - Median: 0.0
  - Stddev: 669.0999755859375
  - Non-zero count: 1,297,274.160601616


- guarantee_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 32,575.0
  - Median: 24,818.0
  - Stddev: 38,902.5
  - Non-zero count: 27,169,979.48920539


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 99.1
  - Median: 0.0
  - Stddev: 669.0999755859375
  - Non-zero count: 1,297,274.160601616


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 72.3
  - Median: 0.0
  - Stddev: 622.7999877929688
  - Non-zero count: 773,565.8661546707


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 2,644.5
  - Median: 0.0
  - Stddev: 4,946.7998046875
  - Non-zero count: 6,762,443.147800893


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 26.8
  - Median: 0.0
  - Stddev: 187.39999389648438
  - Non-zero count: 882,421.6132144928


- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 6,762,443.147800893


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 64.3
  - Median: 0.0
  - Stddev: 578.7000122070312
  - Non-zero count: 1,393,219.148532182


- savings_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Savings Credit
  - Mean: 32,350.2
  - Median: 24,299.2
  - Stddev: 38,905.6015625
  - Non-zero count: 27,011,068.83937171


- would_claim_PC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.240877807


- baseline_has_income_support:
  - Type: bool
  - Entity: benunit
  - Description: Receives Income Support (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 192,295.07543563843


- baseline_income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support (baseline)
  - Mean: 36.1
  - Median: 0.0
  - Stddev: 305.20001220703125
  - Non-zero count: 192,295.07543563843


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 36.1
  - Median: 0.0
  - Stddev: 305.20001220703125
  - Non-zero count: 192,295.07543563843


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 50.7
  - Median: 0.0
  - Stddev: 575.2000122070312
  - Non-zero count: 201,977.7630865574


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 28,560.9
  - Median: 22,283.6
  - Stddev: 28,576.69921875
  - Non-zero count: 25,559,170.808781892


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 201,977.7630865574


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 22.9
  - Median: 0.0
  - Stddev: 270.5
  - Non-zero count: 387,696.76667392254


- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,397,861.240877807


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: DLA (mobility) (reported)
  - Mean: 33.7
  - Median: 0.0
  - Stddev: 350.29998779296875
  - Non-zero count: 883,352.1029307842


- dla_m:
  - Type: float
  - Entity: person
  - Description: DLA (mobility)
  - Mean: 33.0
  - Median: 0.0
  - Stddev: 340.8999938964844
  - Non-zero count: 883,352.1029307842


- dla_m_category:
  - Type: Categorical
  - Entity: person
  - Description: DLA (mobility) category


- dla:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 84.8
  - Median: 0.0
  - Stddev: 763.7000122070312
  - Non-zero count: 1,218,320.366149664


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: DLA (self-care) (reported)
  - Mean: 51.3
  - Median: 0.0
  - Stddev: 490.3999938964844
  - Non-zero count: 1,079,949.4091126919


- dla_sc:
  - Type: float
  - Entity: person
  - Description: DLA (self-care)
  - Mean: 51.8
  - Median: 0.0
  - Stddev: 492.0
  - Non-zero count: 1,079,949.4091126919


- dla_sc_category:
  - Type: Categorical
  - Entity: person
  - Description: DLA (Self-care) category


- dla_sc_middle_plus:
  - Type: bool
  - Entity: person
  - Description: Receives at least middle-rate DLA (self-care)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 818,004.742408514


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility) (reported)
  - Mean: 48.4
  - Median: 0.0
  - Stddev: 373.5
  - Non-zero count: 1,394,095.6614701748


- pip_m:
  - Type: float
  - Entity: person
  - Description: PIP (mobility)
  - Mean: 47.6
  - Median: 0.0
  - Stddev: 364.8999938964844
  - Non-zero count: 1,394,095.6614701748


- pip_m_category:
  - Type: Categorical
  - Entity: person
  - Description: PIP (mobility) category


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: PIP (self-care) (reported)
  - Mean: 102.2
  - Median: 0.0
  - Stddev: 633.9000244140625
  - Non-zero count: 1,834,963.5632741451


- pip_dl:
  - Type: float
  - Entity: person
  - Description: PIP (daily living)
  - Mean: 103.9
  - Median: 0.0
  - Stddev: 644.7000122070312
  - Non-zero count: 1,834,963.5632741451


- pip_dl_category:
  - Type: Categorical
  - Entity: person
  - Description: PIP (daily living) category


- pip:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 151.6
  - Median: 0.0
  - Stddev: 956.5999755859375
  - Non-zero count: 1,936,265.709193945


- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 110.2
  - Median: 33.0
  - Stddev: 552.5
  - Non-zero count: 22,477,960.783508748


- baseline_expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected, baseline)
  - Mean: 279.2
  - Median: 49.8
  - Stddev: 1,372.300048828125
  - Non-zero count: 22,929,836.933825463


- change_in_expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Change in expected Stamp Duty
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 110.2
  - Median: 33.0
  - Stddev: 552.5
  - Non-zero count: 22,477,960.783508748


- corporate_sdlt_change_incidence:
  - Type: float
  - Entity: household
  - Description: Change in corporate Stamp Duty (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected)
  - Mean: 279.2
  - Median: 49.8
  - Stddev: 1,372.300048828125
  - Non-zero count: 22,929,836.933825463


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 24,472,760.19221741


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
  - Mean: 215.2
  - Median: 0.0
  - Stddev: 4,580.60009765625
  - Non-zero count: 461,386.8996887207


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
  - Mean: 3,420.7
  - Median: 0.0
  - Stddev: 23,710.599609375
  - Non-zero count: 5,606,281.097785413


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 3,635.9
  - Median: 0.0
  - Stddev: 25,609.099609375
  - Non-zero count: 5,750,546.514373243


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 3,129.1
  - Median: 0.0
  - Stddev: 21,752.80078125
  - Non-zero count: 5,042,688.924752653


- baseline_child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (baseline)
  - Mean: 337.4
  - Median: 0.0
  - Stddev: 701.0999755859375
  - Non-zero count: 5,646,358.365300655


- baseline_has_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Benefit (baseline)
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,646,358.365300655


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 399.3
  - Median: 0.0
  - Stddev: 741.5999755859375
  - Non-zero count: 6,760,093.540275097


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 338.4
  - Median: 0.0
  - Stddev: 668.0
  - Non-zero count: 5,891,930.477615356


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 157.1
  - Median: 0.0
  - Stddev: 537.7000122070312
  - Non-zero count: 6,342,756.282146692


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 187.4
  - Median: 0.0
  - Stddev: 388.0
  - Non-zero count: 13,726,878.757801533


- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 22,746,695.668193504


- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 1,117.4
  - Median: 334.9
  - Stddev: 5,601.60009765625
  - Non-zero count: 22,477,960.783508748


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,117.4
  - Median: 334.9
  - Stddev: 5,601.60009765625
  - Non-zero count: 22,477,960.783508748


- business_rates_change_incidence:
  - Type: float
  - Entity: household
  - Description: Business rates changes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- change_in_business_rates:
  - Type: float
  - Entity: household
  - Description: Change in expected business rates
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- benunit_tax:
  - Type: float
  - Entity: benunit
  - Description: Benefit unit tax paid
  - Mean: 8,372.9
  - Median: 2,747.5
  - Stddev: 20,847.30078125
  - Non-zero count: 20,540,461.740595132


- household_tax:
  - Type: float
  - Entity: household
  - Description: Taxes
  - Mean: 10,868.0
  - Median: 5,094.4
  - Stddev: 22,718.80078125
  - Non-zero count: 28,043,450.784573525


- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,979.7
  - Median: 36.3
  - Stddev: 14,480.2001953125
  - Non-zero count: 33,900,473.27087703


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,979.7
  - Median: 36.3
  - Stddev: 14,480.2001953125
  - Non-zero count: 33,900,473.27087703


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
  - Mean: 8.9
  - Median: 0.0
  - Stddev: 27.899999618530273
  - Non-zero count: 3,761,919.590400696


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 8.9
  - Median: 0.0
  - Stddev: 27.899999618530273
  - Non-zero count: 3,761,919.590400696


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 24,051,866.137406737


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 865.4
  - Median: 0.0
  - Stddev: 1,871.9000244140625
  - Non-zero count: 23,986,094.23448944


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,218.4
  - Median: 0.0
  - Stddev: 2,753.5
  - Non-zero count: 24,625,182.471592426


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,218.4
  - Median: 0.0
  - Stddev: 2,753.5
  - Non-zero count: 24,625,182.471592426


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,175.9
  - Median: 0.0
  - Stddev: 4,547.5
  - Non-zero count: 28,009,967.668461323


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 98.7
  - Median: 0.0
  - Stddev: 474.20001220703125
  - Non-zero count: 3,362,498.9424438477


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 865.4
  - Median: 0.0
  - Stddev: 1,871.9000244140625
  - Non-zero count: 23,986,094.23448944


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 957.5
  - Median: 0.0
  - Stddev: 1,904.800048828125
  - Non-zero count: 26,948,974.48196113


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 107.5
  - Median: 0.0
  - Stddev: 490.1000061035156
  - Non-zero count: 3,761,919.590400696


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 843.7
  - Median: 0.0
  - Stddev: 13,910.2001953125
  - Non-zero count: 365,909.9068775177


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 379.6
  - Median: 0.0
  - Stddev: 6,259.60009765625
  - Non-zero count: 365,909.9068775177


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 1.1
  - Median: 0.0
  - Stddev: 117.4000015258789
  - Non-zero count: 12,389.363739013672


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7,528.9
  - Median: 0.0
  - Stddev: 14,149.900390625
  - Non-zero count: 30,929,141.469164997


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,505.8
  - Median: 0.0
  - Stddev: 2,830.0
  - Non-zero count: 30,929,141.469164997


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 10.1
  - Median: 0.0
  - Stddev: 370.8999938964844
  - Non-zero count: 101,976.0888967514


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 16.3
  - Median: 0.0
  - Stddev: 396.70001220703125
  - Non-zero count: 581,368.1643883586


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 294.2
  - Median: 0.0
  - Stddev: 9,038.099609375
  - Non-zero count: 1,075,263.3718540072


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,696.6
  - Median: 0.0
  - Stddev: 9,627.5
  - Non-zero count: 30,929,141.469164997


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 10,379.3
  - Median: 0.0
  - Stddev: 26,756.0
  - Non-zero count: 30,929,141.469164997


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 2,006.8
  - Median: 0.0
  - Stddev: 10,438.599609375
  - Non-zero count: 4,169,390.9870408773


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 802.7
  - Median: 0.0
  - Stddev: 4,175.39990234375
  - Non-zero count: 4,169,390.9870408773


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 5.7
  - Median: 0.0
  - Stddev: 533.7000122070312
  - Non-zero count: 34,939.62949371338


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 3,022.2
  - Median: 0.0
  - Stddev: 13,713.400390625
  - Non-zero count: 31,220,284.843987614


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,995.6
  - Median: 0.0
  - Stddev: 13,649.400390625
  - Non-zero count: 31,220,284.843987614


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 35,868,496.54262373


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.30000001192092896
  - Non-zero count: 5,448,210.185401231


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 4.8
  - Median: 0.0
  - Stddev: 237.39999389648438
  - Non-zero count: 135,085.1318883896


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,988.6
  - Median: 5,000.0
  - Stddev: 224.60000610351562
  - Non-zero count: 67,213,914.48050275


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 889.7
  - Median: 0.0
  - Stddev: 25,025.80078125
  - Non-zero count: 1,075,263.3718540072


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 11,286.0
  - Median: 0.0
  - Stddev: 37,806.30078125
  - Non-zero count: 31,220,284.843987614


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 17.0
  - Median: 0.0
  - Stddev: 683.5999755859375
  - Non-zero count: 135,085.1318883896


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
  - Mean: 17.1
  - Median: 0.0
  - Stddev: 378.6000061035156
  - Non-zero count: 156,780.16932678223


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 6.6
  - Median: 0.0
  - Stddev: 170.39999389648438
  - Non-zero count: 114,633.70306777954


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,719.3
  - Median: 10,977.1
  - Stddev: 39,134.6015625
  - Non-zero count: 47,084,931.8050541


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
  - Mean: 23.6
  - Median: 0.0
  - Stddev: 417.0
  - Non-zero count: 270,763.1310005188


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
  - Mean: 468.5
  - Median: 0.0
  - Stddev: 1,316.0
  - Non-zero count: 19,160,993.824376583


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,778.5
  - Median: 0.0
  - Stddev: 1,984.300048828125
  - Non-zero count: 32,471,976.140040636


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 38.4
  - Median: 0.0
  - Stddev: 380.0
  - Non-zero count: 9,138,072.882008255


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 934.2
  - Median: 0.0
  - Stddev: 25,151.400390625
  - Non-zero count: 3,875,087.8333299756


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 11,949.9
  - Median: 0.0
  - Stddev: 22,077.099609375
  - Non-zero count: 28,440,295.539568335


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 43.1
  - Median: 0.0
  - Stddev: 828.5
  - Non-zero count: 776,042.7286429405


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1,599.1
  - Median: 0.0
  - Stddev: 11,354.7998046875
  - Non-zero count: 9,673,347.920187503


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 247.2
  - Median: 0.0
  - Stddev: 4,613.39990234375
  - Non-zero count: 1,818,570.1874465942


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 63.7
  - Median: 0.0
  - Stddev: 819.5
  - Non-zero count: 21,827,581.052438498


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 2,291.9
  - Median: 0.0
  - Stddev: 15,505.400390625
  - Non-zero count: 4,667,139.055475235


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,590.2
  - Median: 0.0
  - Stddev: 3,557.39990234375
  - Non-zero count: 13,084,914.958741218


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 19,278.7
  - Median: 11,222.6
  - Stddev: 39,489.0
  - Non-zero count: 47,082,068.23002663


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
  - Mean: 934.2
  - Median: 0.0
  - Stddev: 25,151.400390625
  - Non-zero count: 3,875,087.8333299756


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 12,380.3
  - Median: 0.0
  - Stddev: 22,673.900390625
  - Non-zero count: 28,378,743.579607397


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1,599.1
  - Median: 0.0
  - Stddev: 11,354.7998046875
  - Non-zero count: 9,673,347.920187503


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 277.3
  - Median: 0.0
  - Stddev: 4,723.60009765625
  - Non-zero count: 2,278,491.874025345


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 99.8
  - Median: 0.0
  - Stddev: 889.0999755859375
  - Non-zero count: 21,972,671.19196868


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 2,354.7
  - Median: 0.0
  - Stddev: 15,580.099609375
  - Non-zero count: 4,840,140.619937897


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,590.2
  - Median: 0.0
  - Stddev: 3,557.39990234375
  - Non-zero count: 13,084,914.958741218


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 158.6
  - Median: 0.0
  - Stddev: 325.20001220703125
  - Non-zero count: 8,928,127.752281904


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 62,755,126.595044285


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 130.3
  - Median: 0.0
  - Stddev: 5,191.2001953125
  - Non-zero count: 14,171,922.907224894


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5,058.2
  - Median: 1,522.9
  - Stddev: 5,179.39990234375
  - Non-zero count: 35,769,363.162572384


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,348.3
  - Median: 12,500.0
  - Stddev: 1,331.699951171875
  - Non-zero count: 66,618,468.934628636


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
  - Non-zero count: 67,264,792.51037088


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
  - Mean: 39,903.6
  - Median: 40,000.0
  - Stddev: 1,637.5
  - Non-zero count: 67,264,792.51037088


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,348.3
  - Median: 12,500.0
  - Stddev: 1,331.699951171875
  - Non-zero count: 66,618,468.934628636


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 67,264,792.51037088


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: 30.1
  - Median: 0.0
  - Stddev: 243.8000030517578
  - Non-zero count: 2,278,491.874025345


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 963.1
  - Median: 1,000.0
  - Stddev: 182.60000610351562
  - Non-zero count: 66,815,424.74154058


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 67,264,792.51037088


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 62.8
  - Median: 0.0
  - Stddev: 463.70001220703125
  - Non-zero count: 4,840,140.619937897


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 26.5
  - Median: 0.0
  - Stddev: 237.39999389648438
  - Non-zero count: 1,303,853.2542846203


- baseline_expected_lbtt:
  - Type: float
  - Entity: household
  - Description: LBTT (expected, baseline)
  - Mean: 41.2
  - Median: 0.0
  - Stddev: 802.0
  - Non-zero count: 882,193.1728057861


- change_in_expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Change in LBTT (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 41.2
  - Median: 0.0
  - Stddev: 802.0
  - Non-zero count: 882,193.1728057861


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 763.6
  - Median: 0.0
  - Stddev: 14,853.2001953125
  - Non-zero count: 882,193.1728057861


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,542,730.671045691


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
  - Mean: 201.7
  - Median: 0.0
  - Stddev: 4,524.89990234375
  - Non-zero count: 461,386.8996887207


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
  - Mean: 9,178.1
  - Median: 0.0
  - Stddev: 37,342.69921875
  - Non-zero count: 10,169,151.219789147


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 9,379.8
  - Median: 0.0
  - Stddev: 38,860.0
  - Non-zero count: 10,219,727.032533288


- baseline_expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (baseline, expected)
  - Mean: 22.4
  - Median: 0.0
  - Stddev: 653.7000122070312
  - Non-zero count: 474,508.85575294495


- change_in_expected_ltt:
  - Type: float
  - Entity: household
  - Description: Change in LTT (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (expected)
  - Mean: 22.4
  - Median: 0.0
  - Stddev: 653.7000122070312
  - Non-zero count: 474,508.85575294495


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 414.1
  - Median: 0.0
  - Stddev: 12,106.7001953125
  - Non-zero count: 474,508.85575294495


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,382,370.375881195


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
  - Mean: 40.4
  - Median: 0.0
  - Stddev: 2,077.199951171875
  - Non-zero count: 18,037.269622802734


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
  - Mean: 7,397.9
  - Median: 0.0
  - Stddev: 31,948.400390625
  - Non-zero count: 10,169,151.219789147


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 7,438.2
  - Median: 0.0
  - Stddev: 32,456.0
  - Non-zero count: 10,171,420.830628991


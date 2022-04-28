# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2022) 2019-20 Family Resources Survey, with simulation turned on.


- in_original_frs:
  - Type: float
  - Entity: household
  - Description: In original FRS
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 23,401,206.79975128


- spi_imputed:
  - Type: float
  - Entity: household
  - Description: SPI imputed
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 5,682,079.139776707


- uc_migrated:
  - Type: float
  - Entity: household
  - Description: UC migrated
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4000000059604645
  - Non-zero count: 5,249,546.773295879


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3,763.7
  - Median: 0.0
  - Stddev: 5,528.2998046875
  - Non-zero count: 27,657,951.104682207


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 665.8
  - Median: 0.0
  - Stddev: 3,162.10009765625
  - Non-zero count: 14,953,608.371474743


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 410.6
  - Median: 0.0
  - Stddev: 1,549.4000244140625
  - Non-zero count: 3,583,440.3489723206


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 3,097.9
  - Median: 0.0
  - Stddev: 5,074.89990234375
  - Non-zero count: 24,112,667.76808858


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 29.3
  - Median: 29.0
  - Stddev: 31.299999237060547
  - Non-zero count: 22,128,586.989771128


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
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 4,662,871.714225769


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1,417.3
  - Median: 0.0
  - Stddev: 3,050.0
  - Non-zero count: 14,974,093.440712214


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 1,041.8
  - Median: 0.0
  - Stddev: 2,801.10009765625
  - Non-zero count: 11,834,105.742687464


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 8,027.3
  - Median: 7,018.4
  - Stddev: 8,533.900390625
  - Non-zero count: 22,273,956.555990458


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 9,127,743.986392975


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 12,621,308.245548248


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 16,874,477.896409035


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,540,155.4443511963


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 20,045,560.847138166


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 18,421,712.152436018


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -665.8
  - Median: 0.0
  - Stddev: 3,162.10009765625
  - Non-zero count: 6,420,531.23060441


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,346.4
  - Median: 0.0
  - Stddev: 4,374.0
  - Non-zero count: 18,460,573.35346532


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,056.1
  - Median: 0.0
  - Stddev: 4,114.0
  - Non-zero count: 16,610,888.369620562


- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: -0.0
  - Median: -0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income
  - Mean: -0.0
  - Median: -0.0
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
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,231,095.766769409


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 870,315.4364318848


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,735,539.265356541


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,007,248.061264992


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 1,066.7
  - Median: 0.0
  - Stddev: 2,594.5
  - Non-zero count: 5,735,539.265356541


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 719.8
  - Median: 0.0
  - Stddev: 2,021.0999755859375
  - Non-zero count: 5,007,248.061264992


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 14,082.9
  - Median: 14,455.1
  - Stddev: 5,705.10009765625
  - Non-zero count: 31,575,730.17763138


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 16,772.1
  - Median: 16,871.0
  - Stddev: 5,520.2001953125
  - Non-zero count: 31,575,730.17763138


- poverty_threshold_bhc:
  - Type: float
  - Entity: household
  - Description: Poverty threshold (BHC)
  - Mean: 16,871.0
  - Median: 16,871.0
  - Stddev: 0.0
  - Non-zero count: 31,575,730.17763138


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
  - Mean: 1,069.2
  - Median: 0.0
  - Stddev: 52,536.19921875
  - Non-zero count: 17,094,141.054442406


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 16,123.8
  - Median: 7,044.5
  - Stddev: 24,920.599609375
  - Non-zero count: 42,013,018.85777974


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 34,762.6
  - Median: 28,477.2
  - Stddev: 45,714.0
  - Non-zero count: 31,467,093.10930252


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 31,456.9
  - Median: 25,602.3
  - Stddev: 46,966.19921875
  - Non-zero count: 30,989,043.19839859


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 34,762.6
  - Median: 28,477.2
  - Stddev: 45,714.0
  - Non-zero count: 31,467,093.10930252


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 21,487.0
  - Median: 15,236.0
  - Stddev: 58,814.6015625
  - Non-zero count: 51,726,439.01248574


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 35,737.8
  - Median: 26,897.0
  - Stddev: 58,237.0
  - Non-zero count: 31,467,093.10930252


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 31,500.7
  - Median: 22,998.5
  - Stddev: 57,945.69921875
  - Non-zero count: 30,989,043.19839859


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 844.6
  - Median: 0.0
  - Stddev: 1,050.0999755859375
  - Non-zero count: 31,007,737.63812256


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 45,463.0
  - Median: 31,197.8
  - Stddev: 90,882.296875
  - Non-zero count: 31,529,818.21162796


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 37,435.7
  - Median: 22,518.0
  - Stddev: 91,993.8984375
  - Non-zero count: 27,593,403.01473379


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 35,737.8
  - Median: 26,897.0
  - Stddev: 58,237.0
  - Non-zero count: 31,467,093.10930252


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 36,676,249.206385136


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
  - Mean: 57.6
  - Median: -1.0
  - Stddev: 1,903.699951171875
  - Non-zero count: 191,360.93504333496


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 34.9
  - Median: 0.0
  - Stddev: 470.79998779296875
  - Non-zero count: 737,888.0174560547


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 17,723.4
  - Median: 7,745.1
  - Stddev: 59,098.19921875
  - Non-zero count: 44,982,800.98618007


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.9
  - Median: 8.9
  - Stddev: 1.7000000476837158
  - Non-zero count: 66,695,051.27413058


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 43.8
  - Median: 0.0
  - Stddev: 775.0
  - Non-zero count: 815,000.479309082


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 17,544.8
  - Median: 14,721.2
  - Stddev: 37,453.5
  - Non-zero count: 51,726,439.01248574


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: 129.7
  - Median: 0.0
  - Stddev: 1,319.5999755859375
  - Non-zero count: 1,079,415.8748950958


- real_household_net_income:
  - Type: float
  - Entity: household
  - Description: Real household net income
  - Mean: 30,935.4
  - Median: 23,282.6
  - Stddev: 50,411.1015625
  - Non-zero count: 31,467,093.10930252


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
  - Mean: 16.2
  - Median: 0.0
  - Stddev: 20.200000762939453
  - Non-zero count: 31,007,737.63812256


- corporate_tax_incidence:
  - Type: float
  - Entity: household
  - Description: Corporate tax incidence
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 17,328,823.7552886


- corporate_wealth:
  - Type: float
  - Entity: household
  - Description: Corporate wealth
  - Mean: 173,767.4
  - Median: 4,998.8
  - Stddev: 1,000,223.375
  - Non-zero count: 17,941,118.15092802


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 17,941,118.15092802


- total_wealth:
  - Type: float
  - Entity: household
  - Description: Total wealth
  - Mean: 379,657.1
  - Median: 186,013.5
  - Stddev: 1,106,692.0
  - Non-zero count: 23,697,465.843559742


- gross_financial_wealth:
  - Type: float
  - Entity: household
  - Description: Gross financial wealth
  - Mean: 62,963.2
  - Median: 3,536.0
  - Stddev: 535,319.0
  - Non-zero count: 26,858,474.31394577


- net_financial_wealth:
  - Type: float
  - Entity: household
  - Description: Net financial wealth
  - Mean: 60,911.7
  - Median: 2,150.0
  - Stddev: 558,605.0
  - Non-zero count: 22,473,449.981702566


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 178,900.0
  - Median: 80,000.0
  - Stddev: 287,949.40625
  - Non-zero count: 17,158,699.632917404


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 2,299.9
  - Median: 0.0
  - Stddev: 35,900.8984375
  - Non-zero count: 312,270.34658908844


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 7,659.8
  - Median: 0.0
  - Stddev: 73,059.796875
  - Non-zero count: 966,562.7686362267


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 205,889.7
  - Median: 100,000.0
  - Stddev: 351,226.0
  - Non-zero count: 18,086,519.053876877


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 186,559.8
  - Median: 90,000.0
  - Stddev: 311,372.90625
  - Non-zero count: 17,402,725.852804184


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 55,833.8
  - Median: 1,606.2
  - Stddev: 321,385.1875
  - Non-zero count: 17,941,118.15092802


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 138,010.2
  - Median: 66,328.0
  - Stddev: 238,156.0
  - Non-zero count: 18,131,084.098371506


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 193,844.0
  - Median: 102,732.1
  - Stddev: 426,301.6875
  - Non-zero count: 23,719,324.007927418


- owned_land:
  - Type: float
  - Entity: household
  - Description: Owned land
  - Mean: 1,447.7
  - Median: 0.0
  - Stddev: 29,495.0
  - Non-zero count: 232,511.7098312378


- carbon_consumption:
  - Type: float
  - Entity: household
  - Description: Carbon consumption
  - Mean: 16.9
  - Median: 12.5
  - Stddev: 15.800000190734863
  - Non-zero count: 31,573,827.67848587


- diesel_litres:
  - Type: float
  - Entity: household
  - Description: Diesel volume
  - Mean: 387.6
  - Median: 0.0
  - Stddev: 813.5999755859375
  - Non-zero count: 9,902,401.915458202


- diesel_price:
  - Type: float
  - Entity: household
  - Description: Price of diesel per litre
  - Mean: 1.5
  - Median: 1.5
  - Stddev: 0.0
  - Non-zero count: 31,575,730.17763138


- petrol_litres:
  - Type: float
  - Entity: household
  - Description: Petrol volume
  - Mean: 588.4
  - Median: 240.4
  - Stddev: 828.7999877929688
  - Non-zero count: 16,568,357.580362558


- petrol_price:
  - Type: float
  - Entity: household
  - Description: Price of petrol per litre
  - Mean: 1.5
  - Median: 1.5
  - Stddev: 0.0
  - Non-zero count: 31,575,730.17763138


- additional_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (additional)
  - Mean: 7,659.8
  - Median: 0.0
  - Stddev: 73,059.796875
  - Non-zero count: 966,562.7686362267


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
  - Mean: 178,900.0
  - Median: 80,000.0
  - Stddev: 287,949.40625
  - Non-zero count: 17,158,699.632917404


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 6,050,861.538839817


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 2,299.9
  - Median: 0.0
  - Stddev: 35,900.8984375
  - Non-zero count: 312,270.34658908844


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
  - Non-zero count: 31,575,730.17763138


- property_sale_rate:
  - Type: float
  - Entity: state
  - Description: Residential property sale rate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 4.0


- rent:
  - Type: float
  - Entity: household
  - Description: Rent
  - Mean: 2,772.9
  - Median: -52.0
  - Stddev: 4,234.7998046875
  - Non-zero count: 11,959,202.336536646


- alcohol_and_tobacco_consumption:
  - Type: float
  - Entity: household
  - Description: Alcohol and tobacco
  - Mean: 826.1
  - Median: 312.0
  - Stddev: 1,515.5999755859375
  - Non-zero count: 20,675,668.297002792


- clothing_and_footwear_consumption:
  - Type: float
  - Entity: household
  - Description: Clothing and footwear
  - Mean: 1,502.3
  - Median: 528.6
  - Stddev: 2,951.199951171875
  - Non-zero count: 21,671,265.493161917


- communication_consumption:
  - Type: float
  - Entity: household
  - Description: Communication
  - Mean: 742.7
  - Median: 434.2
  - Stddev: 1,748.4000244140625
  - Non-zero count: 26,405,250.253314257


- diesel_spending:
  - Type: float
  - Entity: household
  - Description: Diesel spending
  - Mean: 577.9
  - Median: 0.0
  - Stddev: 1,213.0
  - Non-zero count: 9,902,401.915458202


- education_consumption:
  - Type: float
  - Entity: household
  - Description: Education
  - Mean: 298.0
  - Median: 0.0
  - Stddev: 2,993.199951171875
  - Non-zero count: 1,588,477.5725998878


- food_and_non_alcoholic_beverages_consumption:
  - Type: float
  - Entity: household
  - Description: Food and alcoholic beverages
  - Mean: 4,146.5
  - Median: 3,663.7
  - Stddev: 2,352.89990234375
  - Non-zero count: 31,543,959.996341705


- health_consumption:
  - Type: float
  - Entity: household
  - Description: Health
  - Mean: 495.0
  - Median: 34.5
  - Stddev: 1,967.699951171875
  - Non-zero count: 18,189,940.511796713


- household_furnishings_consumption:
  - Type: float
  - Entity: household
  - Description: Household furnishings
  - Mean: 2,265.0
  - Median: 665.9
  - Stddev: 5,353.10009765625
  - Non-zero count: 30,172,358.260484695


- housing_water_and_electricity_consumption:
  - Type: float
  - Entity: household
  - Description: Housing, water and electricity
  - Mean: 5,363.3
  - Median: 3,029.0
  - Stddev: 6,339.7001953125
  - Non-zero count: 31,549,685.22475052


- miscellaneous_consumption:
  - Type: float
  - Entity: household
  - Description: Miscellaneous
  - Mean: 2,784.7
  - Median: 1,371.2
  - Stddev: 5,188.2998046875
  - Non-zero count: 30,939,974.66065216


- petrol_spending:
  - Type: float
  - Entity: household
  - Description: Petrol spending
  - Mean: 877.3
  - Median: 358.4
  - Stddev: 1,235.699951171875
  - Non-zero count: 16,568,357.580362558


- recreation_consumption:
  - Type: float
  - Entity: household
  - Description: Recreation
  - Mean: 4,908.7
  - Median: 1,955.2
  - Stddev: 8,734.0
  - Non-zero count: 31,275,679.65755987


- restaurants_and_hotels_consumption:
  - Type: float
  - Entity: household
  - Description: Restaurants and hotels
  - Mean: 3,264.7
  - Median: 1,787.9
  - Stddev: 4,403.0
  - Non-zero count: 27,641,854.369239807


- transport_consumption:
  - Type: float
  - Entity: household
  - Description: Transport
  - Mean: 5,313.9
  - Median: 2,599.4
  - Stddev: 9,563.900390625
  - Non-zero count: 27,871,264.300993443


- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2,420.2
  - Median: 0.0
  - Stddev: 3,804.800048828125
  - Non-zero count: 12,774,141.899501085


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 110.7
  - Median: 0.0
  - Stddev: 830.5999755859375
  - Non-zero count: 2,424,456.769264221


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,380.8
  - Median: 1,324.2
  - Stddev: 681.7999877929688
  - Non-zero count: 30,578,262.988497734


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,262.4
  - Median: 1,287.6
  - Stddev: 780.0
  - Non-zero count: 28,532,728.479865074


- domestic_rates:
  - Type: float
  - Entity: household
  - Description: Domestic rates
  - Mean: 18.2
  - Median: 0.0
  - Stddev: 291.0
  - Non-zero count: 504,711.448182106


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
  - Mean: 2,371.5
  - Median: -52.0
  - Stddev: 3,995.800048828125
  - Non-zero count: 11,959,202.336536646


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 4,237.1
  - Median: 3,224.0
  - Stddev: 4,298.7998046875
  - Non-zero count: 31,393,661.68255806


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 69.2
  - Median: 0.0
  - Stddev: 369.5
  - Non-zero count: 2,782,675.229490757


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 44.9
  - Median: 0.0
  - Stddev: 806.5
  - Non-zero count: 783,151.6271057129


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
  - Mean: 2,119.8
  - Median: 0.0
  - Stddev: 6,467.0
  - Non-zero count: 8,253,056.769306183


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 825.3
  - Median: -52.0
  - Stddev: 2,137.0
  - Non-zero count: 8,229,251.19260025


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 466.4
  - Median: 0.0
  - Stddev: 1,388.5
  - Non-zero count: 17,328,646.72824669


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,312.8
  - Median: 0.0
  - Stddev: 3,131.39990234375
  - Non-zero count: 11,959,202.336536646


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 28.6
  - Median: 0.0
  - Stddev: 179.6999969482422
  - Non-zero count: 2,019,034.7571353912


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 364.0
  - Median: 343.2
  - Stddev: 253.8000030517578
  - Non-zero count: 30,149,903.16299534


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.1
  - Median: 0.0
  - Stddev: 16.0
  - Non-zero count: 2,424,456.769264221


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


- count_children_and_qyp:
  - Type: int
  - Entity: benunit
  - Description: Children and qualifying young people
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 7,622,594.3276901245


- age:
  - Type: int
  - Entity: person
  - Description: Age
  - Mean: 40.3
  - Median: 40.0
  - Stddev: 23.3
  - Non-zero count: 65,973,107.688738585


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 40,003,935.636916876


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 12,761,457.276995659


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,929,658.360218048


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1,981.7
  - Median: 1,982.0
  - Stddev: 23.3
  - Non-zero count: 66,695,051.27413058


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 79.4
  - Median: 100.0
  - Stddev: 38.6
  - Non-zero count: 66,695,051.27413058


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
  - Non-zero count: 11,862,385.219054699


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 40,793,961.71122408


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 52,765,392.913912535


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,085,271.103462219


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 36,920,038.7435472


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,929,658.360218048


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,548,145.621925354


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 33,758,140.264205694


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 31,575,730.17763138


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 32,936,911.00992489


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,344,987.878097534


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,584,670.482120514


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
  - Non-zero count: 54,731,505.755762815


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 96,576,636.6
  - Median: 96,671,408.1
  - Stddev: 55,492,068.3
  - Non-zero count: 66,695,051.27413058


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight
  - Mean: 2,454.6
  - Median: 1,959.1
  - Stddev: 1,226.9000244140625
  - Non-zero count: 66,695,051.27413058


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- original_weight:
  - Type: float
  - Entity: household
  - Description: Original FRS weight
  - Mean: 1,427.6
  - Median: 1,395.0
  - Stddev: 1,001.7000122070312
  - Non-zero count: 23,401,206.79975128


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 96,576,445.6
  - Median: 96,671,008.0
  - Stddev: 55,492,072.0
  - Non-zero count: 66,695,051.27413058


- person_benunit_role:
  - Type: Categorical
  - Entity: person
  - Description: Role (adult/child)


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 96,575,328.9
  - Median: 96,670,008.0
  - Stddev: 55,492,072.0
  - Non-zero count: 66,695,051.27413058


- person_household_role:
  - Type: Categorical
  - Entity: person
  - Description: Role (adult/child)


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
  - Stddev: 0.4000000059604645
  - Non-zero count: 31,575,730.17763138


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.30000001192092896
  - Non-zero count: 31,575,730.17763138


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 96,306,754.3
  - Median: 96,389,077.9
  - Stddev: 55,444,806.3
  - Non-zero count: 31,575,730.17763138


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.2
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 31,575,730.17763138


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.1
  - Median: 2.0
  - Stddev: 1.2
  - Non-zero count: 31,575,730.17763138


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 2,576.2
  - Median: 2,047.9
  - Stddev: 1,283.9000244140625
  - Non-zero count: 31,575,730.17763138


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 31,575,730.17763138


- is_renting:
  - Type: bool
  - Entity: household
  - Description: Is renting
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 8,929,260.03078556


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
  - Non-zero count: 31,575,730.17763138


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
  - Mean: 96,445,480.3
  - Median: 96,831,749.6
  - Stddev: 55,337,732.9
  - Non-zero count: 36,920,038.7435472


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
  - Mean: 2,593.4
  - Median: 2,077.6
  - Stddev: 1,292.0
  - Non-zero count: 36,920,038.7435472


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 49.4
  - Median: 50.0
  - Stddev: 19.0
  - Non-zero count: 36,920,038.7435472


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7,730,931.95822525


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,920,038.7435472


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
  - Mean: 1.4
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 36,271,405.45788741


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 8,548,145.621925354


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 47.8
  - Median: 48.0
  - Stddev: 18.899999618530273
  - Non-zero count: 36,920,038.7435472


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: inf
  - Stddev: nan
  - Non-zero count: 36,201,277.98896575


- person_state_id:
  - Type: int
  - Entity: person
  - Description: State ID
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- person_state_role:
  - Type: Categorical
  - Entity: person
  - Description: State role


- state_id:
  - Type: int
  - Entity: state
  - Description: State ID
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 4.0


- state_weight:
  - Type: float
  - Entity: state
  - Description: State weight
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 4.0


- benunit_has_carer:
  - Type: bool
  - Entity: benunit
  - Description: Benefit unit has a carer
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 641,530.6734428406


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 34.1
  - Median: 0.0
  - Stddev: 252.1999969482422
  - Non-zero count: 641,530.6734428406


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 645,166.8043022156


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 641,530.6734428406


- is_blind:
  - Type: bool
  - Entity: person
  - Description: Blind
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 185.1
  - Median: 0.0
  - Stddev: 594.9000244140625
  - Non-zero count: 3,211,402.410385132


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 11.0
  - Median: 0.0
  - Stddev: 114.0999984741211
  - Non-zero count: 383,708.83240127563


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,689,903.9129829407


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 433,690.7042579651


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,502,273.6566681862


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,211,402.410385132


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 14,466.166778564453


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 383,708.83240127563


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
  - Non-zero count: 1,330,208.3823456764


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 6,659.615783691406


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 180.5
  - Median: 0.0
  - Stddev: 969.0999755859375
  - Non-zero count: 1,330,208.3823456764


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
  - Mean: 1,082.0
  - Median: 0.0
  - Stddev: 2,188.699951171875
  - Non-zero count: 7,622,594.3276901245


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 38.900001525878906
  - Non-zero count: 4,683.698303222656


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 21.2
  - Median: 0.0
  - Stddev: 104.30000305175781
  - Non-zero count: 1,434,268.3061790466


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 1,103.7
  - Median: 0.0
  - Stddev: 2,239.60009765625
  - Non-zero count: 7,622,594.3276901245


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 11.100000381469727
  - Non-zero count: 2,690.4468383789062


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 53.4
  - Median: 0.0
  - Stddev: 281.3999938964844
  - Non-zero count: 982,591.9182357788


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 7.9
  - Median: 0.0
  - Stddev: 220.5
  - Non-zero count: 159,709.01376342773


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 24.2
  - Median: 0.0
  - Stddev: 187.8000030517578
  - Non-zero count: 434,409.0451698303


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 4.0
  - Median: 0.0
  - Stddev: 111.5999984741211
  - Non-zero count: 45,196.489196777344


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 23.3
  - Median: 0.0
  - Stddev: 204.89999389648438
  - Non-zero count: 417,438.90272140503


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 128.3
  - Median: 0.0
  - Stddev: 758.0
  - Non-zero count: 982,591.9182357788


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 42.0
  - Non-zero count: 31,940.0500831604


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 14.3
  - Median: 0.0
  - Stddev: 89.80000305175781
  - Non-zero count: 635,856.7128067017


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
  - Non-zero count: 36,920,038.7435472


- baseline_has_working_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Working Tax Credit (baseline)
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,920,038.7435472


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
  - Mean: 160.5
  - Median: 0.0
  - Stddev: 1,066.4000244140625
  - Non-zero count: 1,226,691.3524932861


- child_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit pre-minimum
  - Mean: 375.2
  - Median: 0.0
  - Stddev: 1,395.300048828125
  - Non-zero count: 3,008,858.4579353333


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 115.5
  - Median: 0.0
  - Stddev: 950.0999755859375
  - Non-zero count: 1,624,472.4623184204


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit child limit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 61,949,057.78746295


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,434,268.3061790466


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 982,591.9182357788


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 12,621,308.245548248


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 417.8
  - Median: 0.0
  - Stddev: 1,594.5
  - Non-zero count: 3,189,859.01720047


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 34,684.6
  - Median: 21,788.0
  - Stddev: 84,385.1015625
  - Non-zero count: 32,474,147.990228415


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 11,302.8
  - Median: 5,836.4
  - Stddev: 34,174.19921875
  - Non-zero count: 29,897,272.95025468


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 42.6
  - Median: 0.0
  - Stddev: 404.5
  - Non-zero count: 737,631.7640075684


- working_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit pre-minimum
  - Mean: 42.6
  - Median: 0.0
  - Stddev: 404.5
  - Non-zero count: 737,631.7640075684


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 34.7
  - Median: 0.0
  - Stddev: 350.20001220703125
  - Non-zero count: 1,103,818.0721054077


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,624,472.4623184204


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,103,818.0721054077


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 12.9
  - Median: 0.0
  - Stddev: 454.70001220703125
  - Non-zero count: 179,774.66164398193


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 12.9
  - Median: 0.0
  - Stddev: 454.70001220703125
  - Non-zero count: 179,774.66164398193


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 93.9000015258789
  - Non-zero count: 14,580.083557128906


- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 93.9000015258789
  - Non-zero count: 14,580.083557128906


- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 13.5
  - Median: 0.0
  - Stddev: 448.6000061035156
  - Non-zero count: 35,321.62121582031


- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 13.5
  - Median: 0.0
  - Stddev: 448.6000061035156
  - Non-zero count: 35,321.62121582031


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: nan
  - Median: 13,399.9
  - Stddev: nan
  - Non-zero count: 36,920,038.7435472


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,015,687.8672003746


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,971,431.202688456


- state_pension:
  - Type: float
  - Entity: person
  - Description: State Pension
  - Mean: 1,641.7
  - Median: 0.0
  - Stddev: 3,670.39990234375
  - Non-zero count: 12,958,182.85682273


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,641.7
  - Median: 0.0
  - Stddev: 3,670.39990234375
  - Non-zero count: 12,958,182.85682273


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 36.8
  - Median: 0.0
  - Stddev: 449.1000061035156
  - Non-zero count: 630,041.7809615135


- aa_category:
  - Type: Categorical
  - Entity: person
  - Description: Attendance Allowance category


- attendance_allowance:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 37.7
  - Median: 0.0
  - Stddev: 459.1000061035156
  - Non-zero count: 630,041.7809615135


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 8,982.2
  - Median: 7,778.7
  - Stddev: 2,231.300048828125
  - Non-zero count: 36,920,038.7435472


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 1.7
  - Median: 1.0
  - Stddev: 1.0
  - Non-zero count: 36,920,038.7435472


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 2,047.4
  - Median: 0.0
  - Stddev: 2,815.0
  - Non-zero count: 12,774,141.899501085


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
  - Mean: 38.9
  - Median: 0.0
  - Stddev: 493.6000061035156
  - Non-zero count: 395,304.28723859787


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 38.9
  - Median: 0.0
  - Stddev: 493.6000061035156
  - Non-zero count: 395,304.28723859787


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
  - Mean: 34.0
  - Median: 0.0
  - Stddev: 341.0
  - Non-zero count: 645,166.8043022156


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 33.3
  - Median: 0.0
  - Stddev: 332.70001220703125
  - Non-zero count: 645,166.8043022156


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 645,166.8043022156


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 7.1
  - Median: 0.0
  - Stddev: 203.60000610351562
  - Non-zero count: 161,255.80779075623


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 7.1
  - Median: 0.0
  - Stddev: 203.60000610351562
  - Non-zero count: 161,255.80779075623


- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 101.3
  - Median: 0.0
  - Stddev: 256.6000061035156
  - Non-zero count: 4,671,648.780075312


- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 56.1
  - Median: 0.0
  - Stddev: 195.39999389648438
  - Non-zero count: 4,671,648.780075312


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 592.9
  - Median: 191.4
  - Stddev: 610.2000122070312
  - Non-zero count: 33,947,338.094242334


- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 286.9
  - Median: 0.0
  - Stddev: 775.0
  - Non-zero count: 5,893,386.719447613


- baseline_has_housing_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Housing Benefit (baseline)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,900,312.319984436


- baseline_housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit (baseline)
  - Mean: 428.6
  - Median: 0.0
  - Stddev: 931.2000122070312
  - Non-zero count: 2,900,312.319984436


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 428.5
  - Median: 0.0
  - Stddev: 930.7999877929688
  - Non-zero count: 2,900,312.319984436


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 821.8
  - Median: 0.0
  - Stddev: 2,192.5
  - Non-zero count: 3,373,843.423971176


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 26,190.0
  - Median: 19,704.2
  - Stddev: 23,366.599609375
  - Non-zero count: 35,112,218.15658736


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,373,843.423971176


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 291.8
  - Median: 0.0
  - Stddev: 910.0
  - Non-zero count: 3,844,142.322622299


- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,920,038.7435472


- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 2.7
  - Median: 0.0
  - Stddev: 236.1999969482422
  - Non-zero count: 43,484.56042480469


- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 3.8
  - Median: 0.0
  - Stddev: 135.5
  - Non-zero count: 53,116.4157409668


- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 44.5
  - Non-zero count: 59,917.83236694336


- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 42.6
  - Median: 0.0
  - Stddev: 651.2999877929688
  - Non-zero count: 540,502.0551548004


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 197.2
  - Median: 0.0
  - Stddev: 1,401.4000244140625
  - Non-zero count: 1,239,762.3380317688


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 50.4
  - Median: 0.0
  - Stddev: 719.7999877929688
  - Non-zero count: 661,744.1703891754


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 78.80000305175781
  - Non-zero count: 6,062.086273193359


- sda:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 79.5999984741211
  - Non-zero count: 6,062.086273193359


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 3.7
  - Median: 0.0
  - Stddev: 230.8000030517578
  - Non-zero count: 61,422.140548706055


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 3.7
  - Median: 0.0
  - Stddev: 230.8000030517578
  - Non-zero count: 61,422.140548706055


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 8.7
  - Median: 0.0
  - Stddev: 199.39999389648438
  - Non-zero count: 78,165.79895019531


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 6.0
  - Median: 0.0
  - Stddev: 171.8000030517578
  - Non-zero count: 51,951.84646606445


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 6.3
  - Median: 0.0
  - Stddev: 183.39999389648438
  - Non-zero count: 53,565.520111083984


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 25,360.6
  - Median: 18,826.9
  - Stddev: 24,407.69921875
  - Non-zero count: 32,441,162.339677572


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 53,565.520111083984


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 11.0
  - Median: 0.0
  - Stddev: 194.10000610351562
  - Non-zero count: 183,155.51690673828


- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 183,155.51690673828


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 75.80000305175781
  - Non-zero count: 26,213.95248413086


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 75.80000305175781
  - Non-zero count: 26,213.95248413086


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 140.4
  - Median: 0.0
  - Stddev: 670.9000244140625
  - Non-zero count: 500,413.57328796387


- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 500,413.57328796387


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 77.7
  - Median: 0.0
  - Stddev: 494.5
  - Non-zero count: 567,631.6058807373


- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 500,413.57328796387


- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 500,413.57328796387


- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 77.6
  - Median: 0.0
  - Stddev: 113.69999694824219
  - Non-zero count: 10,482,234.660027266


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 36.7
  - Median: 0.0
  - Stddev: 80.30000305175781
  - Non-zero count: 13,154,953.507893562


- armed_forces_independence_payment:
  - Type: float
  - Entity: person
  - Description: Armed Forces Independence Payment
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 412.1
  - Median: 0.0
  - Stddev: 1,227.300048828125
  - Non-zero count: 3,346,865.343826294


- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 4,633,534.050385475


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 14,778.5
  - Median: 1,889.5
  - Stddev: 24,204.80078125
  - Non-zero count: 36,592,400.7046628


- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 34.1
  - Median: 0.0
  - Stddev: 252.8000030517578
  - Non-zero count: 641,530.6734428406


- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1,108.9
  - Median: 0.0
  - Stddev: 2,179.10009765625
  - Non-zero count: 8,548,145.621925354


- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 144.3
  - Median: 0.0
  - Stddev: 932.5
  - Non-zero count: 1,545,336.2920761108


- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 23,232,296.945178032


- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 435.1
  - Median: 0.0
  - Stddev: 1,279.5999755859375
  - Non-zero count: 3,346,865.343826294


- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 18,363.6
  - Median: 11,594.8
  - Stddev: 23,145.30078125
  - Non-zero count: 24,901,882.362211943


- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1,306.3
  - Median: 0.0
  - Stddev: 2,769.699951171875
  - Non-zero count: 9,185,163.551555634


- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 15,198.2
  - Median: 9,737.2
  - Stddev: 73,503.796875
  - Non-zero count: 31,256,377.443721056


- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 613.9
  - Median: 0.0
  - Stddev: 1,191.800048828125
  - Non-zero count: 13,194,089.063648224


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 4.4
  - Median: 0.0
  - Stddev: 49.0
  - Non-zero count: 190,009.48696899414


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 437.2
  - Median: 0.0
  - Stddev: 452.5
  - Non-zero count: 32,175,068.946488142


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 8.3
  - Median: 0.0
  - Stddev: 127.5999984741211
  - Non-zero count: 115,104.01220703125


- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 7,821.7
  - Median: 6,118.9
  - Stddev: 4,681.7001953125
  - Non-zero count: 36,854,888.980630636


- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8,380.1
  - Median: 7,756.2
  - Stddev: 1,694.5999755859375
  - Non-zero count: 36,920,038.7435472


- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 14,412.1
  - Median: 16,216.2
  - Stddev: 3,083.89990234375
  - Non-zero count: 66,695,051.27413058


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,741,344.154300213


- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 224.1
  - Median: 0.0
  - Stddev: 588.7000122070312
  - Non-zero count: 5,611,190.062411785


- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 4,792.9
  - Median: 3,898.1
  - Stddev: 1,184.699951171875
  - Non-zero count: 36,920,038.7435472


- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 5,098.2
  - Median: 0.0
  - Stddev: 73,404.3984375
  - Non-zero count: 17,926,834.043210983


- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1,778.0
  - Median: 0.0
  - Stddev: 2,675.0
  - Non-zero count: 11,310,003.72574997


- baseline_has_universal_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Universal Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,763,231.3717041016


- baseline_universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit (baseline)
  - Mean: 576.0
  - Median: 0.0
  - Stddev: 2,293.300048828125
  - Non-zero count: 1,763,231.3717041016


- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 27,555,175.418246508


- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,310,003.72574997


- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 9,183,664.873550415


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
  - Mean: 798.4
  - Median: 0.0
  - Stddev: 1,929.300048828125
  - Non-zero count: 4,662,871.714225769


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,689,903.9129829407


- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.7
  - Non-zero count: 8,548,145.621925354


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 1,220.6
  - Median: 0.0
  - Stddev: 2,890.699951171875
  - Non-zero count: 5,327,023.910434723


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 287.3
  - Median: 0.0
  - Stddev: 1,697.0999755859375
  - Non-zero count: 2,147,233.0175192356


- would_claim_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 27,689,615.857858658


- baseline_has_income_support:
  - Type: bool
  - Entity: benunit
  - Description: Receives Income Support (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 173,395.9754638672


- baseline_income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support (baseline)
  - Mean: 20.4
  - Median: 0.0
  - Stddev: 441.0
  - Non-zero count: 173,395.9754638672


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 20.4
  - Median: 0.0
  - Stddev: 441.0
  - Non-zero count: 173,395.9754638672


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 31.4
  - Median: 0.0
  - Stddev: 609.0
  - Non-zero count: 183,098.9692993164


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 25,360.6
  - Median: 18,826.9
  - Stddev: 24,407.69921875
  - Non-zero count: 32,441,162.339677572


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 183,098.9692993164


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 21.3
  - Median: 0.0
  - Stddev: 298.3999938964844
  - Non-zero count: 348,559.6297302246


- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,920,038.7435472


- baseline_has_pension_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Pension Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 857,472.683380127


- baseline_pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (baseline)
  - Mean: 84.8
  - Median: 0.0
  - Stddev: 686.5
  - Non-zero count: 857,472.683380127


- would_claim_pc:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 0.7
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 26,291,682.87203765


- pension_credit_income:
  - Type: float
  - Entity: benunit
  - Description: Income for Pension Credit
  - Mean: 37,263.1
  - Median: 24,289.5
  - Stddev: 85,524.5
  - Non-zero count: 32,582,144.796838522


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Pension Credit (reported)
  - Mean: 56.8
  - Median: 0.0
  - Stddev: 528.2000122070312
  - Non-zero count: 1,113,801.7757644653


- is_pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 9,697,269.953926325


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 138.8
  - Median: 0.0
  - Stddev: 869.5
  - Non-zero count: 1,763,562.771396637


- is_savings_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Savings Credit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 31,979,707.772295237


- savings_credit:
  - Type: float
  - Entity: benunit
  - Description: Savings Credit
  - Mean: 123.0
  - Median: 0.0
  - Stddev: 542.5
  - Non-zero count: 3,762,271.9252319336


- savings_credit_income:
  - Type: float
  - Entity: benunit
  - Description: Income for Savings Credit
  - Mean: 37,190.0
  - Median: 24,284.0
  - Stddev: 85,541.1015625
  - Non-zero count: 32,345,775.407106638


- is_guarantee_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Guarantee Credit eligible
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,932,169.57847929


- guarantee_credit:
  - Type: float
  - Entity: benunit
  - Description: Guarantee Credit
  - Mean: 2,186.2
  - Median: 0.0
  - Stddev: 3,941.10009765625
  - Non-zero count: 9,932,169.57847929


- minimum_guarantee:
  - Type: float
  - Entity: benunit
  - Description: Minimum Guarantee
  - Mean: 12,708.0
  - Median: 12,708.8
  - Stddev: 3,712.199951171875
  - Non-zero count: 36,920,038.7435472


- standard_minimum_guarantee:
  - Type: float
  - Entity: benunit
  - Description: Standard Minimum Guarantee
  - Mean: 11,424.3
  - Median: 9,209.2
  - Stddev: 2,418.300048828125
  - Non-zero count: 36,920,038.7435472


- severe_disability_minimum_guarantee_addition:
  - Type: float
  - Entity: benunit
  - Description: Severe disability-related increase
  - Mean: 277.7
  - Median: 0.0
  - Stddev: 985.0999755859375
  - Non-zero count: 2,752,656.800971508


- additional_minimum_guarantee:
  - Type: float
  - Entity: benunit
  - Description: Additional Minimum Guarantee
  - Mean: 1,283.7
  - Median: 0.0
  - Stddev: 2,324.300048828125
  - Non-zero count: 10,817,189.291392803


- child_minimum_guarantee_addition:
  - Type: float
  - Entity: benunit
  - Description: Child-related addition
  - Mean: 971.8
  - Median: 0.0
  - Stddev: 2,182.5
  - Non-zero count: 7,622,594.3276901245


- carer_minimum_guarantee_addition:
  - Type: float
  - Entity: benunit
  - Description: Carer-related increase
  - Mean: 34.3
  - Median: 0.0
  - Stddev: 256.5
  - Non-zero count: 641,530.6734428406


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: DLA (mobility) (reported)
  - Mean: 36.1
  - Median: 0.0
  - Stddev: 326.3999938964844
  - Non-zero count: 931,657.1330165863


- dla_m:
  - Type: float
  - Entity: person
  - Description: DLA (mobility)
  - Mean: 35.5
  - Median: 0.0
  - Stddev: 319.6000061035156
  - Non-zero count: 931,657.1330165863


- dla_m_category:
  - Type: Categorical
  - Entity: person
  - Description: DLA (mobility) category


- dla:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 89.3
  - Median: 0.0
  - Stddev: 705.5999755859375
  - Non-zero count: 1,249,946.577878952


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: DLA (self-care) (reported)
  - Mean: 52.9
  - Median: 0.0
  - Stddev: 445.79998779296875
  - Non-zero count: 1,095,313.356721878


- dla_sc:
  - Type: float
  - Entity: person
  - Description: DLA (self-care)
  - Mean: 53.8
  - Median: 0.0
  - Stddev: 451.70001220703125
  - Non-zero count: 1,095,313.356721878


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
  - Non-zero count: 833,140.1551170349


- receives_highest_dla_sc:
  - Type: bool
  - Entity: person
  - Description: Receives the highest DLA (self-care) category
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 433,690.7042579651


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility) (reported)
  - Mean: 63.1
  - Median: 0.0
  - Stddev: 368.1000061035156
  - Non-zero count: 1,811,139.3997187614


- pip_m:
  - Type: float
  - Entity: person
  - Description: PIP (mobility)
  - Mean: 62.4
  - Median: 0.0
  - Stddev: 361.5
  - Non-zero count: 1,811,139.3997187614


- pip_m_category:
  - Type: Categorical
  - Entity: person
  - Description: PIP (mobility) category


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: PIP (self-care) (reported)
  - Mean: 127.7
  - Median: 0.0
  - Stddev: 623.5
  - Non-zero count: 2,290,543.9439907074


- pip_dl:
  - Type: float
  - Entity: person
  - Description: PIP (daily living)
  - Mean: 130.5
  - Median: 0.0
  - Stddev: 637.2999877929688
  - Non-zero count: 2,290,543.9439907074


- pip_dl_category:
  - Type: Categorical
  - Entity: person
  - Description: PIP (daily living) category


- receives_enhanced_pip_dl:
  - Type: bool
  - Entity: person
  - Description: Receives enhanced PIP (daily living)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,011,797.4456963539


- pip:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 192.9
  - Median: 0.0
  - Stddev: 943.7000122070312
  - Non-zero count: 2,444,954.5510463715


- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 99.1
  - Median: 2.9
  - Stddev: 570.5999755859375
  - Non-zero count: 17,941,118.15092802


- baseline_expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected, baseline)
  - Mean: 304.5
  - Median: 40.6
  - Stddev: 998.2000122070312
  - Non-zero count: 21,145,909.360301495


- change_in_expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Change in expected Stamp Duty
  - Mean: -0.7
  - Median: 0.0
  - Stddev: 44.0
  - Non-zero count: 11,557,541.642100096


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 99.1
  - Median: 2.9
  - Stddev: 570.5999755859375
  - Non-zero count: 17,941,118.15092802


- corporate_sdlt_change_incidence:
  - Type: float
  - Entity: household
  - Description: Change in corporate Stamp Duty (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 15,420,570.119990349


- expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected)
  - Mean: 303.8
  - Median: 40.2
  - Stddev: 998.2999877929688
  - Non-zero count: 21,117,402.738900185


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 27,261,897.80324459


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
  - Mean: 55.6
  - Median: 0.0
  - Stddev: 1,253.5
  - Non-zero count: 128,344.88301086426


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
  - Mean: 5,291.4
  - Median: 0.0
  - Stddev: 18,754.69921875
  - Non-zero count: 12,688,792.043118


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 5,347.1
  - Median: 0.0
  - Stddev: 18,951.30078125
  - Non-zero count: 12,697,331.957355976


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 4,663.1
  - Median: 0.0
  - Stddev: 17,366.400390625
  - Non-zero count: 11,002,418.098279476


- baseline_child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (baseline)
  - Mean: 243.6
  - Median: 0.0
  - Stddev: 624.2000122070312
  - Non-zero count: 5,749,700.15013504


- baseline_has_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Benefit (baseline)
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,749,700.15013504


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 301.2
  - Median: 0.0
  - Stddev: 669.7999877929688
  - Non-zero count: 7,146,699.900085449


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 252.4
  - Median: 0.0
  - Stddev: 619.2999877929688
  - Non-zero count: 6,228,559.9379348755


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 145.8
  - Median: 0.0
  - Stddev: 487.20001220703125
  - Non-zero count: 6,291,557.360759735


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 177.7
  - Median: 0.0
  - Stddev: 362.6000061035156
  - Non-zero count: 12,621,308.245548248


- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 29,726,567.64100933


- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 1,005.0
  - Median: 28.9
  - Stddev: 5,784.7001953125
  - Non-zero count: 17,941,118.15092802


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,005.0
  - Median: 28.9
  - Stddev: 5,784.7001953125
  - Non-zero count: 17,941,118.15092802


- business_rates_change_incidence:
  - Type: float
  - Entity: household
  - Description: Business rates changes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 16,484,696.249043941


- change_in_business_rates:
  - Type: float
  - Entity: household
  - Description: Change in expected business rates
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 16,484,696.249043941


- benunit_tax:
  - Type: float
  - Entity: benunit
  - Description: Benefit unit tax paid
  - Mean: 7,121.5
  - Median: 1,829.6
  - Stddev: 30,645.599609375
  - Non-zero count: 25,370,119.991782427


- household_tax:
  - Type: float
  - Entity: household
  - Description: Taxes
  - Mean: 9,725.2
  - Median: 3,917.0
  - Stddev: 33,157.30078125
  - Non-zero count: 31,426,698.370624542


- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,942.2
  - Median: 18.5
  - Stddev: 21,743.0
  - Non-zero count: 33,488,698.274615765


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,942.2
  - Median: 18.5
  - Stddev: 21,743.0
  - Non-zero count: 33,488,698.274615765


- tax_reported:
  - Type: float
  - Entity: person
  - Description: Reported tax paid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_fuel_duty:
  - Type: float
  - Entity: household
  - Description: Baseline fuel duty (cars only)
  - Mean: 565.6
  - Median: 404.2
  - Stddev: 679.0
  - Non-zero count: 21,361,007.827809095


- change_in_fuel_duty:
  - Type: float
  - Entity: household
  - Description: Change in fuel duty
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- fuel_duty:
  - Type: float
  - Entity: household
  - Description: Fuel duty (cars only)
  - Mean: 565.6
  - Median: 404.2
  - Stddev: 679.0
  - Non-zero count: 21,361,007.827809095


- NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 7.1
  - Median: 0.0
  - Stddev: 31.5
  - Non-zero count: 2,979,152.6279268265


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 7.1
  - Median: 0.0
  - Stddev: 31.5
  - Non-zero count: 2,979,152.6279268265


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 23,934,976.721056223


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 895.1
  - Median: 0.0
  - Stddev: 1,630.199951171875
  - Non-zero count: 22,866,373.81344509


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,282.5
  - Median: 0.0
  - Stddev: 2,716.10009765625
  - Non-zero count: 23,394,142.267357826


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,282.5
  - Median: 0.0
  - Stddev: 2,716.10009765625
  - Non-zero count: 23,394,142.267357826


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,238.6
  - Median: 0.0
  - Stddev: 4,240.2001953125
  - Non-zero count: 26,090,456.676369667


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 59.8
  - Median: 0.0
  - Stddev: 421.1000061035156
  - Non-zero count: 2,429,243.813013315


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 895.1
  - Median: 0.0
  - Stddev: 1,630.199951171875
  - Non-zero count: 22,866,373.81344509


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 956.0
  - Median: 0.0
  - Stddev: 1,654.5999755859375
  - Non-zero count: 25,292,643.42389822


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 66.9
  - Median: 0.0
  - Stddev: 440.8999938964844
  - Non-zero count: 2,979,152.6279268265


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 659.9
  - Median: 0.0
  - Stddev: 9,336.400390625
  - Non-zero count: 409,689.2397994995


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 297.0
  - Median: 0.0
  - Stddev: 4,201.39990234375
  - Non-zero count: 409,689.2397994995


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.9
  - Median: 0.0
  - Stddev: 52.599998474121094
  - Non-zero count: 22,677.84521484375


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7,554.4
  - Median: 0.0
  - Stddev: 12,059.599609375
  - Non-zero count: 30,625,730.973334312


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,510.9
  - Median: 0.0
  - Stddev: 2,411.89990234375
  - Non-zero count: 30,625,730.973334312


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 9.4
  - Median: 0.0
  - Stddev: 365.70001220703125
  - Non-zero count: 101,223.55423736572


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 15.0
  - Median: 0.0
  - Stddev: 381.0
  - Non-zero count: 503,215.07137298584


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 319.1
  - Median: 0.0
  - Stddev: 19,260.400390625
  - Non-zero count: 1,134,978.0151004791


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,637.3
  - Median: 0.0
  - Stddev: 8,275.7998046875
  - Non-zero count: 30,625,730.973334312


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 10,266.9
  - Median: 0.0
  - Stddev: 23,639.19921875
  - Non-zero count: 30,625,730.973334312


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 2,052.6
  - Median: 0.0
  - Stddev: 10,721.400390625
  - Non-zero count: 4,301,487.214130402


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 821.0
  - Median: 0.0
  - Stddev: 4,288.5
  - Non-zero count: 4,301,487.214130402


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 1.0
  - Median: 0.0
  - Stddev: 102.30000305175781
  - Non-zero count: 22,336.610927581787


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2,986.2
  - Median: 0.0
  - Stddev: 21,353.900390625
  - Non-zero count: 30,999,479.735711098


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,959.2
  - Median: 0.0
  - Stddev: 21,265.30078125
  - Non-zero count: 30,999,479.735711098


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 36,920,038.7435472


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.30000001192092896
  - Non-zero count: 5,487,726.185651779


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 2.7
  - Median: 0.0
  - Stddev: 91.69999694824219
  - Non-zero count: 134,941.08464050293


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,989.4
  - Median: 5,000.0
  - Stddev: 189.10000610351562
  - Non-zero count: 66,644,355.02668834


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 930.2
  - Median: 0.0
  - Stddev: 52,379.3984375
  - Non-zero count: 1,134,978.0151004791


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 11,208.5
  - Median: 0.0
  - Stddev: 58,191.69921875
  - Non-zero count: 30,999,479.735711098


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 11.4
  - Median: 0.0
  - Stddev: 396.6000061035156
  - Non-zero count: 134,941.08464050293


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
  - Mean: 18.2
  - Median: 0.0
  - Stddev: 346.5
  - Non-zero count: 161,653.99100494385


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 5.4
  - Median: 0.0
  - Stddev: 160.39999389648438
  - Non-zero count: 98,204.11657714844


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,754.6
  - Median: 11,133.6
  - Stddev: 58,721.30078125
  - Non-zero count: 46,827,728.0633471


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
  - Mean: 23.7
  - Median: 0.0
  - Stddev: 381.6000061035156
  - Non-zero count: 259,858.10758209229


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
  - Mean: 495.0
  - Median: 0.0
  - Stddev: 1,407.4000244140625
  - Non-zero count: 18,595,634.24248314


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,790.0
  - Median: 0.0
  - Stddev: 2,136.199951171875
  - Non-zero count: 32,688,784.21565008


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 46.4
  - Median: 0.0
  - Stddev: 425.6000061035156
  - Non-zero count: 7,757,876.59350872


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 990.9
  - Median: 0.0
  - Stddev: 52,482.6015625
  - Non-zero count: 5,493,064.511787415


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 12,520.8
  - Median: 0.0
  - Stddev: 21,542.19921875
  - Non-zero count: 32,449,033.50922346


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 43.8
  - Median: 0.0
  - Stddev: 775.0
  - Non-zero count: 815,000.479309082


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1,717.5
  - Median: 0.0
  - Stddev: 8,497.599609375
  - Non-zero count: 11,406,391.432303667


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 332.2
  - Median: 0.0
  - Stddev: 6,762.7998046875
  - Non-zero count: 2,090,374.8555979729


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 47.9
  - Median: 0.0
  - Stddev: 497.79998779296875
  - Non-zero count: 12,382,078.259560585


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1,385.5
  - Median: 0.0
  - Stddev: 10,705.2001953125
  - Non-zero count: 4,162,739.828083992


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,716.1
  - Median: 0.0
  - Stddev: 3,688.89990234375
  - Non-zero count: 14,009,409.172160387


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 19,319.8
  - Median: 11,439.6
  - Stddev: 59,001.30078125
  - Non-zero count: 46,946,727.82903314


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
  - Mean: 990.9
  - Median: 0.0
  - Stddev: 52,482.6015625
  - Non-zero count: 5,493,064.511787415


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 12,979.0
  - Median: 0.0
  - Stddev: 22,294.900390625
  - Non-zero count: 32,389,981.89444685


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1,717.5
  - Median: 0.0
  - Stddev: 8,497.599609375
  - Non-zero count: 11,406,391.432303667


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 366.9
  - Median: 0.0
  - Stddev: 6,854.2998046875
  - Non-zero count: 2,601,445.6563329697


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 78.3
  - Median: 0.0
  - Stddev: 626.7000122070312
  - Non-zero count: 14,539,621.220402718


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 1,427.3
  - Median: 0.0
  - Stddev: 10,832.400390625
  - Non-zero count: 4,633,534.050385475


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,716.1
  - Median: 0.0
  - Stddev: 3,688.89990234375
  - Non-zero count: 14,009,409.172160387


- total_pension_income:
  - Type: float
  - Entity: person
  - Description: Total pension income
  - Mean: 3,359.2
  - Median: 0.0
  - Stddev: 10,245.0
  - Non-zero count: 15,531,027.84817481


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 151.6
  - Median: 0.0
  - Stddev: 382.8999938964844
  - Non-zero count: 8,434,326.87864995


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 62,080,960.8932302


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 181.3
  - Median: 0.0
  - Stddev: 5,277.2001953125
  - Non-zero count: 13,845,520.208180666


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5,008.4
  - Median: 1,436.4
  - Stddev: 5,425.0
  - Non-zero count: 35,456,018.42490935


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,414.1
  - Median: 12,570.0
  - Stddev: 1,327.4000244140625
  - Non-zero count: 66,059,722.769560575


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
  - Non-zero count: 66,695,051.27413058


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
  - Mean: 39,899.4
  - Median: 40,000.0
  - Stddev: 2,120.5
  - Non-zero count: 66,695,051.27413058


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,414.1
  - Median: 12,570.0
  - Stddev: 1,327.4000244140625
  - Non-zero count: 66,059,722.769560575


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: 34.8
  - Median: 0.0
  - Stddev: 213.60000610351562
  - Non-zero count: 2,601,445.6563329697


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 962.0
  - Median: 1,000.0
  - Stddev: 145.6999969482422
  - Non-zero count: 66,234,672.01511264


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 66,695,051.27413058


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 41.8
  - Median: 0.0
  - Stddev: 707.7000122070312
  - Non-zero count: 4,633,534.050385475


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 27.0
  - Median: 0.0
  - Stddev: 209.1999969482422
  - Non-zero count: 1,361,994.258014679


- baseline_expected_lbtt:
  - Type: float
  - Entity: household
  - Description: LBTT (expected, baseline)
  - Mean: 32.0
  - Median: 0.0
  - Stddev: 461.5
  - Non-zero count: 1,109,821.0458555222


- change_in_expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Change in LBTT (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 3.0999999046325684
  - Non-zero count: 174,434.3025112152


- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 32.0
  - Median: 0.0
  - Stddev: 461.5
  - Non-zero count: 1,124,151.4052305222


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 729.6
  - Median: 0.0
  - Stddev: 10,516.599609375
  - Non-zero count: 1,124,151.4052305222


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,766,317.5565538406


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
  - Mean: 52.2
  - Median: 0.0
  - Stddev: 1,211.5
  - Non-zero count: 128,344.88301086426


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
  - Mean: 7,938.2
  - Median: 0.0
  - Stddev: 26,948.69921875
  - Non-zero count: 13,065,371.031747818


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 7,990.4
  - Median: 0.0
  - Stddev: 27,132.80078125
  - Non-zero count: 13,072,471.56146431


- baseline_expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (baseline, expected)
  - Mean: 10.3
  - Median: 0.0
  - Stddev: 190.8000030517578
  - Non-zero count: 542,144.1506919861


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
  - Mean: 10.3
  - Median: 0.0
  - Stddev: 190.8000030517578
  - Non-zero count: 542,144.1506919861


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 234.2
  - Median: 0.0
  - Stddev: 4,347.5
  - Non-zero count: 542,144.1506919861


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,547,514.8178329468


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
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 79.9000015258789
  - Non-zero count: 2,879.43408203125


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
  - Mean: 6,442.1
  - Median: 0.0
  - Stddev: 22,374.5
  - Non-zero count: 11,544,044.194823742


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 6,442.4
  - Median: 0.0
  - Stddev: 22,375.0
  - Non-zero count: 11,544,044.194823742


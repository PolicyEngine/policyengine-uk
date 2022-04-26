# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2022) 2019-20 Family Resources Survey, with simulation turned on.


- in_original_frs:
  - Type: float
  - Entity: household
  - Description: In original FRS
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 25,262,401.67829895


- spi_imputed:
  - Type: float
  - Entity: household
  - Description: SPI imputed
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4000000059604645
  - Non-zero count: 2,196,798.202069193


- uc_migrated:
  - Type: float
  - Entity: household
  - Description: UC migrated
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 2,117,363.9047864974


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3,538.6
  - Median: 0.0
  - Stddev: 5,789.7998046875
  - Non-zero count: 26,616,841.26214692


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 630.4
  - Median: 0.0
  - Stddev: 3,444.5
  - Non-zero count: 14,300,055.42207089


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 375.3
  - Median: 0.0
  - Stddev: 1,579.300048828125
  - Non-zero count: 3,135,688.1490659714


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2,908.2
  - Median: 0.0
  - Stddev: 5,357.89990234375
  - Non-zero count: 22,861,121.49988526


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 31.2
  - Median: 35.0
  - Stddev: 30.200000762939453
  - Non-zero count: 22,791,889.585928172


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
  - Non-zero count: 4,295,344.807775497


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1,250.8
  - Median: 0.0
  - Stddev: 3,386.699951171875
  - Non-zero count: 14,651,614.868334204


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 937.7
  - Median: 0.0
  - Stddev: 3,183.89990234375
  - Non-zero count: 10,924,323.321943283


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 8,410.2
  - Median: 7,363.0
  - Stddev: 9,013.2998046875
  - Non-zero count: 20,387,039.594753355


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 10,008,288.463448226


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,587,051.760222733


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 17,399,012.886896282


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,508,230.187517166


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 18,745,127.983162284


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 17,146,342.374735236


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -630.4
  - Median: 0.0
  - Stddev: 3,444.5
  - Non-zero count: 6,550,203.4326581955


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,287.8
  - Median: 0.0
  - Stddev: 4,516.89990234375
  - Non-zero count: 17,704,902.935673177


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1,970.6
  - Median: 0.0
  - Stddev: 4,205.5
  - Non-zero count: 15,672,064.596939504


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
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,813,798.3362865448


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 747,034.8711776733


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,434,051.158005714


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,611,527.674956322


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 1,100.9
  - Median: 0.0
  - Stddev: 2,816.800048828125
  - Non-zero count: 5,434,051.158005714


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 742.3
  - Median: 0.0
  - Stddev: 2,230.0
  - Non-zero count: 4,611,527.674956322


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 15,339.6
  - Median: 14,455.1
  - Stddev: 6,114.7998046875
  - Non-zero count: 28,554,269.10323161


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 17,971.4
  - Median: 16,871.0
  - Stddev: 5,899.7001953125
  - Non-zero count: 28,554,269.10323161


- poverty_threshold_bhc:
  - Type: float
  - Entity: household
  - Description: Poverty threshold (BHC)
  - Mean: 16,871.0
  - Median: 16,871.0
  - Stddev: 0.0
  - Non-zero count: 28,554,269.10323161


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
  - Mean: 1,282.5
  - Median: 0.0
  - Stddev: 51,333.3984375
  - Non-zero count: 23,372,779.198782265


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 15,723.8
  - Median: 6,864.0
  - Stddev: 37,401.8984375
  - Non-zero count: 40,512,251.02392146


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 35,049.7
  - Median: 28,407.9
  - Stddev: 51,901.3984375
  - Non-zero count: 28,486,532.01526469


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 31,617.3
  - Median: 25,580.9
  - Stddev: 53,321.5
  - Non-zero count: 28,094,392.990743816


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 35,049.7
  - Median: 28,407.9
  - Stddev: 51,901.3984375
  - Non-zero count: 28,486,532.01526469


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 21,233.0
  - Median: 15,017.8
  - Stddev: 64,194.3984375
  - Non-zero count: 51,412,765.94594991


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 38,270.0
  - Median: 29,202.8
  - Stddev: 64,256.8984375
  - Non-zero count: 28,486,532.01526469


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 34,060.5
  - Median: 25,310.3
  - Stddev: 63,873.1015625
  - Non-zero count: 28,094,392.990743816


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 873.4
  - Median: 0.0
  - Stddev: 1,035.199951171875
  - Non-zero count: 31,855,637.068116903


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 50,076.8
  - Median: 34,828.0
  - Stddev: 103,348.203125
  - Non-zero count: 28,525,429.606039226


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 41,666.6
  - Median: 26,312.0
  - Stddev: 104,563.703125
  - Non-zero count: 25,409,484.12445277


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 38,270.0
  - Median: 29,202.8
  - Stddev: 64,256.8984375
  - Non-zero count: 28,486,532.01526469


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 34,432,483.07013348


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
  - Mean: 83.4
  - Median: -1.0
  - Stddev: 2,141.699951171875
  - Non-zero count: 256,058.92094230652


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 34.0
  - Median: 0.0
  - Stddev: 481.0
  - Non-zero count: 715,832.8599662781


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 17,694.4
  - Median: 7,740.0
  - Stddev: 64,480.1015625
  - Non-zero count: 45,220,909.67612827


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.9
  - Median: 8.9
  - Stddev: 1.7000000476837158
  - Non-zero count: 67,239,322.06306267


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 59.5
  - Median: 0.0
  - Stddev: 1,002.9000244140625
  - Non-zero count: 771,787.4630403519


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 17,257.3
  - Median: 14,492.5
  - Stddev: 39,686.69921875
  - Non-zero count: 51,412,765.94594991


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: 110.9
  - Median: 0.0
  - Stddev: 1,486.699951171875
  - Non-zero count: 1,171,882.585793972


- real_household_net_income:
  - Type: float
  - Entity: household
  - Description: Real household net income
  - Mean: 33,127.2
  - Median: 25,278.5
  - Stddev: 55,622.0
  - Non-zero count: 28,486,532.01526469


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
  - Non-zero count: 31,855,637.068116903


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
  - Mean: 358,571.1
  - Median: 125,284.9
  - Stddev: 1,371,022.375
  - Non-zero count: 22,987,657.523749888


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 22,987,657.523749888


- total_wealth:
  - Type: float
  - Entity: household
  - Description: Total wealth
  - Mean: 653,189.3
  - Median: 347,640.9
  - Stddev: 1,527,302.625
  - Non-zero count: 25,060,300.119156778


- gross_financial_wealth:
  - Type: float
  - Entity: household
  - Description: Gross financial wealth
  - Mean: 189,541.6
  - Median: 30,026.9
  - Stddev: 1,068,570.375
  - Non-zero count: 27,657,035.614601314


- net_financial_wealth:
  - Type: float
  - Entity: household
  - Description: Net financial wealth
  - Mean: 184,530.7
  - Median: 27,290.1
  - Stddev: 1,069,140.5
  - Non-zero count: 22,751,057.342936188


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 225,958.1
  - Median: 149,000.0
  - Stddev: 310,853.8125
  - Non-zero count: 18,107,816.797572345


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 10,070.0
  - Median: 0.0
  - Stddev: 93,943.0
  - Non-zero count: 1,144,783.5358160138


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 31,969.3
  - Median: 0.0
  - Stddev: 137,675.296875
  - Non-zero count: 3,602,005.252691269


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 294,618.1
  - Median: 172,866.9
  - Stddev: 440,782.0
  - Non-zero count: 19,104,571.99468538


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 257,927.4
  - Median: 156,000.0
  - Stddev: 369,108.8125
  - Non-zero count: 18,562,516.159478635


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 61,560.6
  - Median: 21,509.3
  - Stddev: 235,381.40625
  - Non-zero count: 22,987,657.523749888


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 162,861.4
  - Median: 89,639.2
  - Stddev: 304,490.0
  - Non-zero count: 19,276,742.931046695


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 224,422.0
  - Median: 123,770.0
  - Stddev: 415,958.40625
  - Non-zero count: 25,128,531.11282438


- owned_land:
  - Type: float
  - Entity: household
  - Description: Owned land
  - Mean: 11,950.9
  - Median: 0.0
  - Stddev: 151,052.59375
  - Non-zero count: 1,170,859.0618499517


- carbon_consumption:
  - Type: float
  - Entity: household
  - Description: Carbon consumption
  - Mean: 19.0
  - Median: 14.0
  - Stddev: 18.5
  - Non-zero count: 28,542,069.03493327


- diesel_litres:
  - Type: float
  - Entity: household
  - Description: Diesel volume
  - Mean: 403.1
  - Median: 0.0
  - Stddev: 795.5
  - Non-zero count: 8,958,554.066563666


- diesel_price:
  - Type: float
  - Entity: household
  - Description: Price of diesel per litre
  - Mean: 1.5
  - Median: 1.5
  - Stddev: 0.0
  - Non-zero count: 28,554,269.10323161


- petrol_litres:
  - Type: float
  - Entity: household
  - Description: Petrol volume
  - Mean: 575.6
  - Median: 144.8
  - Stddev: 805.2000122070312
  - Non-zero count: 14,567,475.974196553


- petrol_price:
  - Type: float
  - Entity: household
  - Description: Price of petrol per litre
  - Mean: 1.5
  - Median: 1.5
  - Stddev: 0.0
  - Non-zero count: 28,554,269.10323161


- additional_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (additional)
  - Mean: 31,969.3
  - Median: 0.0
  - Stddev: 137,675.296875
  - Non-zero count: 3,602,005.252691269


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
  - Mean: 225,958.1
  - Median: 149,000.0
  - Stddev: 310,853.8125
  - Non-zero count: 18,107,816.797572345


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,507,226.005473405


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 10,070.0
  - Median: 0.0
  - Stddev: 93,943.0
  - Non-zero count: 1,144,783.5358160138


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
  - Non-zero count: 28,554,269.10323161


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
  - Mean: 2,674.1
  - Median: -52.0
  - Stddev: 4,559.7001953125
  - Non-zero count: 10,134,834.55674693


- alcohol_and_tobacco_consumption:
  - Type: float
  - Entity: household
  - Description: Alcohol and tobacco
  - Mean: 725.9
  - Median: 240.2
  - Stddev: 1,298.4000244140625
  - Non-zero count: 17,884,893.402352035


- clothing_and_footwear_consumption:
  - Type: float
  - Entity: household
  - Description: Clothing and footwear
  - Mean: 1,476.4
  - Median: 503.6
  - Stddev: 2,689.89990234375
  - Non-zero count: 19,258,927.861445636


- communication_consumption:
  - Type: float
  - Entity: household
  - Description: Communication
  - Mean: 716.2
  - Median: 432.9
  - Stddev: 1,712.0999755859375
  - Non-zero count: 23,775,385.130108416


- diesel_spending:
  - Type: float
  - Entity: household
  - Description: Diesel spending
  - Mean: 601.0
  - Median: 0.0
  - Stddev: 1,186.0999755859375
  - Non-zero count: 8,958,554.066563666


- education_consumption:
  - Type: float
  - Entity: household
  - Description: Education
  - Mean: 645.2
  - Median: 0.0
  - Stddev: 4,846.10009765625
  - Non-zero count: 2,638,581.702819526


- food_and_non_alcoholic_beverages_consumption:
  - Type: float
  - Entity: household
  - Description: Food and alcoholic beverages
  - Mean: 3,575.9
  - Median: 3,089.0
  - Stddev: 2,243.0
  - Non-zero count: 28,415,837.250731647


- health_consumption:
  - Type: float
  - Entity: household
  - Description: Health
  - Mean: 543.6
  - Median: 59.5
  - Stddev: 1,832.9000244140625
  - Non-zero count: 17,901,583.38948545


- household_furnishings_consumption:
  - Type: float
  - Entity: household
  - Description: Household furnishings
  - Mean: 2,548.3
  - Median: 772.8
  - Stddev: 5,302.39990234375
  - Non-zero count: 27,386,598.92419696


- housing_water_and_electricity_consumption:
  - Type: float
  - Entity: household
  - Description: Housing, water and electricity
  - Mean: 4,905.4
  - Median: 2,510.7
  - Stddev: 6,722.7001953125
  - Non-zero count: 28,457,050.95742625


- miscellaneous_consumption:
  - Type: float
  - Entity: household
  - Description: Miscellaneous
  - Mean: 3,577.8
  - Median: 1,719.1
  - Stddev: 6,703.89990234375
  - Non-zero count: 28,256,603.628636062


- petrol_spending:
  - Type: float
  - Entity: household
  - Description: Petrol spending
  - Mean: 858.2
  - Median: 215.9
  - Stddev: 1,200.5999755859375
  - Non-zero count: 14,567,475.974196553


- recreation_consumption:
  - Type: float
  - Entity: household
  - Description: Recreation
  - Mean: 5,123.2
  - Median: 2,125.5
  - Stddev: 9,034.900390625
  - Non-zero count: 28,323,644.358120143


- restaurants_and_hotels_consumption:
  - Type: float
  - Entity: household
  - Description: Restaurants and hotels
  - Mean: 3,524.0
  - Median: 2,024.8
  - Stddev: 4,587.39990234375
  - Non-zero count: 25,666,611.029856503


- transport_consumption:
  - Type: float
  - Entity: household
  - Description: Transport
  - Mean: 6,180.2
  - Median: 3,133.6
  - Stddev: 10,641.900390625
  - Non-zero count: 25,762,526.874604583


- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2,168.6
  - Median: 0.0
  - Stddev: 3,905.60009765625
  - Non-zero count: 11,198,118.913994372


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 110.1
  - Median: 0.0
  - Stddev: 850.2000122070312
  - Non-zero count: 2,432,410.7274161577


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,378.3
  - Median: 1,340.3
  - Stddev: 654.0
  - Non-zero count: 27,571,689.00710529


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,253.2
  - Median: 1,300.0
  - Stddev: 777.0
  - Non-zero count: 25,539,615.035176694


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
  - Mean: 2,112.6
  - Median: -52.0
  - Stddev: 4,222.2001953125
  - Non-zero count: 10,134,834.55674693


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 4,209.5
  - Median: 3,016.0
  - Stddev: 4,576.60009765625
  - Non-zero count: 28,446,863.455737293


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 66.4
  - Median: 0.0
  - Stddev: 355.79998779296875
  - Non-zero count: 2,593,845.60706836


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 38.4
  - Median: 0.0
  - Stddev: 628.2000122070312
  - Non-zero count: 714,935.5672094822


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
  - Mean: 2,276.1
  - Median: 0.0
  - Stddev: 6,055.60009765625
  - Non-zero count: 8,135,845.406061083


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 882.6
  - Median: -52.0
  - Stddev: 2,067.800048828125
  - Non-zero count: 8,113,820.679307848


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 452.1
  - Median: 0.0
  - Stddev: 1,271.4000244140625
  - Non-zero count: 18,102,369.04482028


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,135.6
  - Median: 0.0
  - Stddev: 3,318.199951171875
  - Non-zero count: 10,134,834.55674693


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 27.5
  - Median: 0.0
  - Stddev: 164.3000030517578
  - Non-zero count: 2,021,003.1847229302


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 377.2
  - Median: 358.8
  - Stddev: 246.6999969482422
  - Non-zero count: 27,284,872.602359474


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.1
  - Median: 0.0
  - Stddev: 16.299999237060547
  - Non-zero count: 2,432,410.7274161577


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
  - Stddev: 23.5
  - Non-zero count: 66,488,837.18433237


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 40,036,183.23662686


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 12,445,041.232886732


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 14,758,097.593549073


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1,982.9
  - Median: 1,983.0
  - Stddev: 23.5
  - Non-zero count: 67,239,322.06306267


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 78.4
  - Median: 100.0
  - Stddev: 39.4
  - Non-zero count: 67,239,322.06306267


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
  - Non-zero count: 10,230,321.239154816


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 40,987,472.7695055


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 52,481,224.469513595


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 7,885,940.911652118


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 36,144,140.87005857


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 14,758,097.593549073


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,443,678.907532245


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 33,959,705.423692435


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 28,554,269.10323161


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 33,279,616.639370233


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,335,915.4918804467


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,422,182.101668626


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
  - Non-zero count: 54,332,925.76004857


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 96,031,862.3
  - Median: 95,917,161.3
  - Stddev: 55,233,272.5
  - Non-zero count: 67,239,322.06306267


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight
  - Mean: 2,118.4
  - Median: 1,853.2
  - Stddev: 1,051.9000244140625
  - Non-zero count: 67,239,322.06306267


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 96,031,658.1
  - Median: 95,916,971.8
  - Stddev: 55,233,272.0
  - Non-zero count: 67,239,322.06306267


- person_benunit_role:
  - Type: Categorical
  - Entity: person
  - Description: Role (adult/child)


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 96,030,486.9
  - Median: 95,915,524.2
  - Stddev: 55,233,272.0
  - Non-zero count: 67,239,322.06306267


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
  - Mean: 1.1
  - Median: 1.0
  - Stddev: 0.4000000059604645
  - Non-zero count: 28,554,269.10323161


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.1
  - Median: 1.0
  - Stddev: 0.30000001192092896
  - Non-zero count: 28,554,269.10323161


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 95,806,941.8
  - Median: 95,591,175.9
  - Stddev: 55,273,490.5
  - Non-zero count: 28,554,269.10323161


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.3
  - Median: 1.0
  - Stddev: 0.6
  - Non-zero count: 28,554,269.10323161


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.4
  - Median: 2.0
  - Stddev: 1.3
  - Non-zero count: 28,554,269.10323161


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 2,001.2
  - Median: 1,762.9
  - Stddev: 992.2000122070312
  - Non-zero count: 28,554,269.10323161


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,554,269.10323161


- is_renting:
  - Type: bool
  - Entity: household
  - Description: Is renting
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,380,751.182626694


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
  - Non-zero count: 28,554,269.10323161


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
  - Mean: 95,760,560.4
  - Median: 95,591,000.1
  - Stddev: 55,183,478.6
  - Non-zero count: 36,144,140.87005857


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
  - Mean: 2,121.6
  - Median: 1,848.9
  - Stddev: 1,047.800048828125
  - Non-zero count: 36,144,140.87005857


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 47.7
  - Median: 48.0
  - Stddev: 19.399999618530273
  - Non-zero count: 36,144,140.87005857


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7,593,703.518631488


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,144,140.87005857


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
  - Non-zero count: 35,486,478.47676328


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 8,443,678.907532245


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 46.0
  - Median: 45.0
  - Stddev: 19.200000762939453
  - Non-zero count: 36,144,140.87005857


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: nan
  - Median: inf
  - Stddev: nan
  - Non-zero count: 35,399,583.952204734


- person_state_id:
  - Type: int
  - Entity: person
  - Description: State ID
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


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
  - Non-zero count: 584,523.5082798004


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 31.7
  - Median: 0.0
  - Stddev: 265.8999938964844
  - Non-zero count: 584,523.5082798004


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 588,273.4450473785


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 584,523.5082798004


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 168.8
  - Median: 0.0
  - Stddev: 615.7999877929688
  - Non-zero count: 2,812,444.737687111


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 10.3
  - Median: 0.0
  - Stddev: 113.30000305175781
  - Non-zero count: 349,318.2344055176


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,026,306.8587350845


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 355,189.04092407227


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,220,639.2119369507


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,812,444.737687111


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 14,319.2021484375


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 349,318.2344055176


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
  - Non-zero count: 1,168,353.4309158325


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 8,002.5015869140625


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 164.5
  - Median: 0.0
  - Stddev: 978.0
  - Non-zero count: 1,168,353.4309158325


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
  - Mean: 1,142.2
  - Median: 0.0
  - Stddev: 2,221.800048828125
  - Non-zero count: 7,604,576.012337238


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 48.29999923706055
  - Non-zero count: 5,611.2418212890625


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 22.6
  - Median: 0.0
  - Stddev: 93.30000305175781
  - Non-zero count: 1,497,773.115433097


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 1,165.4
  - Median: 0.0
  - Stddev: 2,263.199951171875
  - Non-zero count: 7,604,576.012337238


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 12.0
  - Non-zero count: 3,192.1424560546875


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 58.9
  - Median: 0.0
  - Stddev: 260.20001220703125
  - Non-zero count: 1,062,242.0773214102


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 12.8
  - Median: 0.0
  - Stddev: 221.10000610351562
  - Non-zero count: 193,223.30617177486


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 26.1
  - Median: 0.0
  - Stddev: 173.10000610351562
  - Non-zero count: 457,341.3122638464


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 6.7
  - Median: 0.0
  - Stddev: 113.9000015258789
  - Non-zero count: 74,863.90287780762


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 29.0
  - Median: 0.0
  - Stddev: 189.60000610351562
  - Non-zero count: 509,276.93778800964


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 149.2
  - Median: 0.0
  - Stddev: 715.4000244140625
  - Non-zero count: 1,062,242.0773214102


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 1.8
  - Median: 0.0
  - Stddev: 42.400001525878906
  - Non-zero count: 45,215.787006378174


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 13.9
  - Median: 0.0
  - Stddev: 81.5
  - Non-zero count: 603,643.1160196066


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
  - Non-zero count: 36,144,140.87005857


- baseline_has_working_tax_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Working Tax Credit (baseline)
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,144,140.87005857


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
  - Mean: 208.7
  - Median: 0.0
  - Stddev: 943.0
  - Non-zero count: 1,319,221.3318634033


- child_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit pre-minimum
  - Mean: 453.4
  - Median: 0.0
  - Stddev: 1,530.4000244140625
  - Non-zero count: 3,159,612.625453949


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 128.8
  - Median: 0.0
  - Stddev: 843.5
  - Non-zero count: 1,627,944.0341590643


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit child limit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 62,266,757.37181795


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,497,773.115433097


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,062,242.0773214102


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,587,051.760222733


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 524.1
  - Median: 0.0
  - Stddev: 1,701.5999755859375
  - Non-zero count: 3,329,891.0022850037


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 35,680.8
  - Median: 22,464.0
  - Stddev: 93,276.296875
  - Non-zero count: 31,806,944.136042148


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 11,711.1
  - Median: 6,142.7
  - Stddev: 37,830.5
  - Non-zero count: 29,472,435.673414737


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 70.7
  - Median: 0.0
  - Stddev: 406.6000061035156
  - Non-zero count: 876,496.4974822998


- working_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit pre-minimum
  - Mean: 70.7
  - Median: 0.0
  - Stddev: 406.6000061035156
  - Non-zero count: 876,496.4974822998


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 42.4
  - Median: 0.0
  - Stddev: 351.1000061035156
  - Non-zero count: 1,190,157.5173085928


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,627,944.0341590643


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,190,157.5173085928


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 11.0
  - Median: 0.0
  - Stddev: 413.29998779296875
  - Non-zero count: 152,353.50714492798


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 11.0
  - Median: 0.0
  - Stddev: 413.29998779296875
  - Non-zero count: 152,353.50714492798


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 87.80000305175781
  - Non-zero count: 12,630.140808105469


- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 87.80000305175781
  - Non-zero count: 12,630.140808105469


- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 10.4
  - Median: 0.0
  - Stddev: 485.5
  - Non-zero count: 27,311.686332702637


- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 10.4
  - Median: 0.0
  - Stddev: 485.5
  - Non-zero count: 27,311.686332702637


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: nan
  - Median: 13,399.9
  - Stddev: nan
  - Non-zero count: 36,144,140.87005857


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,930,509.2179174423


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,493,751.700008094


- state_pension:
  - Type: float
  - Entity: person
  - Description: State Pension
  - Mean: 1,608.9
  - Median: 0.0
  - Stddev: 3,745.10009765625
  - Non-zero count: 12,824,677.907904088


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,608.9
  - Median: 0.0
  - Stddev: 3,745.10009765625
  - Non-zero count: 12,824,677.907904088


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 50.9
  - Median: 0.0
  - Stddev: 497.29998779296875
  - Non-zero count: 868,770.7076538801


- aa_category:
  - Type: Categorical
  - Entity: person
  - Description: Attendance Allowance category


- attendance_allowance:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 52.0
  - Median: 0.0
  - Stddev: 508.29998779296875
  - Non-zero count: 868,770.7076538801


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 9,549.5
  - Median: 9,753.1
  - Stddev: 2,457.800048828125
  - Non-zero count: 36,144,140.87005857


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 2.0
  - Median: 2.0
  - Stddev: 1.100000023841858
  - Non-zero count: 36,144,140.87005857


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 1,843.4
  - Median: 0.0
  - Stddev: 2,931.89990234375
  - Non-zero count: 11,198,118.913994372


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
  - Stddev: 521.7000122070312
  - Non-zero count: 331,941.6319360733


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 31.4
  - Median: 0.0
  - Stddev: 521.7000122070312
  - Non-zero count: 331,941.6319360733


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
  - Mean: 30.8
  - Median: 0.0
  - Stddev: 361.29998779296875
  - Non-zero count: 588,273.4450473785


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 30.1
  - Median: 0.0
  - Stddev: 353.0
  - Non-zero count: 588,273.4450473785


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 588,273.4450473785


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 7.2
  - Median: 0.0
  - Stddev: 197.5
  - Non-zero count: 148,610.40618515015


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 7.2
  - Median: 0.0
  - Stddev: 197.5
  - Non-zero count: 148,610.40618515015


- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 98.9
  - Median: 0.0
  - Stddev: 285.0
  - Non-zero count: 4,328,427.430448413


- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 53.2
  - Median: 0.0
  - Stddev: 218.6999969482422
  - Non-zero count: 4,328,427.430448413


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 604.7
  - Median: 191.4
  - Stddev: 611.4000244140625
  - Non-zero count: 35,191,733.28302753


- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 470.3
  - Median: 0.0
  - Stddev: 918.9000244140625
  - Non-zero count: 8,873,591.115546346


- baseline_has_housing_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Housing Benefit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 330.8
  - Median: 0.0
  - Stddev: 868.2999877929688
  - Non-zero count: 2,714,424.8098506927


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 755.0
  - Median: 0.0
  - Stddev: 2,185.699951171875
  - Non-zero count: 2,970,627.8606214523


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 26,384.2
  - Median: 19,861.2
  - Stddev: 30,775.599609375
  - Non-zero count: 34,374,993.41848624


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,970,627.8606214523


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 253.6
  - Median: 0.0
  - Stddev: 914.0999755859375
  - Non-zero count: 3,550,468.789457321


- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,144,140.87005857


- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 5.3
  - Median: 0.0
  - Stddev: 318.1000061035156
  - Non-zero count: 38,210.00619506836


- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 4.2
  - Median: 0.0
  - Stddev: 156.1999969482422
  - Non-zero count: 59,349.19867706299


- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 0.9
  - Median: 0.0
  - Stddev: 43.599998474121094
  - Non-zero count: 45,767.17613220215


- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 41.5
  - Median: 0.0
  - Stddev: 778.5999755859375
  - Non-zero count: 477,379.87365436554


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 224.6
  - Median: 0.0
  - Stddev: 1,538.199951171875
  - Non-zero count: 1,470,659.2303991318


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 51.8
  - Median: 0.0
  - Stddev: 870.5
  - Non-zero count: 588,913.9909410477


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.8
  - Median: 0.0
  - Stddev: 57.400001525878906
  - Non-zero count: 12,816.54459285736


- sda:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 0.9
  - Median: 0.0
  - Stddev: 65.30000305175781
  - Non-zero count: 12,816.54459285736


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 4.3
  - Median: 0.0
  - Stddev: 190.89999389648438
  - Non-zero count: 57,022.80386734009


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 4.3
  - Median: 0.0
  - Stddev: 190.89999389648438
  - Non-zero count: 57,022.80386734009


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 9.9
  - Median: 0.0
  - Stddev: 174.3000030517578
  - Non-zero count: 88,472.46475028992


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 6.3
  - Median: 0.0
  - Stddev: 133.10000610351562
  - Non-zero count: 54,204.5407409668


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 6.9
  - Median: 0.0
  - Stddev: 150.39999389648438
  - Non-zero count: 56,614.978088378906


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 25,555.2
  - Median: 19,126.1
  - Stddev: 31,634.5
  - Non-zero count: 31,762,710.055456758


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 56,614.978088378906


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 11.2
  - Median: 0.0
  - Stddev: 187.6999969482422
  - Non-zero count: 188,841.2974395752


- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 188,841.2974395752


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 1.9
  - Median: 0.0
  - Stddev: 84.4000015258789
  - Non-zero count: 34,267.92400932312


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 1.9
  - Median: 0.0
  - Stddev: 84.4000015258789
  - Non-zero count: 34,267.92400932312


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 79.2
  - Median: 0.0
  - Stddev: 650.0999755859375
  - Non-zero count: 402,875.4299545288


- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 402,875.4299545288


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 42.6
  - Median: 0.0
  - Stddev: 482.79998779296875
  - Non-zero count: 411,770.25453948975


- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 402,875.4299545288


- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 402,875.4299545288


- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 77.6
  - Median: 0.0
  - Stddev: 114.9000015258789
  - Non-zero count: 9,540,825.560111344


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 33.0
  - Median: 0.0
  - Stddev: 79.69999694824219
  - Non-zero count: 12,826,006.58387798


- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 345.3
  - Median: 0.0
  - Stddev: 1,268.4000244140625
  - Non-zero count: 2,858,800.7575235367


- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 4,175,640.6977385283


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 14,938.7
  - Median: 1,522.9
  - Stddev: 37,212.80078125
  - Non-zero count: 34,370,945.66784504


- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 31.8
  - Median: 0.0
  - Stddev: 266.5
  - Non-zero count: 584,523.5082798004


- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1,177.7
  - Median: 0.0
  - Stddev: 2,249.800048828125
  - Non-zero count: 8,443,678.907532245


- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 147.1
  - Median: 0.0
  - Stddev: 942.2999877929688
  - Non-zero count: 1,519,132.8197327852


- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 21,225,406.266597122


- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 352.1
  - Median: 0.0
  - Stddev: 1,313.800048828125
  - Non-zero count: 2,858,800.7575235367


- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 19,081.5
  - Median: 13,261.9
  - Stddev: 30,025.0
  - Non-zero count: 23,671,908.818345606


- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1,028.4
  - Median: 0.0
  - Stddev: 2,922.89990234375
  - Non-zero count: 8,001,651.48728615


- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 14,991.6
  - Median: 9,757.4
  - Stddev: 74,288.3984375
  - Non-zero count: 30,846,576.42927602


- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 633.1
  - Median: 0.0
  - Stddev: 1,209.5
  - Non-zero count: 13,749,974.600902617


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 49.900001525878906
  - Non-zero count: 54,692.99230957031


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 440.0
  - Median: 0.0
  - Stddev: 453.1000061035156
  - Non-zero count: 32,644,123.848999023


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 2.4
  - Median: 0.0
  - Stddev: 118.0
  - Non-zero count: 33,613.67724609375


- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 7,566.7
  - Median: 6,118.9
  - Stddev: 4,939.89990234375
  - Non-zero count: 35,993,268.46081784


- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8,453.9
  - Median: 7,756.2
  - Stddev: 1,739.5999755859375
  - Non-zero count: 36,144,140.87005857


- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 14,305.0
  - Median: 16,216.2
  - Stddev: 3,145.39990234375
  - Non-zero count: 67,239,322.06306267


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,052,811.1743706465


- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 360.3
  - Median: 0.0
  - Stddev: 690.4000244140625
  - Non-zero count: 8,390,336.870431066


- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 4,829.6
  - Median: 3,898.1
  - Stddev: 1,196.0999755859375
  - Non-zero count: 36,144,140.87005857


- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 4,496.8
  - Median: 3.0
  - Stddev: 73,240.1015625
  - Non-zero count: 19,309,802.02488488


- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1,770.1
  - Median: 0.0
  - Stddev: 2,677.39990234375
  - Non-zero count: 10,780,733.571810275


- baseline_has_universal_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Universal Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 27,901,158.69912669


- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,780,733.571810275


- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 9,785,532.902304351


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
  - Mean: 717.9
  - Median: 0.0
  - Stddev: 1,781.0999755859375
  - Non-zero count: 4,295,344.807775497


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,026,306.8587350845


- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.7
  - Non-zero count: 8,443,678.907532245


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 1,102.6
  - Median: 0.0
  - Stddev: 3,525.39990234375
  - Non-zero count: 5,006,486.605466843


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 235.0
  - Median: 0.0
  - Stddev: 2,291.39990234375
  - Non-zero count: 1,554,400.9394574165


- would_claim_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 27,250,437.19493723


- baseline_has_pension_credit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Pension Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- guarantee_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 29,216.2
  - Median: 21,138.9
  - Stddev: 58,653.69921875
  - Non-zero count: 33,706,624.29152158


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 80.9
  - Median: 0.0
  - Stddev: 594.9000244140625
  - Non-zero count: 1,338,011.1094360352


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 62.7
  - Median: 0.0
  - Stddev: 547.5
  - Non-zero count: 848,252.2827301025


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 2,355.4
  - Median: 0.0
  - Stddev: 4,984.2001953125
  - Non-zero count: 7,655,977.704196036


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 18.2
  - Median: 0.0
  - Stddev: 166.39999389648438
  - Non-zero count: 849,915.0264129639


- is_pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,655,977.704196036


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 54.8
  - Median: 0.0
  - Stddev: 523.5999755859375
  - Non-zero count: 1,231,041.3284056187


- savings_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Savings Credit
  - Mean: 29,054.5
  - Median: 20,791.1
  - Stddev: 58,653.8984375
  - Non-zero count: 33,533,872.699450046


- would_claim_PC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,144,140.87005857


- baseline_has_income_support:
  - Type: bool
  - Entity: benunit
  - Description: Receives Income Support (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 22.2
  - Median: 0.0
  - Stddev: 379.79998779296875
  - Non-zero count: 154,730.59803771973


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 33.1
  - Median: 0.0
  - Stddev: 520.0999755859375
  - Non-zero count: 163,938.0549545288


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 25,555.2
  - Median: 19,126.1
  - Stddev: 31,634.5
  - Non-zero count: 31,762,710.055456758


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 163,938.0549545288


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 18.8
  - Median: 0.0
  - Stddev: 278.5
  - Non-zero count: 304,441.181892395


- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 36,144,140.87005857


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: DLA (mobility) (reported)
  - Mean: 30.3
  - Median: 0.0
  - Stddev: 325.8999938964844
  - Non-zero count: 794,603.9834299088


- dla_m:
  - Type: float
  - Entity: person
  - Description: DLA (mobility)
  - Mean: 29.8
  - Median: 0.0
  - Stddev: 319.1000061035156
  - Non-zero count: 794,603.9834299088


- dla_m_category:
  - Type: Categorical
  - Entity: person
  - Description: DLA (mobility) category


- dla:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 77.0
  - Median: 0.0
  - Stddev: 710.2000122070312
  - Non-zero count: 1,114,483.50055027


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: DLA (self-care) (reported)
  - Mean: 46.4
  - Median: 0.0
  - Stddev: 454.6000061035156
  - Non-zero count: 981,401.0508308411


- dla_sc:
  - Type: float
  - Entity: person
  - Description: DLA (self-care)
  - Mean: 47.1
  - Median: 0.0
  - Stddev: 456.8999938964844
  - Non-zero count: 981,401.0508308411


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
  - Non-zero count: 748,702.0986862183


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility) (reported)
  - Mean: 47.1
  - Median: 0.0
  - Stddev: 386.70001220703125
  - Non-zero count: 1,376,311.2113780975


- pip_m:
  - Type: float
  - Entity: person
  - Description: PIP (mobility)
  - Mean: 46.6
  - Median: 0.0
  - Stddev: 380.70001220703125
  - Non-zero count: 1,376,311.2113780975


- pip_m_category:
  - Type: Categorical
  - Entity: person
  - Description: PIP (mobility) category


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: PIP (self-care) (reported)
  - Mean: 100.3
  - Median: 0.0
  - Stddev: 660.4000244140625
  - Non-zero count: 1,808,884.3287525177


- pip_dl:
  - Type: float
  - Entity: person
  - Description: PIP (daily living)
  - Mean: 102.6
  - Median: 0.0
  - Stddev: 675.0999755859375
  - Non-zero count: 1,808,884.3287525177


- pip_dl_category:
  - Type: Categorical
  - Entity: person
  - Description: PIP (daily living) category


- pip:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 149.2
  - Median: 0.0
  - Stddev: 998.2999877929688
  - Non-zero count: 1,917,229.389678955


- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 109.6
  - Median: 38.3
  - Stddev: 419.1000061035156
  - Non-zero count: 22,987,657.523749888


- baseline_expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected, baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- change_in_expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Change in expected Stamp Duty
  - Mean: 429.9
  - Median: 94.3
  - Stddev: 1,124.5999755859375
  - Non-zero count: 24,160,579.86268419


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 109.6
  - Median: 38.3
  - Stddev: 419.1000061035156
  - Non-zero count: 22,987,657.523749888


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
  - Mean: 429.9
  - Median: 94.3
  - Stddev: 1,124.5999755859375
  - Non-zero count: 24,160,579.86268419


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 24,590,712.849098086


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
  - Mean: 235.8
  - Median: 0.0
  - Stddev: 3,846.0
  - Non-zero count: 548,731.394356072


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
  - Mean: 8,190.0
  - Median: 160.0
  - Stddev: 22,961.599609375
  - Non-zero count: 14,537,718.922358125


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 8,425.8
  - Median: 200.0
  - Stddev: 23,907.5
  - Non-zero count: 14,591,522.270894617


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 7,299.1
  - Median: 0.0
  - Stddev: 22,155.30078125
  - Non-zero count: 12,618,049.461886793


- baseline_child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- baseline_has_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Receives Child Benefit (baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 326.5
  - Median: 0.0
  - Stddev: 696.2000122070312
  - Non-zero count: 7,132,352.404498607


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 270.0
  - Median: 0.0
  - Stddev: 640.0999755859375
  - Non-zero count: 6,113,730.2608162165


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 150.4
  - Median: 0.0
  - Stddev: 507.5
  - Non-zero count: 6,126,531.264963627


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 186.7
  - Median: 0.0
  - Stddev: 365.29998779296875
  - Non-zero count: 13,587,051.760222733


- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 29,008,855.95105079


- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 1,111.3
  - Median: 388.3
  - Stddev: 4,249.2001953125
  - Non-zero count: 22,987,657.523749888


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,111.3
  - Median: 388.3
  - Stddev: 4,249.2001953125
  - Non-zero count: 22,987,657.523749888


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
  - Mean: 7,396.0
  - Median: 2,077.5
  - Stddev: 35,669.0
  - Non-zero count: 25,267,818.776479155


- household_tax:
  - Type: float
  - Entity: household
  - Description: Taxes
  - Mean: 11,806.8
  - Median: 5,711.0
  - Stddev: 40,044.0
  - Non-zero count: 28,467,404.95494479


- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,975.7
  - Median: 25.0
  - Stddev: 25,138.69921875
  - Non-zero count: 33,778,984.52087471


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,975.7
  - Median: 25.0
  - Stddev: 25,138.69921875
  - Non-zero count: 33,778,984.52087471


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- change_in_fuel_duty:
  - Type: float
  - Entity: household
  - Description: Change in fuel duty
  - Mean: 567.2
  - Median: 404.2
  - Stddev: 654.9000244140625
  - Non-zero count: 19,272,700.238146722


- fuel_duty:
  - Type: float
  - Entity: household
  - Description: Fuel duty (cars only)
  - Mean: 567.2
  - Median: 404.2
  - Stddev: 654.9000244140625
  - Non-zero count: 19,272,700.238146722


- NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 7.1
  - Median: 0.0
  - Stddev: 29.200000762939453
  - Non-zero count: 2,997,701.830866337


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 7.1
  - Median: 0.0
  - Stddev: 29.200000762939453
  - Non-zero count: 2,997,701.830866337


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 24,400,148.003022194


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 896.0
  - Median: 0.0
  - Stddev: 1,655.0
  - Non-zero count: 24,420,517.142964244


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,289.3
  - Median: 0.0
  - Stddev: 2,854.5
  - Non-zero count: 25,006,511.983914256


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,289.3
  - Median: 0.0
  - Stddev: 2,854.5
  - Non-zero count: 25,006,511.983914256


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,241.6
  - Median: 0.0
  - Stddev: 4,430.89990234375
  - Non-zero count: 27,696,584.16005552


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 65.0
  - Median: 0.0
  - Stddev: 692.0999755859375
  - Non-zero count: 2,549,543.7053189278


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 896.0
  - Median: 0.0
  - Stddev: 1,655.0
  - Non-zero count: 24,420,517.142964244


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 952.2
  - Median: 0.0
  - Stddev: 1,768.0
  - Non-zero count: 26,622,246.41255462


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 72.1
  - Median: 0.0
  - Stddev: 703.7999877929688
  - Non-zero count: 2,997,701.830866337


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 776.2
  - Median: 0.0
  - Stddev: 29,155.599609375
  - Non-zero count: 353,355.9631690979


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 349.3
  - Median: 0.0
  - Stddev: 13,120.0
  - Non-zero count: 353,355.9631690979


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 4.3
  - Median: 0.0
  - Stddev: 276.3999938964844
  - Non-zero count: 18,277.750274658203


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7,309.1
  - Median: 0.0
  - Stddev: 12,142.099609375
  - Non-zero count: 30,891,080.23272544


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,461.8
  - Median: 0.0
  - Stddev: 2,428.39990234375
  - Non-zero count: 30,891,080.23272544


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 13.7
  - Median: 0.0
  - Stddev: 389.3999938964844
  - Non-zero count: 113,972.9571428299


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 19.9
  - Median: 0.0
  - Stddev: 409.0
  - Non-zero count: 605,345.2122935355


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 369.9
  - Median: 0.0
  - Stddev: 18,766.400390625
  - Non-zero count: 1,154,228.3843764365


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,611.6
  - Median: 0.0
  - Stddev: 15,414.7001953125
  - Non-zero count: 30,891,080.23272544


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 10,065.3
  - Median: 0.0
  - Stddev: 37,099.69921875
  - Non-zero count: 30,891,080.23272544


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 1,980.1
  - Median: 0.0
  - Stddev: 10,582.599609375
  - Non-zero count: 4,096,062.9593215287


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 792.0
  - Median: 0.0
  - Stddev: 4,233.0
  - Non-zero count: 4,096,062.9593215287


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 17.2
  - Median: 0.0
  - Stddev: 718.7999877929688
  - Non-zero count: 55,933.899629592896


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 3,023.5
  - Median: 0.0
  - Stddev: 24,490.0
  - Non-zero count: 31,208,727.077200264


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,993.1
  - Median: 0.0
  - Stddev: 24,412.80078125
  - Non-zero count: 31,208,727.077200264


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 36,144,140.87005857


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.30000001192092896
  - Non-zero count: 5,544,417.5458628535


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 11.6
  - Median: 0.0
  - Stddev: 362.20001220703125
  - Non-zero count: 165,503.51820278168


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,987.7
  - Median: 5,000.0
  - Stddev: 214.1999969482422
  - Non-zero count: 67,174,519.0311718


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 1,115.6
  - Median: 0.0
  - Stddev: 51,176.5
  - Non-zero count: 1,154,228.3843764365


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 11,216.1
  - Median: 0.0
  - Stddev: 63,623.6015625
  - Non-zero count: 31,208,727.077200264


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 35.3
  - Median: 0.0
  - Stddev: 957.0
  - Non-zero count: 165,503.51820278168


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
  - Mean: 19.2
  - Median: 0.0
  - Stddev: 334.3999938964844
  - Non-zero count: 175,309.49304771423


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 5.9
  - Median: 0.0
  - Stddev: 168.6999969482422
  - Non-zero count: 105,672.27379798889


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,703.8
  - Median: 11,048.2
  - Stddev: 64,119.19921875
  - Non-zero count: 47,130,834.13125265


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
  - Mean: 25.1
  - Median: 0.0
  - Stddev: 375.70001220703125
  - Non-zero count: 280,127.93017578125


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
  - Mean: 479.6
  - Median: 0.0
  - Stddev: 1,289.199951171875
  - Non-zero count: 19,344,420.679252625


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,809.7
  - Median: 0.0
  - Stddev: 2,067.10009765625
  - Non-zero count: 33,082,469.85757926


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 39.2
  - Median: 0.0
  - Stddev: 380.70001220703125
  - Non-zero count: 9,316,864.649248093


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 1,166.8
  - Median: 0.0
  - Stddev: 51,290.0
  - Non-zero count: 4,138,236.9688646197


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 12,628.0
  - Median: 0.0
  - Stddev: 22,515.0
  - Non-zero count: 30,286,992.402183324


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 59.5
  - Median: 0.0
  - Stddev: 1,002.9000244140625
  - Non-zero count: 771,787.4630403519


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1,102.0
  - Median: 0.0
  - Stddev: 4,881.5
  - Non-zero count: 9,301,682.557232678


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 488.3
  - Median: 0.0
  - Stddev: 6,364.89990234375
  - Non-zero count: 2,060,066.305748254


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 81.4
  - Median: 0.0
  - Stddev: 1,070.4000244140625
  - Non-zero count: 19,025,031.979306996


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1,504.8
  - Median: 0.0
  - Stddev: 29,242.900390625
  - Non-zero count: 3,961,577.255010605


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,672.9
  - Median: 0.0
  - Stddev: 3,762.5
  - Non-zero count: 13,748,469.413428724


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 19,260.9
  - Median: 11,350.9
  - Stddev: 64,376.0
  - Non-zero count: 47,333,046.1043514


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
  - Mean: 1,166.8
  - Median: 0.0
  - Stddev: 51,290.0
  - Non-zero count: 4,138,236.9688646197


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 13,069.4
  - Median: 0.0
  - Stddev: 23,191.599609375
  - Non-zero count: 30,225,843.990287572


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1,102.0
  - Median: 0.0
  - Stddev: 4,881.5
  - Non-zero count: 9,301,682.557232678


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 522.1
  - Median: 0.0
  - Stddev: 6,451.5
  - Non-zero count: 2,547,360.87280491


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 115.8
  - Median: 0.0
  - Stddev: 1,136.0
  - Non-zero count: 22,247,425.56127006


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 1,552.4
  - Median: 0.0
  - Stddev: 29,289.69921875
  - Non-zero count: 4,175,640.6977385283


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,672.9
  - Median: 0.0
  - Stddev: 3,762.5
  - Non-zero count: 13,748,469.413428724


- total_pension_income:
  - Type: float
  - Entity: person
  - Description: Total pension income
  - Mean: 2,710.9
  - Median: 0.0
  - Stddev: 7,293.5
  - Non-zero count: 14,335,566.632000625


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 159.9
  - Median: 0.0
  - Stddev: 401.5
  - Non-zero count: 8,945,638.722113729


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 62,690,906.34895021


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 198.6
  - Median: 0.0
  - Stddev: 5,374.60009765625
  - Non-zero count: 14,315,381.732912183


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5,067.0
  - Median: 1,521.8
  - Stddev: 5,453.7001953125
  - Non-zero count: 35,709,986.01497379


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,409.1
  - Median: 12,570.0
  - Stddev: 1,426.5999755859375
  - Non-zero count: 66,562,754.78077945


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
  - Non-zero count: 67,239,322.06306267


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
  - Mean: 39,899.1
  - Median: 40,000.0
  - Stddev: 2,150.800048828125
  - Non-zero count: 67,239,322.06306267


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,409.1
  - Median: 12,570.0
  - Stddev: 1,426.5999755859375
  - Non-zero count: 66,562,754.78077945


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: 33.7
  - Median: 0.0
  - Stddev: 206.89999389648438
  - Non-zero count: 2,547,360.87280491


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 962.8
  - Median: 1,000.0
  - Stddev: 151.3000030517578
  - Non-zero count: 66,780,442.63740644


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 67,239,322.06306267


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 47.6
  - Median: 0.0
  - Stddev: 618.4000244140625
  - Non-zero count: 4,175,640.6977385283


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 30.4
  - Median: 0.0
  - Stddev: 221.8000030517578
  - Non-zero count: 1,456,776.7904271185


- baseline_expected_lbtt:
  - Type: float
  - Entity: household
  - Description: LBTT (expected, baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- change_in_expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Change in LBTT (expected)
  - Mean: 50.3
  - Median: 0.0
  - Stddev: 573.0999755859375
  - Non-zero count: 1,254,949.1195148826


- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 50.3
  - Median: 0.0
  - Stddev: 573.0999755859375
  - Non-zero count: 1,254,949.1195148826


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 1,147.0
  - Median: 0.0
  - Stddev: 13,059.599609375
  - Non-zero count: 1,254,949.1195148826


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,575,192.036562979


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
  - Mean: 221.2
  - Median: 0.0
  - Stddev: 3,784.5
  - Non-zero count: 548,731.394356072


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
  - Mean: 12,245.0
  - Median: 300.0
  - Stddev: 33,344.30078125
  - Non-zero count: 14,862,568.132002562


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 12,466.2
  - Median: 300.0
  - Stddev: 34,147.8984375
  - Non-zero count: 14,906,155.090069443


- baseline_expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (baseline, expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- change_in_expected_ltt:
  - Type: float
  - Entity: household
  - Description: Change in LTT (expected)
  - Mean: 19.2
  - Median: 0.0
  - Stddev: 264.3999938964844
  - Non-zero count: 655,934.5569355488


- expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (expected)
  - Mean: 19.2
  - Median: 0.0
  - Stddev: 264.3999938964844
  - Non-zero count: 655,934.5569355488


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 436.4
  - Median: 0.0
  - Stddev: 6,024.10009765625
  - Non-zero count: 655,934.5569355488


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,388,364.2175705433


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
  - Mean: 22.2
  - Median: 0.0
  - Stddev: 1,357.9000244140625
  - Non-zero count: 29,033.703684806824


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
  - Mean: 10,032.4
  - Median: 0.0
  - Stddev: 27,757.80078125
  - Non-zero count: 13,490,246.9395096


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 10,054.5
  - Median: 0.0
  - Stddev: 27,859.599609375
  - Non-zero count: 13,491,020.421443194


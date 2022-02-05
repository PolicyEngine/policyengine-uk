# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2022) 2018-19 Family Resources Survey, with simulation turned on.


- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: -1,503.6
  - Median: -337.5
  - Stddev: 3,134.4
  - Non-zero count: 0.0
  - Aggregate: -42,136,968,846.0

- hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income
  - Mean: -1,503.6
  - Median: -337.5
  - Stddev: 3,134.4
  - Non-zero count: 0.0
  - Aggregate: -42,136,968,846.0

- hbai_excluded_income_change:
  - Type: float
  - Entity: household
  - Description: Change in HBAI-excluded income
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 111.7
  - Median: 16.1
  - Stddev: 248.3
  - Non-zero count: 13,304.0
  - Aggregate: 3,130,000,006.0

- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 111.7
  - Median: 16.1
  - Stddev: 248.3
  - Non-zero count: 13,304.0
  - Aggregate: 3,130,000,006.0

- corporate_sdlt_change_incidence:
  - Type: float
  - Entity: household
  - Description: Corporate Stamp Duty
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- expected_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (expected)
  - Mean: 323.8
  - Median: 66.0
  - Stddev: 854.3
  - Non-zero count: 14,408.0
  - Aggregate: 9,073,434,400.0

- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 15,712.0
  - Aggregate: 24,155,043.0

- sdlt_on_non_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on non-residential property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- sdlt_on_non_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on non-residential property
  - Mean: 55.5
  - Median: 0.0
  - Stddev: 1,303.6
  - Non-zero count: 89.0
  - Aggregate: 1,554,183,443.0

- sdlt_on_rent:
  - Type: float
  - Entity: household
  - Description: SDLT on property rental
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- sdlt_on_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on residential property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- sdlt_on_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: Stamp Duty on residential property
  - Mean: 4,515.3
  - Median: 0.0
  - Stddev: 15,684.8
  - Non-zero count: 8,688.0
  - Aggregate: 126,535,889,889.0

- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 4,570.8
  - Median: 0.0
  - Stddev: 15,975.0
  - Non-zero count: 8,696.0
  - Aggregate: 128,090,073,310.0

- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 3,928.0
  - Median: 0.0
  - Stddev: 14,160.9
  - Non-zero count: 7,104.0
  - Aggregate: 110,076,901,112.0

- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 321.8
  - Median: 0.0
  - Stddev: 732.5
  - Non-zero count: 4,832.0
  - Aggregate: 11,338,610,477.0

- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 260.0
  - Median: 0.0
  - Stddev: 677.9
  - Non-zero count: 4,116.0
  - Aggregate: 9,163,209,014.0

- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 162.4
  - Median: 0.0
  - Stddev: 537.6
  - Non-zero count: 4,408.0
  - Aggregate: 10,451,194,877.0

- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 187.4
  - Median: 0.0
  - Stddev: 389.8
  - Non-zero count: 9,272.0
  - Aggregate: 12,678,010,326.0

- is_imputed_to_take_up_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Is imputed to take up Child Benefit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 20,896.0
  - Aggregate: 32,417,746.0

- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 20,896.0
  - Aggregate: 32,417,746.0

- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 1,132.3
  - Median: 163.1
  - Stddev: 2,516.8
  - Non-zero count: 13,304.0
  - Aggregate: 31,732,499,023.0

- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,132.3
  - Median: 163.1
  - Stddev: 2,516.8
  - Non-zero count: 13,304.0
  - Aggregate: 31,732,499,023.0

- business_rates_change_incidence:
  - Type: float
  - Entity: household
  - Description: Business rates changes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 65.5
  - Median: 0.0
  - Stddev: 678.7
  - Non-zero count: 408.0
  - Aggregate: 2,309,200,234.0

- tax_credits_below_minimum:
  - Type: bool
  - Entity: benunit
  - Description: Tax Credits are below the minimum
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 22,208.0
  - Aggregate: 34,524,031.0

- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Income for Tax Credits
  - Mean: 32,602.3
  - Median: 21,308.5
  - Stddev: 41,565.8
  - Non-zero count: 18,496.0
  - Aggregate: 1,148,898,328,138.0

- is_child_for_ctc:
  - Type: bool
  - Entity: person
  - Description: Child eligible for the Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,272.0
  - Aggregate: 13,626,359.0

- is_ctc_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,053.0
  - Aggregate: 1,521,663.0

- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit
  - Mean: 55.2
  - Median: 0.0
  - Stddev: 608.8
  - Non-zero count: 329.0
  - Aggregate: 1,945,653,910.0

- ctc_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit (before minimum benefit rules)
  - Mean: 68.9
  - Median: 0.0
  - Stddev: 688.2
  - Non-zero count: 413.0
  - Aggregate: 2,429,098,010.0

- ctc_reduction:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit reduction
  - Mean: 155.0
  - Median: 0.0
  - Stddev: 940.9
  - Non-zero count: 808.0
  - Aggregate: 5,463,124,362.0

- maximum_ctc:
  - Type: float
  - Entity: benunit
  - Description: CTC maximum rate
  - Mean: 224.0
  - Median: 0.0
  - Stddev: 1,191.3
  - Non-zero count: 1,053.0
  - Aggregate: 7,892,222,375.0

- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported Child Tax Credit
  - Mean: 156.2
  - Median: 0.0
  - Stddev: 1,165.6
  - Non-zero count: 1,401.0
  - Aggregate: 10,565,512,719.0

- claims_ctc:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 3,748.0
  - Aggregate: 5,767,694.0

- would_claim_ctc:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 18,832.0
  - Aggregate: 29,162,521.0

- ctc_child_element:
  - Type: float
  - Entity: benunit
  - Description: Child element
  - Mean: 1,006.2
  - Median: 0.0
  - Stddev: 2,209.4
  - Non-zero count: 5,244.0
  - Aggregate: 35,456,526,595.0

- is_ctc_child_limit_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Is exempt from the CTC child limit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- meets_ctc_child_limit:
  - Type: bool
  - Entity: person
  - Description: Meets the child limit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.1
  - Non-zero count: 42,784.0
  - Aggregate: 66,862,099.0

- ctc_family_element:
  - Type: float
  - Entity: benunit
  - Description: Family element
  - Mean: 17.7
  - Median: 0.0
  - Stddev: 101.3
  - Non-zero count: 815.0
  - Aggregate: 624,626,680.0

- ctc_disability_element:
  - Type: float
  - Entity: benunit
  - Description: CTC disability element
  - Mean: 2.8
  - Median: 0.0
  - Stddev: 122.1
  - Non-zero count: 19.0
  - Aggregate: 98,297,545.0

- ctc_severe_disability_element:
  - Type: float
  - Entity: person
  - Description: CTC severe disability element
  - Mean: 0.8
  - Median: 0.0
  - Stddev: 73.3
  - Non-zero count: 10.0
  - Aggregate: 55,311,246.0

- ctc_standard_disability_element:
  - Type: float
  - Entity: person
  - Description: CTC standard disability element
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 71.9
  - Non-zero count: 19.0
  - Aggregate: 85,311,415.0

- in_wtc_qualifying_remunerative_work:
  - Type: bool
  - Entity: person
  - Description: In qualifying remunerative work
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 15,408.0
  - Aggregate: 25,827,394.0

- is_work_disadvantaged:
  - Type: bool
  - Entity: person
  - Description: Has a disadvantage when looking for work
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,996.0
  - Aggregate: 3,864,431.0

- is_wtc_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for WTC
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,112.0
  - Aggregate: 3,432,425.0

- maximum_wtc:
  - Type: float
  - Entity: benunit
  - Description: WTC maximum rate
  - Mean: 451.4
  - Median: 0.0
  - Stddev: 1,484.3
  - Non-zero count: 2,112.0
  - Aggregate: 15,906,848,401.0

- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 10.3
  - Median: 0.0
  - Stddev: 211.3
  - Non-zero count: 127.0
  - Aggregate: 363,546,324.0

- wtc_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit (before minimum benefit rules)
  - Mean: 17.1
  - Median: 0.0
  - Stddev: 272.7
  - Non-zero count: 197.0
  - Aggregate: 600,865,714.0

- wtc_reduction:
  - Type: float
  - Entity: benunit
  - Description: WTC reduction
  - Mean: 434.3
  - Median: 0.0
  - Stddev: 1,435.8
  - Non-zero count: 2,076.0
  - Aggregate: 15,305,982,683.0

- claims_wtc:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,954.0
  - Aggregate: 4,535,046.0

- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported Working Tax Credit
  - Mean: 36.8
  - Median: 0.0
  - Stddev: 440.2
  - Non-zero count: 736.0
  - Aggregate: 2,487,992,535.0

- would_claim_wtc:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,954.0
  - Aggregate: 4,535,046.0

- wtc_worker_element:
  - Type: float
  - Entity: benunit
  - Description: WTC worker element
  - Mean: 448.9
  - Median: 830.0
  - Stddev: 415.0
  - Non-zero count: 11,248.0
  - Aggregate: 15,819,306,980.0

- wtc_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 122.8
  - Median: 0.0
  - Stddev: 844.7
  - Non-zero count: 1,011.0
  - Aggregate: 4,328,067,250.0

- wtc_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: WTC lone parent element
  - Mean: 143.0
  - Median: 0.0
  - Stddev: 549.1
  - Non-zero count: 1,750.0
  - Aggregate: 5,041,017,760.0

- wtc_basic_element:
  - Type: float
  - Entity: benunit
  - Description: WTC basic element
  - Mean: 2,005.0
  - Median: 2,005.0
  - Stddev: 0.6
  - Non-zero count: 22,736.0
  - Aggregate: 70,655,682,710.0

- wtc_severe_disability_element:
  - Type: float
  - Entity: benunit
  - Description: WTC severe disability element
  - Mean: 104.7
  - Median: 0.0
  - Stddev: 638.6
  - Non-zero count: 920.0
  - Aggregate: 3,689,686,080.0

- wtc_couple_element:
  - Type: float
  - Entity: benunit
  - Description: WTC couple element
  - Mean: 950.0
  - Median: 0.0
  - Stddev: 1,028.2
  - Non-zero count: 10,696.0
  - Aggregate: 33,476,884,900.0

- wtc_disability_element:
  - Type: float
  - Entity: benunit
  - Description: WTC disability element
  - Mean: 326.1
  - Median: 0.0
  - Stddev: 1,067.2
  - Non-zero count: 2,814.0
  - Aggregate: 11,490,112,440.0

- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 154.7
  - Median: 0.0
  - Stddev: 424.1
  - Non-zero count: 6,032.0
  - Aggregate: 10,466,649,839.0

- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 40,352.0
  - Aggregate: 62,664,194.0

- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 52.6
  - Median: 0.0
  - Stddev: 5,880.0
  - Non-zero count: 9,088.0
  - Aggregate: 3,557,286,168.0

- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5,119.4
  - Median: 1,341.5
  - Stddev: 5,680.5
  - Non-zero count: 23,584.0
  - Aggregate: 346,278,448,078.0

- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 33.2
  - Median: 0.0
  - Stddev: 231.7
  - Non-zero count: 1,003.0
  - Aggregate: 2,243,615,868.0

- corporate_tax_incidence:
  - Type: float
  - Entity: household
  - Description: Corporate tax incidence
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- corporate_wealth:
  - Type: float
  - Entity: household
  - Description: Corporate wealth
  - Mean: 169,869.6
  - Median: 24,466.3
  - Stddev: 377,553.2
  - Non-zero count: 13,304.0
  - Aggregate: 4,760,394,009,163.0

- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 13,304.0
  - Aggregate: 1.0

- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 185,889.2
  - Median: 140,000.0
  - Stddev: 235,661.8
  - Non-zero count: 12,168.0
  - Aggregate: 5,209,324,617,504.0

- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 2,292.4
  - Median: 0.0
  - Stddev: 36,947.5
  - Non-zero count: 174.0
  - Aggregate: 64,243,094,584.0

- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 9,361.0
  - Median: 0.0
  - Stddev: 69,043.3
  - Non-zero count: 938.0
  - Aggregate: 262,329,717,623.0

- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 216,117.5
  - Median: 147,240.3
  - Stddev: 307,987.2
  - Non-zero count: 12,432.0
  - Aggregate: 6,056,436,671,314.0

- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 195,250.2
  - Median: 140,000.0
  - Stddev: 258,538.2
  - Non-zero count: 12,240.0
  - Aggregate: 5,471,654,334,584.0

- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 62,725.9
  - Median: 9,034.4
  - Stddev: 139,416.9
  - Non-zero count: 13,304.0
  - Aggregate: 1,757,818,048,408.0

- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 153,767.0
  - Median: 104,761.1
  - Stddev: 219,135.7
  - Non-zero count: 12,432.0
  - Aggregate: 4,309,138,025,641.0

- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 216,492.9
  - Median: 139,059.7
  - Stddev: 298,218.0
  - Non-zero count: 15,576.0
  - Aggregate: 6,066,956,073,310.0

- owned_land:
  - Type: float
  - Entity: household
  - Description: Owned land
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 35.5
  - Median: 0.0
  - Stddev: 542.1
  - Non-zero count: 1,265.0
  - Aggregate: 994,405,750.0

- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 657.2
  - Median: 0.0
  - Stddev: 10,040.4
  - Non-zero count: 1,265.0
  - Aggregate: 18,417,146,781.0

- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,728.0
  - Aggregate: 2,505,382.0

- lbtt_on_non_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LBTT on non-residential property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- lbtt_on_non_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on non-residential property transactions
  - Mean: 51.4
  - Median: 0.0
  - Stddev: 1,262.0
  - Non-zero count: 89.0
  - Aggregate: 1,441,357,808.0

- lbtt_on_rent:
  - Type: float
  - Entity: household
  - Description: LBTT on property rental
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- lbtt_on_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LBTT on residential property rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- lbtt_on_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on residential property
  - Mean: 6,583.1
  - Median: 0.0
  - Stddev: 21,339.9
  - Non-zero count: 8,944.0
  - Aggregate: 184,483,744,879.0

- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 6,634.5
  - Median: 0.0
  - Stddev: 21,604.6
  - Non-zero count: 8,952.0
  - Aggregate: 185,925,102,669.0

- carbon_consumption:
  - Type: float
  - Entity: household
  - Description: Carbon consumption
  - Mean: 19.4
  - Median: 14.4
  - Stddev: 18.3
  - Non-zero count: 19,216.0
  - Aggregate: 543,852,023.0

- alcohol_and_tobacco_consumption:
  - Type: float
  - Entity: household
  - Description: Alcohol and tobacco
  - Mean: 741.1
  - Median: 233.7
  - Stddev: 1,284.3
  - Non-zero count: 11,640.0
  - Aggregate: 20,768,633,389.0

- clothing_and_footwear_consumption:
  - Type: float
  - Entity: household
  - Description: Clothing and footwear
  - Mean: 1,471.5
  - Median: 467.7
  - Stddev: 2,632.3
  - Non-zero count: 12,696.0
  - Aggregate: 41,237,179,108.0

- communication_consumption:
  - Type: float
  - Entity: household
  - Description: Communication
  - Mean: 737.3
  - Median: 418.4
  - Stddev: 1,704.3
  - Non-zero count: 15,592.0
  - Aggregate: 20,661,655,321.0

- education_consumption:
  - Type: float
  - Entity: household
  - Description: Education
  - Mean: 593.5
  - Median: 0.0
  - Stddev: 3,994.7
  - Non-zero count: 1,689.0
  - Aggregate: 16,632,033,199.0

- food_and_non_alcoholic_beverages_consumption:
  - Type: float
  - Entity: household
  - Description: Food and alcoholic beverages
  - Mean: 3,447.3
  - Median: 2,959.0
  - Stddev: 2,195.1
  - Non-zero count: 19,072.0
  - Aggregate: 96,606,272,418.0

- health_consumption:
  - Type: float
  - Entity: household
  - Description: Health
  - Mean: 532.1
  - Median: 53.4
  - Stddev: 1,819.0
  - Non-zero count: 11,696.0
  - Aggregate: 14,911,423,789.0

- household_furnishings_consumption:
  - Type: float
  - Entity: household
  - Description: Household furnishings
  - Mean: 2,461.9
  - Median: 739.9
  - Stddev: 5,062.0
  - Non-zero count: 18,240.0
  - Aggregate: 68,991,767,024.0

- housing_water_and_electricity_consumption:
  - Type: float
  - Entity: household
  - Description: Housing, water and electricity
  - Mean: 4,975.3
  - Median: 2,530.5
  - Stddev: 6,289.9
  - Non-zero count: 19,168.0
  - Aggregate: 139,426,867,830.0

- miscellaneous_consumption:
  - Type: float
  - Entity: household
  - Description: Miscellaneous
  - Mean: 3,696.4
  - Median: 1,739.3
  - Stddev: 6,987.0
  - Non-zero count: 18,928.0
  - Aggregate: 103,586,943,548.0

- recreation_consumption:
  - Type: float
  - Entity: household
  - Description: Recreation
  - Mean: 5,350.1
  - Median: 2,166.6
  - Stddev: 8,970.1
  - Non-zero count: 19,024.0
  - Aggregate: 149,930,069,261.0

- restaurants_and_hotels_consumption:
  - Type: float
  - Entity: household
  - Description: Restaurants and hotels
  - Mean: 3,530.7
  - Median: 2,019.3
  - Stddev: 4,496.1
  - Non-zero count: 16,944.0
  - Aggregate: 98,945,011,376.0

- transport_consumption:
  - Type: float
  - Entity: household
  - Description: Transport
  - Mean: 6,275.3
  - Median: 3,130.4
  - Stddev: 10,837.9
  - Non-zero count: 17,088.0
  - Aggregate: 175,858,658,841.0

- additional_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (additional)
  - Mean: 9,361.0
  - Median: 0.0
  - Stddev: 69,043.3
  - Non-zero count: 938.0
  - Aggregate: 262,329,717,623.0

- cumulative_non_residential_rent:
  - Type: float
  - Entity: household
  - Description: Cumulative non-residential rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- cumulative_residential_rent:
  - Type: float
  - Entity: household
  - Description: Cumulative residential rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- main_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (main)
  - Mean: 185,889.2
  - Median: 140,000.0
  - Stddev: 235,661.8
  - Non-zero count: 12,168.0
  - Aggregate: 5,209,324,617,504.0

- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 3,632.0
  - Aggregate: 5,518,017.0

- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 2,292.4
  - Median: 0.0
  - Stddev: 36,947.5
  - Non-zero count: 174.0
  - Aggregate: 64,243,094,584.0

- non_residential_rent:
  - Type: float
  - Entity: household
  - Description: Non-residential rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- property_purchased:
  - Type: bool
  - Entity: household
  - Description: All property bought this year
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 19,216.0
  - Aggregate: 28,023,811.0

- property_sale_rate:
  - Type: float
  - Entity: state
  - Description: Residential property sale rate
  - Mean: 0.1
  - Median: 0.1
  - Stddev: 0.0
  - Non-zero count: 1.0
  - Aggregate: 0.0

- rent:
  - Type: float
  - Entity: household
  - Description: Rent
  - Mean: 2,914.2
  - Median: -52.0
  - Stddev: 4,221.1
  - Non-zero count: 6,664.0
  - Aggregate: 72,504,293,680.0

- base_net_income:
  - Type: float
  - Entity: person
  - Description: Existing net income for the person to use as a base in microsimulation
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- capital_income:
  - Type: float
  - Entity: person
  - Description: Income from savings or dividends
  - Mean: 251.4
  - Median: 0.0
  - Stddev: 2,203.3
  - Non-zero count: 15,384.0
  - Aggregate: 17,005,015,183.0

- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 17,058.1
  - Median: 7,435.8
  - Stddev: 26,786.6
  - Non-zero count: 25,008.0
  - Aggregate: 1,153,821,807,333.0

- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 33,848.9
  - Median: 29,168.2
  - Stddev: 23,234.7
  - Non-zero count: 18,912.0
  - Aggregate: 948,574,075,837.0

- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 30,258.7
  - Median: 26,167.2
  - Stddev: 23,620.2
  - Non-zero count: 18,448.0
  - Aggregate: 847,964,618,382.0

- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 32,362.9
  - Median: 27,734.0
  - Stddev: 22,253.9
  - Non-zero count: 18,848.0
  - Aggregate: 906,932,581,476.0

- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 20,135.5
  - Median: 13,935.5
  - Stddev: 26,942.5
  - Non-zero count: 31,776.0
  - Aggregate: 1,361,974,717,883.0

- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 36,685.5
  - Median: 29,695.0
  - Stddev: 28,222.7
  - Non-zero count: 18,912.0
  - Aggregate: 1,028,068,325,476.0

- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 32,400.8
  - Median: 25,873.5
  - Stddev: 27,711.8
  - Non-zero count: 18,448.0
  - Aggregate: 907,992,848,187.0

- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 843.2
  - Median: 0.0
  - Stddev: 1,034.4
  - Non-zero count: 18,928.0
  - Aggregate: 60,060,159,285.0

- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 47,139.3
  - Median: 35,095.8
  - Stddev: 43,283.4
  - Non-zero count: 19,008.0
  - Aggregate: 1,321,021,915,654.0

- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 40,118.2
  - Median: 28,533.8
  - Stddev: 45,499.4
  - Non-zero count: 16,032.0
  - Aggregate: 1,124,264,927,871.0

- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 35,181.9
  - Median: 28,180.7
  - Stddev: 27,253.1
  - Non-zero count: 18,848.0
  - Aggregate: 985,931,356,472.0

- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 18,928.0
  - Aggregate: 32,458,741.0

- is_apprentice:
  - Type: bool
  - Entity: person
  - Description: In an apprenticeship programme
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- lump_sum_income:
  - Type: float
  - Entity: person
  - Description: Lump sum income
  - Mean: 76.9
  - Median: -1.0
  - Stddev: 1,944.6
  - Non-zero count: 146.0
  - Aggregate: 5,231,686,925.0

- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 41.9
  - Median: 0.0
  - Stddev: 512.9
  - Non-zero count: 566.0
  - Aggregate: 2,404,718,583.0

- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 17,137.1
  - Median: 7,694.2
  - Stddev: 27,239.2
  - Non-zero count: 25,968.0
  - Aggregate: 1,159,166,016,221.0

- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.9
  - Median: 8.9
  - Stddev: 1.8
  - Non-zero count: 43,328.0
  - Aggregate: 532,475,412.0

- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: -142.6
  - Median: -208.0
  - Stddev: 836.9
  - Non-zero count: 486.0
  - Aggregate: -9,643,708,981.0

- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 16,303.0
  - Median: 13,607.8
  - Stddev: 17,988.9
  - Non-zero count: 31,776.0
  - Aggregate: 1,102,747,192,856.0

- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: -126.4
  - Median: -312.0
  - Stddev: 1,242.4
  - Non-zero count: 578.0
  - Aggregate: -8,551,733,164.0

- sublet_income:
  - Type: float
  - Entity: person
  - Description: Income received from sublet agreements
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- weekly_hours:
  - Type: float
  - Entity: person
  - Description: Weekly hours
  - Mean: 16.2
  - Median: 0.0
  - Stddev: 19.9
  - Non-zero count: 18,928.0
  - Aggregate: 1,155,003,063.0

- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2,199.7
  - Median: 0.0
  - Stddev: 3,914.8
  - Non-zero count: 7,040.0
  - Aggregate: 77,517,285,259.0

- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 112.1
  - Median: 0.0
  - Stddev: 881.9
  - Non-zero count: 1,675.0
  - Aggregate: 7,579,445,717.0

- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,482.9
  - Median: 1,445.1
  - Stddev: 765.6
  - Non-zero count: 17,024.0
  - Aggregate: 41,556,591,585.0

- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,368.2
  - Median: 1,404.1
  - Stddev: 872.3
  - Non-zero count: 16,040.0
  - Aggregate: 38,341,479,893.0

- employer_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Employer pension contributions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- family_rent:
  - Type: float
  - Entity: benunit
  - Description: Gross rent for the family
  - Mean: 2,057.5
  - Median: -52.0
  - Stddev: 3,968.8
  - Non-zero count: 6,660.0
  - Aggregate: 72,504,293,680.0

- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 4,284.8
  - Median: 3,083.4
  - Stddev: 4,434.6
  - Non-zero count: 19,072.0
  - Aggregate: 120,075,478,058.0

- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 50.2
  - Median: 0.0
  - Stddev: 339.3
  - Non-zero count: 1,810.0
  - Aggregate: 1,857,105,226.0

- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 35.9
  - Median: 0.0
  - Stddev: 621.6
  - Non-zero count: 437.0
  - Aggregate: 2,845,512,473.0

- mortgage:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- mortgage_capital_repayment:
  - Type: float
  - Entity: household
  - Description: Mortgage payments
  - Mean: 2,373.5
  - Median: 0.0
  - Stddev: 5,618.8
  - Non-zero count: 4,908.0
  - Aggregate: 63,777,264,151.0

- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 870.5
  - Median: -52.0
  - Stddev: 2,093.6
  - Non-zero count: 4,900.0
  - Aggregate: 24,618,486,760.0

- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 406.8
  - Median: 0.0
  - Stddev: 1,300.1
  - Non-zero count: 11,040.0
  - Aggregate: 31,901,133,699.0

- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,105.5
  - Median: 0.0
  - Stddev: 3,035.4
  - Non-zero count: 6,660.0
  - Aggregate: 74,773,694,297.0

- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 30.4
  - Median: 0.0
  - Stddev: 172.6
  - Non-zero count: 1,333.0
  - Aggregate: 1,964,336,456.0

- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 388.6
  - Median: 358.8
  - Stddev: 252.8
  - Non-zero count: 16,848.0
  - Aggregate: 10,548,626,784.0

- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 17.0
  - Non-zero count: 1,675.0
  - Aggregate: 145,758,571.0

- weekly_rent:
  - Type: float
  - Entity: household
  - Description: Weekly average rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- benunit_tax:
  - Type: float
  - Entity: benunit
  - Description: Benefit unit tax paid
  - Mean: 7,133.9
  - Median: 2,592.1
  - Stddev: 14,555.4
  - Non-zero count: 15,656.0
  - Aggregate: 251,396,999,490.0

- household_tax:
  - Type: float
  - Entity: household
  - Description: Taxes
  - Mean: 11,957.4
  - Median: 6,954.9
  - Stddev: 17,254.0
  - Non-zero count: 18,768.0
  - Aggregate: 335,090,559,693.0

- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,832.4
  - Median: 69.1
  - Stddev: 9,757.6
  - Non-zero count: 21,008.0
  - Aggregate: 259,227,525,252.0

- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,832.4
  - Median: 69.1
  - Stddev: 9,757.6
  - Non-zero count: 21,008.0
  - Aggregate: 259,227,525,252.0

- tax_reported:
  - Type: float
  - Entity: person
  - Description: Reported tax paid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 8.2
  - Median: 0.0
  - Stddev: 34.0
  - Non-zero count: 2,086.0
  - Aggregate: 552,781,948.0

- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 8.2
  - Median: 0.0
  - Stddev: 34.0
  - Non-zero count: 2,086.0
  - Aggregate: 552,781,948.0

- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 17,184.0
  - Aggregate: 23,802,149.0

- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 957.8
  - Median: 0.0
  - Stddev: 1,596.7
  - Non-zero count: 14,296.0
  - Aggregate: 64,785,630,467.0

- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,390.9
  - Median: 0.0
  - Stddev: 3,003.2
  - Non-zero count: 14,568.0
  - Aggregate: 94,083,597,130.0

- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,390.9
  - Median: 0.0
  - Stddev: 3,003.2
  - Non-zero count: 14,568.0
  - Aggregate: 94,083,597,130.0

- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,428.4
  - Median: 0.0
  - Stddev: 4,479.9
  - Non-zero count: 16,448.0
  - Aggregate: 164,259,561,220.0

- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 82.5
  - Median: 0.0
  - Stddev: 498.9
  - Non-zero count: 1,870.0
  - Aggregate: 5,577,112,206.0

- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 957.8
  - Median: 0.0
  - Stddev: 1,596.7
  - Non-zero count: 14,296.0
  - Aggregate: 64,785,630,467.0

- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 1,037.5
  - Median: 0.0
  - Stddev: 1,635.6
  - Non-zero count: 15,952.0
  - Aggregate: 70,175,963,712.0

- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 90.6
  - Median: 0.0
  - Stddev: 522.2
  - Non-zero count: 2,086.0
  - Aggregate: 6,129,894,217.0

- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 498.9
  - Median: 0.0
  - Stddev: 8,805.9
  - Non-zero count: 206.0
  - Aggregate: 33,744,222,980.0

- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 224.5
  - Median: 0.0
  - Stddev: 3,963.0
  - Non-zero count: 206.0
  - Aggregate: 15,184,900,026.0

- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 23.9
  - Non-zero count: 4.0
  - Aggregate: 16,135,844.0

- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 8,039.7
  - Median: 0.0
  - Stddev: 11,729.1
  - Non-zero count: 19,360.0
  - Aggregate: 543,807,539,459.0

- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,607.9
  - Median: 0.0
  - Stddev: 2,346.2
  - Non-zero count: 19,360.0
  - Aggregate: 108,761,509,154.0

- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 10.3
  - Median: 0.0
  - Stddev: 413.8
  - Non-zero count: 72.0
  - Aggregate: 698,048,515.0

- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 17.7
  - Median: 0.0
  - Stddev: 430.0
  - Non-zero count: 1,063.0
  - Aggregate: 1,199,636,026.0

- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 20.8
  - Median: 0.0
  - Stddev: 480.2
  - Non-zero count: 558.0
  - Aggregate: 1,407,437,591.0

- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,737.8
  - Median: 0.0
  - Stddev: 8,418.2
  - Non-zero count: 19,360.0
  - Aggregate: 185,189,747,031.0

- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 10,778.5
  - Median: 0.0
  - Stddev: 24,107.8
  - Non-zero count: 19,360.0
  - Aggregate: 729,064,405,368.0

- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 2,240.0
  - Median: 0.0
  - Stddev: 11,363.6
  - Non-zero count: 2,756.0
  - Aggregate: 151,512,642,929.0

- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 896.0
  - Median: 0.0
  - Stddev: 4,545.5
  - Non-zero count: 2,756.0
  - Aggregate: 60,605,057,888.0

- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 2.4
  - Median: 0.0
  - Stddev: 220.9
  - Non-zero count: 16.0
  - Aggregate: 159,725,491.0

- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2,794.9
  - Median: 0.0
  - Stddev: 8,601.9
  - Non-zero count: 19,520.0
  - Aggregate: 189,051,561,586.0

- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,761.8
  - Median: 0.0
  - Stddev: 8,500.1
  - Non-zero count: 19,520.0
  - Aggregate: 186,807,945,587.0

- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 22,736.0
  - Aggregate: 36,327,238.0

- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,580.0
  - Aggregate: 5,483,000.0

- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 3.1
  - Median: 0.0
  - Stddev: 135.5
  - Non-zero count: 86.0
  - Aggregate: 210,761,030.0

- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,987.4
  - Median: 5,000.0
  - Stddev: 197.8
  - Non-zero count: 43,264.0
  - Aggregate: 337,349,976,345.0

- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 109.9
  - Median: 0.0
  - Stddev: 1,866.8
  - Non-zero count: 558.0
  - Aggregate: 7,432,983,150.0

- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 10,901.3
  - Median: 0.0
  - Stddev: 24,360.1
  - Non-zero count: 19,520.0
  - Aggregate: 737,371,298,271.0

- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 12.9
  - Median: 0.0
  - Stddev: 515.2
  - Non-zero count: 86.0
  - Aggregate: 873,909,850.0

- ISA_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount received in interest from Individual Savings Accounts
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- SMP:
  - Type: float
  - Entity: person
  - Description: Statutory Maternity Pay
  - Mean: 16.4
  - Median: 0.0
  - Stddev: 378.6
  - Non-zero count: 107.0
  - Aggregate: 1,247,822,669.0

- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 7.2
  - Median: 0.0
  - Stddev: 170.4
  - Non-zero count: 73.0
  - Aggregate: 428,112,107.0

- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,345.3
  - Median: 11,228.5
  - Stddev: 26,357.8
  - Non-zero count: 29,152.0
  - Aggregate: 1,240,890,091,974.0

- capital_allowances:
  - Type: float
  - Entity: person
  - Description: Full relief from capital expenditure allowances
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- deficiency_relief:
  - Type: float
  - Entity: person
  - Description: Deficiency relief
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- employment_benefits:
  - Type: float
  - Entity: person
  - Description: Employment benefits
  - Mean: 23.6
  - Median: 0.0
  - Stddev: 416.9
  - Non-zero count: 179.0
  - Aggregate: 1,675,934,776.0

- employment_deductions:
  - Type: float
  - Entity: person
  - Description: Deductions from employment income
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- employment_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of expenses necessarily incurred and reimbursed by employment
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- loss_relief:
  - Type: float
  - Entity: person
  - Description: Tax relief from trading losses
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- pension_contributions:
  - Type: float
  - Entity: person
  - Description: Amount contributed to registered pension schemes paid by the individual (not the employer)
  - Mean: 437.2
  - Median: 0.0
  - Stddev: 1,319.6
  - Non-zero count: 11,856.0
  - Aggregate: 33,865,470,155.0

- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,743.0
  - Median: 0.0
  - Stddev: 2,069.0
  - Non-zero count: 18,464.0
  - Aggregate: 117,900,440,478.0

- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 51.9
  - Median: 0.0
  - Stddev: 380.0
  - Non-zero count: 6,180.0
  - Aggregate: 2,830,015,685.0

- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 147.4
  - Median: 0.0
  - Stddev: 1,997.6
  - Non-zero count: 2,468.0
  - Aggregate: 9,967,441,495.0

- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 13,138.6
  - Median: 0.0
  - Stddev: 23,541.2
  - Non-zero count: 19,440.0
  - Aggregate: 888,702,946,113.0

- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: -142.6
  - Median: -208.0
  - Stddev: 836.9
  - Non-zero count: 486.0
  - Aggregate: -9,643,708,981.0

- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1,716.7
  - Median: 0.0
  - Stddev: 7,077.4
  - Non-zero count: 7,528.0
  - Aggregate: 116,115,975,920.0

- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 185.4
  - Median: 0.0
  - Stddev: 2,096.7
  - Non-zero count: 1,046.0
  - Aggregate: 12,540,855,990.0

- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 62.2
  - Median: 0.0
  - Stddev: 608.0
  - Non-zero count: 14,840.0
  - Aggregate: 4,207,557,988.0

- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1,686.0
  - Median: 0.0
  - Stddev: 12,072.3
  - Non-zero count: 2,560.0
  - Aggregate: 114,043,290,466.0

- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,507.7
  - Median: 0.0
  - Stddev: 3,616.2
  - Non-zero count: 9,784.0
  - Aggregate: 101,981,823,434.0

- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,777.8
  - Median: 11,304.8
  - Stddev: 27,118.7
  - Non-zero count: 29,152.0
  - Aggregate: 1,270,140,365,457.0

- trading_loss:
  - Type: float
  - Entity: person
  - Description: Loss from trading in the current year.
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- dividend_income:
  - Type: float
  - Entity: person
  - Description: Income from dividends
  - Mean: 147.4
  - Median: 0.0
  - Stddev: 1,997.6
  - Non-zero count: 2,468.0
  - Aggregate: 9,967,441,495.0

- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 13,600.5
  - Median: 0.0
  - Stddev: 24,338.6
  - Non-zero count: 16,112.0
  - Aggregate: 919,943,047,414.0

- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1,716.7
  - Median: 0.0
  - Stddev: 7,077.4
  - Non-zero count: 7,528.0
  - Aggregate: 116,115,975,920.0

- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 103.1
  - Median: -111.0
  - Stddev: 2,196.3
  - Non-zero count: 1,301.0
  - Aggregate: 6,975,431,737.0

- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 104.0
  - Median: 0.0
  - Stddev: 778.4
  - Non-zero count: 14,840.0
  - Aggregate: 7,037,573,673.0

- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 1,741.0
  - Median: 0.0
  - Stddev: 12,208.3
  - Non-zero count: 2,636.0
  - Aggregate: 117,762,784,102.0

- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,507.7
  - Median: 0.0
  - Stddev: 3,616.2
  - Non-zero count: 9,784.0
  - Aggregate: 101,981,823,434.0

- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,425.4
  - Median: 12,570.0
  - Stddev: 1,198.9
  - Non-zero count: 42,976.0
  - Aggregate: 840,459,962,864.0

- blind_persons_allowance:
  - Type: float
  - Entity: person
  - Description: Blind Person's Allowance for the year (not simulated)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- charitable_investment_gifts:
  - Type: float
  - Entity: person
  - Description: Gifts of qualifying investment or property to charities
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- covenanted_payments:
  - Type: float
  - Entity: person
  - Description: Covenanted payments to charities
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- dividend_allowance:
  - Type: float
  - Entity: person
  - Description: Dividend allowance for the person
  - Mean: 2,000.0
  - Median: 2,000.0
  - Stddev: 0.0
  - Non-zero count: 43,328.0
  - Aggregate: 135,281,231,995.0

- gift_aid:
  - Type: float
  - Entity: person
  - Description: Expenditure under Gift Aid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- married_couples_allowance:
  - Type: float
  - Entity: person
  - Description: Married Couples' allowance for the year
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- married_couples_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction from Married Couples' allowance for the year
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- other_deductions:
  - Type: float
  - Entity: person
  - Description: All other tax deductions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- pension_annual_allowance:
  - Type: float
  - Entity: person
  - Description: Annual Allowance for pension contributions
  - Mean: 39,934.9
  - Median: 40,000.0
  - Stddev: 1,323.6
  - Non-zero count: 43,328.0
  - Aggregate: 2,701,219,370,411.0

- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,425.4
  - Median: 12,570.0
  - Stddev: 1,198.9
  - Non-zero count: 42,976.0
  - Aggregate: 840,459,962,864.0

- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 43,328.0
  - Aggregate: 67,640,615,998.0

- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: -82.3
  - Median: -111.0
  - Stddev: 181.0
  - Non-zero count: 1,301.0
  - Aggregate: -5,565,424,253.0

- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 943.2
  - Median: 1,000.0
  - Stddev: 208.5
  - Non-zero count: 41,952.0
  - Aggregate: 63,797,426,767.0

- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 43,328.0
  - Aggregate: 67,640,615,998.0

- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 55.0
  - Median: 0.0
  - Stddev: 630.4
  - Non-zero count: 2,636.0
  - Aggregate: 3,719,493,636.0

- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 2,865.4
  - Median: 0.0
  - Stddev: 5,385.6
  - Non-zero count: 17,472.0
  - Aggregate: 193,816,175,329.0

- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 189.0
  - Median: 0.0
  - Stddev: 3,096.4
  - Non-zero count: 6,880.0
  - Aggregate: 12,785,842,103.0

- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 364.2
  - Median: 0.0
  - Stddev: 1,605.6
  - Non-zero count: 2,396.0
  - Aggregate: 12,836,063,550.0

- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2,676.4
  - Median: 0.0
  - Stddev: 5,272.2
  - Non-zero count: 16,152.0
  - Aggregate: 181,030,333,170.0

- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 31.8
  - Median: 35.0
  - Stddev: 31.4
  - Non-zero count: 13,448.0
  - Aggregate: 1,120,391,913.0

- claims_all_entitled_benefits:
  - Type: bool
  - Entity: benunit
  - Description: Claims all eligible benefits
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- claims_legacy_benefits:
  - Type: bool
  - Entity: benunit
  - Description: Claims legacy benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,536.0
  - Aggregate: 6,977,333.0

- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 756.1
  - Median: 0.0
  - Stddev: 2,976.5
  - Non-zero count: 8,320.0
  - Aggregate: 51,142,710,502.0

- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 1,367.8
  - Median: 0.0
  - Stddev: 3,105.0
  - Non-zero count: 7,592.0
  - Aggregate: 59,271,262,335.0

- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 6,779.0
  - Median: 2,022.4
  - Stddev: 8,344.8
  - Non-zero count: 13,616.0
  - Aggregate: 189,974,104,896.0

- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Is qualifying young person
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 6,940.0
  - Aggregate: 10,034,078.0

- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,272.0
  - Aggregate: 13,626,359.0

- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 11,136.0
  - Aggregate: 17,048,984.0

- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,750.0
  - Aggregate: 2,447,096.0

- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 11,600.0
  - Aggregate: 18,190,758.0

- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 10,288.0
  - Aggregate: 16,541,731.0

- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -189.0
  - Median: 0.0
  - Stddev: 3,096.4
  - Non-zero count: 5,236.0
  - Aggregate: -12,785,842,103.0

- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,109.3
  - Median: 0.0
  - Stddev: 4,343.3
  - Non-zero count: 12,168.0
  - Aggregate: 142,673,464,855.0

- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1,800.1
  - Median: 0.0
  - Stddev: 4,088.5
  - Non-zero count: 11,160.0
  - Aggregate: 121,759,070,851.0

- benunit_has_carer:
  - Type: bool
  - Entity: benunit
  - Description: Benefit unit has a carer
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 493.0
  - Aggregate: 657,949.0

- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 36.4
  - Median: 0.0
  - Stddev: 284.0
  - Non-zero count: 493.0
  - Aggregate: 1,283,000,550.0

- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 499.0
  - Aggregate: 683,118.0

- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 493.0
  - Aggregate: 662,945.0

- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 165.3
  - Median: 0.0
  - Stddev: 637.5
  - Non-zero count: 2,126.0
  - Aggregate: 5,825,883,414.0

- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 23.1
  - Non-zero count: 9.0
  - Aggregate: 10,128,940.0

- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,260.0
  - Aggregate: 2,930,352.0

- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 9.0
  - Aggregate: 8,817.0

- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 936.0
  - Aggregate: 1,187,892.0

- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,126.0
  - Aggregate: 2,794,162.0

- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 19.0
  - Aggregate: 24,111.0

- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 9.0
  - Aggregate: 8,557.0

- num_enhanced_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- num_severely_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled adults
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 902.0
  - Aggregate: 1,124,499.0

- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 10.0
  - Aggregate: 11,134.0

- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 162.2
  - Median: 0.0
  - Stddev: 1,041.1
  - Non-zero count: 902.0
  - Aggregate: 5,717,050,478.0

- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 10.2
  - Median: 0.0
  - Stddev: 383.8
  - Non-zero count: 119.0
  - Aggregate: 915,975,078.0

- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 10.2
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 128,117.73638916016


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 383.8
  - Non-zero count: 119.0
  - Aggregate: 915,975,078.0

- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.5
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 10.0
  - Aggregate: 98,168,644.0

- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.3
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 10.0
  - Aggregate: 98,168,644.0

- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 10.4
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 18.0
  - Aggregate: 700,664,911.0

- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 10.4
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 18.0
  - Aggregate: 700,664,911.0

- PIP:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 171.5
  - Median: 0.0
  - Stddev: 952.6
  - Non-zero count: 1,303.0
  - Aggregate: 9,129,288,116.0

- PIP_DL:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 115.5
  - Median: 0.0
  - Stddev: 633.9
  - Non-zero count: 1,237.0
  - Aggregate: 6,204,081,620.0

- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 115.5
  - Median: 0.0
  - Stddev: 633.9
  - Non-zero count: 1,237.0
  - Aggregate: 6,204,081,620.0

- PIP_M:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 43.2
  - Median: 0.0
  - Stddev: 373.5
  - Non-zero count: 933.0
  - Aggregate: 2,925,206,555.0

- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 43.2
  - Median: 0.0
  - Stddev: 373.5
  - Non-zero count: 933.0
  - Aggregate: 2,925,206,555.0

- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 8,448.0
  - Aggregate: 10,914,633.0

- state_pension:
  - Type: float
  - Entity: person
  - Description: Income from the State Pension
  - Mean: 1,443.6
  - Median: 0.0
  - Stddev: 3,592.3
  - Non-zero count: 9,056.0
  - Aggregate: 97,643,177,033.0

- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 43,328.0
  - Aggregate: 4,464,280,656.0

- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,443.6
  - Median: 0.0
  - Stddev: 3,592.3
  - Non-zero count: 9,056.0
  - Aggregate: 97,643,177,033.0

- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 43,328.0
  - Aggregate: 69,467,111.0

- DLA:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 99.6
  - Median: 0.0
  - Stddev: 770.2
  - Non-zero count: 964.0
  - Aggregate: 5,554,195,523.0

- DLA_M:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 32.7
  - Median: 0.0
  - Stddev: 350.3
  - Non-zero count: 703.0
  - Aggregate: 2,214,592,909.0

- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 32.7
  - Median: 0.0
  - Stddev: 350.3
  - Non-zero count: 703.0
  - Aggregate: 2,214,592,909.0

- DLA_SC:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 63.4
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 842.0
  - Aggregate: 3,339,602,652.0

- DLA_SC_middle_plus:
  - Type: bool
  - Entity: person
  - Description: Receives at least DLA (self-care) middle rate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 842.0
  - Aggregate: 1,044,250.0

- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 63.4
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 842.0
  - Aggregate: 3,339,602,652.0

- ESA_contrib:
  - Type: float
  - Entity: person
  - Description: ESA (contribution-based)
  - Mean: 24.8
  - Median: 0.0
  - Stddev: 513.3
  - Non-zero count: 248.0
  - Aggregate: 1,887,329,331.0

- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 24.8
  - Median: 0.0
  - Stddev: 513.3
  - Non-zero count: 248.0
  - Aggregate: 1,887,329,331.0

- incapacity_benefit:
  - Type: float
  - Entity: person
  - Description: Incapacity Benefit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- incapacity_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Incapacity Benefit (reported)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- carers_allowance:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance
  - Mean: 37.8
  - Median: 0.0
  - Stddev: 366.1
  - Non-zero count: 499.0
  - Aggregate: 2,340,422,278.0

- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 37.8
  - Median: 0.0
  - Stddev: 366.1
  - Non-zero count: 499.0
  - Aggregate: 2,340,422,278.0

- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 499.0
  - Aggregate: 683,118.0

- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 5.1
  - Median: 0.0
  - Stddev: 206.9
  - Non-zero count: 116.0
  - Aggregate: 510,922,373.0

- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 5.1
  - Median: 0.0
  - Stddev: 206.9
  - Non-zero count: 116.0
  - Aggregate: 510,922,373.0

- SDA:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 1.1
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 13.0
  - Aggregate: 67,038,984.0

- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 1.1
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 13.0
  - Aggregate: 67,038,984.0

- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 4.3
  - Median: 0.0
  - Stddev: 261.5
  - Non-zero count: 19.0
  - Aggregate: 293,400,926.0

- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 5.3
  - Median: 0.0
  - Stddev: 143.4
  - Non-zero count: 35.0
  - Aggregate: 361,546,374.0

- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 1.0
  - Median: 0.0
  - Stddev: 52.5
  - Non-zero count: 57.0
  - Aggregate: 66,524,904.0

- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 36.5
  - Median: 0.0
  - Stddev: 630.5
  - Non-zero count: 263.0
  - Aggregate: 2,472,072,403.0

- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 225.4
  - Median: 0.0
  - Stddev: 1,334.0
  - Non-zero count: 637.0
  - Aggregate: 15,246,081,065.0

- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 47.2
  - Median: 0.0
  - Stddev: 710.8
  - Non-zero count: 351.0
  - Aggregate: 3,193,544,604.0

- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 2.5
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 44.0
  - Aggregate: 288,654,985.0

- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 2.5
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 44.0
  - Aggregate: 288,654,985.0

- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 2.2
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 20.0
  - Aggregate: 110,894,796.0

- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 2.2
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 20.0
  - Aggregate: 110,894,796.0

- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 69.2
  - Median: 0.0
  - Stddev: 111.0
  - Non-zero count: 6,744.0
  - Aggregate: 1,939,757,500.0

- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 29.6
  - Median: 0.0
  - Stddev: 74.7
  - Non-zero count: 9,168.0
  - Aggregate: 1,999,582,079.0

- AA:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 49.0
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 648.0
  - Aggregate: 3,311,172,311.0

- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 49.0
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 648.0
  - Aggregate: 3,311,172,311.0

- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: inf
  - Median: 13,399.9
  - Stddev: nan
  - Non-zero count: 22,736.0
  - Aggregate: inf

- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,975.0
  - Aggregate: 2,492,757.0

- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 9,502.7
  - Median: 9,753.1
  - Stddev: 2,320.7
  - Non-zero count: 22,736.0
  - Aggregate: 334,871,260,816.0

- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 2.0
  - Median: 2.0
  - Stddev: 1.1
  - Non-zero count: 22,736.0
  - Aggregate: 69,548,809.0

- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 1,853.7
  - Median: 0.0
  - Stddev: 2,930.7
  - Non-zero count: 7,040.0
  - Aggregate: 65,324,574,081.0

- LHA_category:
  - Type: Categorical
  - Entity: benunit
  - Description: LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms


- LHA_eligible:
  - Type: float
  - Entity: benunit
  - Description: Eligibility for Local Housing Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 91.2
  - Median: 0.0
  - Stddev: 291.9
  - Non-zero count: 2,696.0
  - Aggregate: 3,215,111,692.0

- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 66.9
  - Median: 0.0
  - Stddev: 217.2
  - Non-zero count: 2,696.0
  - Aggregate: 3,315,202,137.0

- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 562.9
  - Median: 0.0
  - Stddev: 589.0
  - Non-zero count: 21,040.0
  - Aggregate: 38,074,520,056.0

- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 235.0
  - Median: 0.0
  - Stddev: 748.4
  - Non-zero count: 3,684.0
  - Aggregate: 13,676,969,253.0

- claims_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 3,672.0
  - Aggregate: 5,650,671.0

- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 66.2
  - Median: 0.0
  - Stddev: 620.4
  - Non-zero count: 437.0
  - Aggregate: 2,333,107,916.0

- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 1,145.8
  - Median: 0.0
  - Stddev: 3,210.1
  - Non-zero count: 4,244.0
  - Aggregate: 40,379,413,519.0

- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 27,155.9
  - Median: 20,513.1
  - Stddev: 24,765.6
  - Non-zero count: 21,440.0
  - Aggregate: 956,966,088,515.0

- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,244.0
  - Aggregate: 6,076,929.0

- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 383.0
  - Median: 0.0
  - Stddev: 1,103.3
  - Non-zero count: 2,312.0
  - Aggregate: 13,819,209,373.0

- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 18,416.0
  - Aggregate: 28,463,724.0

- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 12.2
  - Median: 0.0
  - Stddev: 219.2
  - Non-zero count: 64.0
  - Aggregate: 429,010,560.0

- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 9.1
  - Median: 0.0
  - Stddev: 189.6
  - Non-zero count: 44.0
  - Aggregate: 321,468,366.0

- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 10.0
  - Median: 0.0
  - Stddev: 197.8
  - Non-zero count: 45.0
  - Aggregate: 353,357,723.0

- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 26,798.3
  - Median: 20,421.8
  - Stddev: 25,864.2
  - Non-zero count: 19,984.0
  - Aggregate: 944,364,638,625.0

- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 413.0
  - Aggregate: 752,283.0

- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 19.2
  - Median: 0.0
  - Stddev: 243.0
  - Non-zero count: 146.0
  - Aggregate: 817,500,738.0

- claims_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim JSA based on survey response and take-up rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,562.0
  - Aggregate: 3,924,072.0

- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 12,824.0
  - Aggregate: 19,785,158.0

- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 116.9
  - Median: 0.0
  - Stddev: 1,024.6
  - Non-zero count: 481.0
  - Aggregate: 4,118,230,206.0

- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 481.0
  - Aggregate: 628,035.0

- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 81.8
  - Median: 0.0
  - Stddev: 740.1
  - Non-zero count: 485.0
  - Aggregate: 4,242,173,714.0

- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 87.0
  - Aggregate: 97,384.0

- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 481.0
  - Aggregate: 628,035.0

- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 332.9
  - Median: 0.0
  - Stddev: 1,298.1
  - Non-zero count: 2,156.0
  - Aggregate: 11,730,060,378.0

- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,636.0
  - Aggregate: 4,379,540.0

- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 15,424.4
  - Median: -104.0
  - Stddev: 26,615.0
  - Non-zero count: 18,912.0
  - Aggregate: 1,043,317,247,105.0

- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 36.7
  - Median: 0.0
  - Stddev: 286.2
  - Non-zero count: 493.0
  - Aggregate: 1,292,711,884.0

- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1,169.9
  - Median: 0.0
  - Stddev: 2,396.1
  - Non-zero count: 5,584.0
  - Aggregate: 41,226,436,002.0

- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 151.9
  - Median: 0.0
  - Stddev: 1,029.9
  - Non-zero count: 1,051.0
  - Aggregate: 5,351,644,761.0

- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 11,160.0
  - Aggregate: 19,046,780.0

- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 339.0
  - Median: 0.0
  - Stddev: 1,336.5
  - Non-zero count: 2,156.0
  - Aggregate: 11,947,391,447.0

- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 19,879.2
  - Median: 14,020.7
  - Stddev: 25,253.5
  - Non-zero count: 13,192.0
  - Aggregate: 700,538,791,171.0

- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1,112.2
  - Median: 0.0
  - Stddev: 2,889.8
  - Non-zero count: 5,184.0
  - Aggregate: 39,192,133,348.0

- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 14,665.4
  - Median: 10,575.3
  - Stddev: 16,535.0
  - Non-zero count: 19,152.0
  - Aggregate: 516,803,463,130.0

- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 628.3
  - Median: 0.0
  - Stddev: 1,269.3
  - Non-zero count: 9,144.0
  - Aggregate: 42,501,564,958.0

- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 2.3
  - Median: 0.0
  - Stddev: 45.2
  - Non-zero count: 37.0
  - Aggregate: 80,448,455.0

- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 439.8
  - Median: 0.0
  - Stddev: 453.0
  - Non-zero count: 20,912.0
  - Aggregate: 29,749,839,891.0

- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 4.2
  - Median: 0.0
  - Stddev: 103.7
  - Non-zero count: 20.0
  - Aggregate: 143,454,320.0

- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 7,649.9
  - Median: 6,118.9
  - Stddev: 4,964.1
  - Non-zero count: 22,688.0
  - Aggregate: 269,580,649,466.0

- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8,433.6
  - Median: 7,756.2
  - Stddev: 1,884.7
  - Non-zero count: 22,736.0
  - Aggregate: 297,198,996,373.0

- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 14,327.3
  - Median: 16,216.2
  - Stddev: 3,270.6
  - Non-zero count: 43,328.0
  - Aggregate: 969,105,264,862.0

- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 3,968.0
  - Aggregate: 5,252,254.0

- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 222.6
  - Median: 0.0
  - Stddev: 624.3
  - Non-zero count: 3,854.0
  - Aggregate: 11,798,158,713.0

- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 4,840.3
  - Median: 3,898.1
  - Stddev: 1,189.8
  - Non-zero count: 22,736.0
  - Aggregate: 170,570,331,734.0

- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 3,731.8
  - Median: 2.7
  - Stddev: 11,605.1
  - Non-zero count: 12,800.0
  - Aggregate: 131,507,119,457.0

- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1,773.0
  - Median: 0.0
  - Stddev: 2,835.1
  - Non-zero count: 7,344.0
  - Aggregate: 62,479,059,792.0

- claims_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 3,388.0
  - Aggregate: 4,832,498.0

- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 17,024.0
  - Aggregate: 27,803,365.0

- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 7,344.0
  - Aggregate: 10,518,640.0

- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 6,584.0
  - Aggregate: 9,735,355.0

- is_in_startup_period:
  - Type: bool
  - Entity: person
  - Description: In a start-up period
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- legacy_benefits:
  - Type: float
  - Entity: benunit
  - Description: Legacy benefits
  - Mean: 425.1
  - Median: 0.0
  - Stddev: 2,047.7
  - Non-zero count: 2,273,298.5


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,260.0
  - Aggregate: 2,930,352.0

- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.8
  - Non-zero count: 5,584.0
  - Aggregate: 13,308,714.0

- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 654.4
  - Median: 0.0
  - Stddev: 2,924.7
  - Non-zero count: 1,992.0
  - Aggregate: 23,059,398,898.0

- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 262.7
  - Median: 0.0
  - Stddev: 1,447.0
  - Non-zero count: 902.0
  - Aggregate: 12,026,161,076.0

- claims_PC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Pension Credit
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 14,456.0
  - Aggregate: 22,364,643.0

- guarantee_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 29,744.1
  - Median: 22,679.7
  - Stddev: 26,736.6
  - Non-zero count: 21,600.0
  - Aggregate: 1,048,172,723,149.0

- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 66.3
  - Median: 0.0
  - Stddev: 578.5
  - Non-zero count: 892.0
  - Aggregate: 2,335,002,476.0

- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 53.0
  - Median: 0.0
  - Stddev: 545.6
  - Non-zero count: 523.0
  - Aggregate: 1,866,333,885.0

- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 1,411.8
  - Median: 0.0
  - Stddev: 4,225.2
  - Non-zero count: 3,462.0
  - Aggregate: 49,751,223,640.0

- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 13.3
  - Median: 0.0
  - Stddev: 175.8
  - Non-zero count: 570.0
  - Aggregate: 468,668,589.0

- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,464.0
  - Aggregate: 6,897,251.0

- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 122.6
  - Median: 0.0
  - Stddev: 578.8
  - Non-zero count: 920.0
  - Aggregate: 3,437,964,134.0

- savings_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Savings Credit
  - Mean: 29,611.0
  - Median: 22,555.5
  - Stddev: 26,783.6
  - Non-zero count: 21,552.0
  - Aggregate: 1,043,484,224,429.0

- would_claim_PC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 14,456.0
  - Aggregate: 22,364,643.0

- claims_IS:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Income Support
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,082.0
  - Aggregate: 6,293,980.0

- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 16.7
  - Median: 0.0
  - Stddev: 395.8
  - Non-zero count: 83.0
  - Aggregate: 589,311,267.0

- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 40.5
  - Median: 0.0
  - Stddev: 670.0
  - Non-zero count: 151.0
  - Aggregate: 1,427,207,128.0

- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 26,798.3
  - Median: 20,421.8
  - Stddev: 25,864.2
  - Non-zero count: 19,984.0
  - Aggregate: 944,364,638,625.0

- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 879.0
  - Aggregate: 1,159,297.0

- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 21.0
  - Median: 0.0
  - Stddev: 382.0
  - Non-zero count: 327.0
  - Aggregate: 1,423,553,134.0

- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 20,416.0
  - Aggregate: 31,650,847.0

- in_deep_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), after housing costs
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 1,962.0
  - Aggregate: 2,891,419.0

- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,117.0
  - Aggregate: 1,620,566.0

- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,332.0
  - Aggregate: 6,146,228.0

- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,040.0
  - Aggregate: 5,561,598.0

- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 1,663.7
  - Median: 0.0
  - Stddev: 4,353.6
  - Non-zero count: 4,332.0
  - Aggregate: 46,624,129,981.0

- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 1,208.9
  - Median: 0.0
  - Stddev: 3,453.6
  - Non-zero count: 4,040.0
  - Aggregate: 33,877,341,023.0

- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 14,792.8
  - Median: 13,992.9
  - Stddev: 5,767.1
  - Non-zero count: 19,216.0
  - Aggregate: 414,550,661,278.0

- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 17,340.0
  - Median: 16,331.6
  - Stddev: 5,599.4
  - Non-zero count: 19,216.0
  - Aggregate: 485,932,395,851.0

- BRMA:
  - Type: Categorical
  - Entity: household
  - Description: Broad Rental Market Area


- local_authority:
  - Type: Categorical
  - Entity: household
  - Description: The Local Authority for the household


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 24,544.0
  - Aggregate: 41,424,595.0

- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 8,976.0
  - Aggregate: 11,585,457.0

- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,792.0
  - Aggregate: 14,630,564.0

- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: -1,682,986,160.8
  - Median: -2,147,483,648.0
  - Stddev: 898,368,124.3
  - Non-zero count: 9,792.0
  - Aggregate: -1.1383822063300427e+17

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
  - Aggregate: 0.0

- in_HE:
  - Type: bool
  - Entity: person
  - Description: In higher education
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- in_social_housing:
  - Type: bool
  - Entity: person
  - Description: Whether this person lives in social housing
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,468.0
  - Aggregate: 11,009,980.0

- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 25,072.0
  - Aggregate: 42,095,419.0

- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 33,536.0
  - Aggregate: 53,010,052.0

- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,404.0
  - Aggregate: 8,105,126.0

- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 22,736.0
  - Aggregate: 36,327,238.0

- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,792.0
  - Aggregate: 14,630,564.0

- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,584.0
  - Aggregate: 8,568,469.0

- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 22,464.0
  - Aggregate: 34,246,098.0

- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 19,200.0
  - Aggregate: 28,887,466.0

- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 20,848.0
  - Aggregate: 33,394,518.0

- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 2,124.0
  - Aggregate: 3,283,506.0

- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,676.0
  - Aggregate: 11,347,058.0

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
  - Non-zero count: 34,592.0
  - Aggregate: 54,753,101.0

- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 43,328.0
  - Aggregate: 67,640,616.0

- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 959,647.1
  - Median: 959,487.5
  - Stddev: 554,308.8
  - Non-zero count: 43,328.0
  - Aggregate: 64,911,118,271,035.0

- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight (region-adjusted)
  - Mean: 2,066.0
  - Median: 1,753.5
  - Stddev: 887.5
  - Non-zero count: 43,328.0
  - Aggregate: 139,747,048,202.0

- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 2,002.8
  - Median: 1,700.0
  - Stddev: 858.7
  - Non-zero count: 43,328.0
  - Aggregate: 135,473,727,297.0

- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 959,645.0
  - Median: 959,485.5
  - Stddev: 554,307.8
  - Non-zero count: 43,328.0
  - Aggregate: 64,910,981,372,234.0

- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 959,633.4
  - Median: 959,475.5
  - Stddev: 554,307.9
  - Non-zero count: 43,328.0
  - Aggregate: 64,910,192,782,923.0

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
  - Stddev: 0.4
  - Non-zero count: 19,216.0
  - Aggregate: 29,625,745.0

- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.1
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 19,216.0
  - Aggregate: 29,754,177.0

- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 958,404.5
  - Median: 958,313.7
  - Stddev: 554,559.4
  - Non-zero count: 19,216.0
  - Aggregate: 26,858,147,234,600.0

- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.3
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 19,216.0
  - Aggregate: 35,239,742.0

- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.4
  - Median: 2.0
  - Stddev: 1.3
  - Non-zero count: 19,216.0
  - Aggregate: 65,614,604.0

- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 1,938.5
  - Median: 1,639.0
  - Stddev: 836.5
  - Non-zero count: 19,216.0
  - Aggregate: 54,323,852,197.0

- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 19,216.0
  - Aggregate: 28,023,811.0

- is_renting:
  - Type: bool
  - Entity: household
  - Description: Is renting
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- is_shared_accommodation:
  - Type: bool
  - Entity: household
  - Description: Whether the household is shared accommodation
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- num_bedrooms:
  - Type: int
  - Entity: household
  - Description: The number of bedrooms in the house
  - Mean: 2.9
  - Median: 3.0
  - Stddev: 1.0
  - Non-zero count: 19,216.0
  - Aggregate: 77,782,274.0

- region:
  - Type: Categorical
  - Entity: household
  - Description: Region


- tenure_type:
  - Type: Categorical
  - Entity: household
  - Description: Tenure type of the household


- benunit_has_children:
  - Type: bool
  - Entity: benunit
  - Description: Has children
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,584.0
  - Aggregate: 8,311,716.0

- benunit_has_children_or_qyp:
  - Type: bool
  - Entity: benunit
  - Description: Has children or qualifying young people
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,244.0
  - Aggregate: 7,635,545.0

- benunit_id:
  - Type: int
  - Entity: benunit
  - Description: ID for the family
  - Mean: 959,451.6
  - Median: 961,134.1
  - Stddev: 553,578.7
  - Non-zero count: 22,736.0
  - Aggregate: 33,810,825,217,040.0

- benunit_is_renting:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is renting
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- benunit_tenure_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Tenure type of the family's household


- benunit_weight:
  - Type: float
  - Entity: benunit
  - Description: Weight factor for the benefit unit
  - Mean: 2,072.4
  - Median: 1,742.0
  - Stddev: 899.8
  - Non-zero count: 22,736.0
  - Aggregate: 73,032,389,132.0

- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 47.7
  - Median: 48.0
  - Stddev: 18.7
  - Non-zero count: 22,736.0
  - Aggregate: 1,679,619,656.0

- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: -inf
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 5,220.0
  - Aggregate: -inf

- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 22,736.0
  - Aggregate: 35,239,742.0

- family_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Family composition


- is_joint_benunit:
  - Type: bool
  - Entity: benunit
  - Description: Joint benefit unit
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 10,696.0
  - Aggregate: 16,250,915.0

- is_married:
  - Type: bool
  - Entity: benunit
  - Description: Married
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- num_adults:
  - Type: int
  - Entity: benunit
  - Description: The number of adults in the family
  - Mean: 1.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 22,464.0
  - Aggregate: 51,423,206.0

- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.9
  - Non-zero count: 5,584.0
  - Aggregate: 14,191,398.0

- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 45.9
  - Median: 45.0
  - Stddev: 18.6
  - Non-zero count: 22,736.0
  - Aggregate: 1,618,746,804.0

- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: inf
  - Median: inf
  - Stddev: nan
  - Non-zero count: 22,288.0
  - Aggregate: inf

- state_id:
  - Type: int
  - Entity: state
  - Description: State ID
  - Mean: 11.5
  - Median: 11.5
  - Stddev: 0.7
  - Non-zero count: 1.0
  - Aggregate: 1.0

- state_weight:
  - Type: float
  - Entity: state
  - Description: State weight
  - Mean: 0.5
  - Median: 0.5
  - Stddev: 0.0
  - Non-zero count: 1.0
  - Aggregate: 1.0

- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status


- is_in_work:
  - Type: bool
  - Entity: person
  - Description: In work
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 20,384.0
  - Aggregate: 34,812,531.0

- age:
  - Type: int
  - Entity: person
  - Description: Age
  - Mean: 39.3
  - Median: 39.0
  - Stddev: 23.6
  - Non-zero count: 42,880.0
  - Aggregate: 2,655,595,264.0

- birth_date:
  - Type: Categorical
  - Entity: person
  - Description: Date of birth


- birth_year:
  - Type: int
  - Entity: person
  - Description: Birth year
  - Mean: 1,982.7
  - Median: 1,983.0
  - Stddev: 23.6
  - Non-zero count: 43,328.0
  - Aggregate: 134,113,730,283.0

- expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (expected)
  - Mean: 12.0
  - Median: 0.0
  - Stddev: 164.5
  - Non-zero count: 301.0
  - Aggregate: 336,629,674.0

- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 222.5
  - Median: 0.0
  - Stddev: 3,045.6
  - Non-zero count: 301.0
  - Aggregate: 6,234,636,283.0

- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 772.0
  - Aggregate: 1,363,386.0

- ltt_on_non_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LTT on non-residential property rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- ltt_on_non_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on non-residential property transactions
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 54.1
  - Non-zero count: 3.0
  - Aggregate: 14,952,526.0

- ltt_on_rent:
  - Type: float
  - Entity: household
  - Description: LTT on property rental
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- ltt_on_residential_property_rent:
  - Type: float
  - Entity: household
  - Description: LTT on residential property rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0
  - Aggregate: 0.0

- ltt_on_residential_property_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on residential property
  - Mean: 5,389.5
  - Median: 0.0
  - Stddev: 18,187.7
  - Non-zero count: 7,664.0
  - Aggregate: 151,034,495,834.0

- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 5,390.0
  - Median: 0.0
  - Stddev: 18,188.3
  - Non-zero count: 7,664.0
  - Aggregate: 151,049,448,361.0

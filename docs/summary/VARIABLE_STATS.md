# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2022) 2018-19 Family Resources Survey, with simulation turned on.


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


- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: -1,425.5
  - Median: -139.7
  - Stddev: 2,656.5
  - Non-zero count: 0.0
  - Aggregate: -42,136,968,846.0

- hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income
  - Mean: -1,425.5
  - Median: -139.7
  - Stddev: 2,656.5
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
  - Mean: 111.6
  - Median: 8.4
  - Stddev: 213.0
  - Non-zero count: 18,480,916.636779785


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 111.6
  - Median: 8.4
  - Stddev: 213.0
  - Non-zero count: 18,480,916.636779785


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
  - Mean: 251.6
  - Median: 11.7
  - Stddev: 832.2
  - Non-zero count: 18,862,621.805610657


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 24,195,938.79616165


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
  - Stddev: 1,163.3
  - Non-zero count: 109,249.38595581055


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
  - Mean: 2,784.3
  - Median: 0.0
  - Stddev: 14,829.8
  - Non-zero count: 3,634,948.652656555


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 2,854.5
  - Median: 0.0
  - Stddev: 15,108.6
  - Non-zero count: 3,668,258.709236145


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 2,592.2
  - Median: 0.0
  - Stddev: 14,423.6
  - Non-zero count: 3,220,432.1008224487


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
  - Mean: 164.2
  - Median: 0.0
  - Stddev: 537.8
  - Non-zero count: 6,944,473.9205207825


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 188.7
  - Median: 0.0
  - Stddev: 388.0
  - Non-zero count: 13,673,870.674171448


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
  - Mean: 1,131.4
  - Median: 85.0
  - Stddev: 2,159.4
  - Non-zero count: 18,480,916.636779785


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 1,131.4
  - Median: 85.0
  - Stddev: 2,159.4
  - Non-zero count: 18,480,916.636779785


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
  - Mean: 140.4
  - Median: 0.0
  - Stddev: 423.6
  - Non-zero count: 7,876,758.877456665


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 62,815,325.53197098


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 43.3
  - Median: 0.0
  - Stddev: 5,833.7
  - Non-zero count: 12,723,131.263820648


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5,239.4
  - Median: 1,867.0
  - Stddev: 5,640.3
  - Non-zero count: 35,769,661.41034317


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 27.6
  - Median: 0.0
  - Stddev: 225.3
  - Non-zero count: 1,290,683.0376968384


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
  - Mean: 199,108.8
  - Median: 14,958.1
  - Stddev: 379,999.5
  - Non-zero count: 18,480,916.636779785


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 18,480,916.636779785


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 195,688.1
  - Median: 135,000.0
  - Stddev: 242,235.6
  - Non-zero count: 17,556,145.707069397


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 2,460.5
  - Median: 0.0
  - Stddev: 31,084.9
  - Non-zero count: 212,128.03999328613


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 11,544.4
  - Median: 0.0
  - Stddev: 75,007.6
  - Non-zero count: 1,536,092.0964355469


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 233,996.6
  - Median: 140,000.0
  - Stddev: 496,108.8
  - Non-zero count: 17,895,796.915390015


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 207,232.5
  - Median: 137,000.0
  - Stddev: 268,339.4
  - Non-zero count: 17,672,996.34412384


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 62,673.3
  - Median: 4,708.3
  - Stddev: 119,619.2
  - Non-zero count: 18,480,916.636779785


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 153,638.2
  - Median: 91,921.6
  - Stddev: 325,724.9
  - Non-zero count: 17,895,796.915390015


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 216,311.5
  - Median: 118,184.9
  - Stddev: 368,920.1
  - Non-zero count: 21,909,554.881454468


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
  - Mean: 31.0
  - Median: 0.0
  - Stddev: 447.2
  - Non-zero count: 651,845.5383453369


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 574.0
  - Median: 0.0
  - Stddev: 8,283.8
  - Non-zero count: 651,845.5383453369


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 2,469,405.8291015625


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
  - Mean: 67.0
  - Median: 0.0
  - Stddev: 1,134.4
  - Non-zero count: 109,249.38595581055


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
  - Mean: 7,382.8
  - Median: 0.0
  - Stddev: 22,608.4
  - Non-zero count: 8,496,665.474945068


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
  - Mean: 7,449.8
  - Median: 0.0
  - Stddev: 22,854.8
  - Non-zero count: 8,501,620.364715576


- carbon_consumption:
  - Type: float
  - Entity: household
  - Description: Carbon consumption
  - Mean: 19.4
  - Median: 14.3
  - Stddev: 18.3
  - Non-zero count: 28,037,492.495838165


- alcohol_and_tobacco_consumption:
  - Type: float
  - Entity: household
  - Description: Alcohol and tobacco
  - Mean: 752.3
  - Median: 253.5
  - Stddev: 1,258.8
  - Non-zero count: 17,439,004.083824158


- clothing_and_footwear_consumption:
  - Type: float
  - Entity: household
  - Description: Clothing and footwear
  - Mean: 1,488.6
  - Median: 459.7
  - Stddev: 2,651.7
  - Non-zero count: 18,807,475.51677704


- communication_consumption:
  - Type: float
  - Entity: household
  - Description: Communication
  - Mean: 770.1
  - Median: 420.2
  - Stddev: 1,826.9
  - Non-zero count: 23,109,122.424633026


- education_consumption:
  - Type: float
  - Entity: household
  - Description: Education
  - Mean: 628.6
  - Median: 0.0
  - Stddev: 4,125.8
  - Non-zero count: 2,727,918.4423599243


- food_and_non_alcoholic_beverages_consumption:
  - Type: float
  - Entity: household
  - Description: Food and alcoholic beverages
  - Mean: 3,487.1
  - Median: 2,978.6
  - Stddev: 2,186.6
  - Non-zero count: 27,817,039.23921585


- health_consumption:
  - Type: float
  - Entity: household
  - Description: Health
  - Mean: 573.6
  - Median: 52.3
  - Stddev: 1,913.0
  - Non-zero count: 17,314,746.39849472


- household_furnishings_consumption:
  - Type: float
  - Entity: household
  - Description: Household furnishings
  - Mean: 2,735.4
  - Median: 780.0
  - Stddev: 5,295.1
  - Non-zero count: 26,765,223.45269394


- housing_water_and_electricity_consumption:
  - Type: float
  - Entity: household
  - Description: Housing, water and electricity
  - Mean: 4,951.7
  - Median: 2,621.3
  - Stddev: 6,178.6
  - Non-zero count: 27,986,278.69888687


- miscellaneous_consumption:
  - Type: float
  - Entity: household
  - Description: Miscellaneous
  - Mean: 3,591.1
  - Median: 1,736.3
  - Stddev: 6,500.3
  - Non-zero count: 27,553,594.65301895


- recreation_consumption:
  - Type: float
  - Entity: household
  - Description: Recreation
  - Mean: 5,630.7
  - Median: 2,159.7
  - Stddev: 8,895.1
  - Non-zero count: 27,719,231.960407257


- restaurants_and_hotels_consumption:
  - Type: float
  - Entity: household
  - Description: Restaurants and hotels
  - Mean: 3,694.5
  - Median: 2,052.2
  - Stddev: 4,507.1
  - Non-zero count: 24,768,016.094341278


- transport_consumption:
  - Type: float
  - Entity: household
  - Description: Transport
  - Mean: 6,290.5
  - Median: 3,152.9
  - Stddev: 10,853.3
  - Non-zero count: 24,980,155.469112396


- additional_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Residential property bought (additional)
  - Mean: 11,544.4
  - Median: 0.0
  - Stddev: 75,007.6
  - Non-zero count: 1,536,092.0964355469


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
  - Mean: 195,688.1
  - Median: 135,000.0
  - Stddev: 242,235.6
  - Non-zero count: 17,556,145.707069397


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,329,702.849460602


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 2,460.5
  - Median: 0.0
  - Stddev: 31,084.9
  - Non-zero count: 212,128.03999328613


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
  - Non-zero count: 28,047,312.09782791


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
  - Mean: 3,008.4
  - Median: -52.0
  - Stddev: 4,221.4
  - Non-zero count: 11,699,710.715679169


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
  - Mean: 315.4
  - Median: 0.0
  - Stddev: 2,145.3
  - Non-zero count: 22,132,514.64226532


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 16,795.0
  - Median: 6,652.9
  - Stddev: 26,078.0
  - Non-zero count: 38,536,362.80913544


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 35,891.2
  - Median: 29,898.9
  - Stddev: 22,294.0
  - Non-zero count: 27,989,393.875141144


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 33,217.5
  - Median: 27,585.6
  - Stddev: 23,261.6
  - Non-zero count: 27,574,744.223651886


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 34,513.4
  - Median: 28,928.4
  - Stddev: 21,476.7
  - Non-zero count: 27,981,670.653583527


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 20,990.2
  - Median: 15,364.6
  - Stddev: 26,211.3
  - Non-zero count: 50,024,772.62595749


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 39,534.8
  - Median: 31,670.7
  - Stddev: 27,441.0
  - Non-zero count: 27,989,393.875141144


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 36,526.4
  - Median: 28,730.3
  - Stddev: 27,821.4
  - Non-zero count: 27,574,744.223651886


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 853.3
  - Median: 0.0
  - Stddev: 1,034.5
  - Non-zero count: 31,427,095.239601135


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 50,504.6
  - Median: 36,847.6
  - Stddev: 42,000.8
  - Non-zero count: 28,012,301.547016144


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 41,828.0
  - Median: 28,420.7
  - Stddev: 44,457.9
  - Non-zero count: 22,755,522.4143219


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 38,109.3
  - Median: 30,409.5
  - Stddev: 26,673.6
  - Non-zero count: 27,981,670.653583527


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 31,431,252.62046051


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
  - Mean: 69.8
  - Median: -1.0
  - Stddev: 1,944.1
  - Non-zero count: 225,962.52822875977


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 40.6
  - Median: 0.0
  - Stddev: 515.9
  - Non-zero count: 940,471.4236831665


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 17,408.2
  - Median: 7,564.4
  - Stddev: 26,574.0
  - Non-zero count: 41,030,164.200920105


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.7
  - Median: 8.7
  - Stddev: 1.7
  - Non-zero count: 67,391,291.62257004


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 49.0
  - Median: 0.0
  - Stddev: 828.2
  - Non-zero count: 748,346.7191314697


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 17,047.5
  - Median: 14,708.9
  - Stddev: 17,585.3
  - Non-zero count: 50,024,772.62595749


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: 76.6
  - Median: 0.0
  - Stddev: 1,219.7
  - Non-zero count: 892,766.4016265869


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
  - Mean: 16.4
  - Median: 0.0
  - Stddev: 19.9
  - Non-zero count: 31,427,095.239601135


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
  - Mean: 102.7
  - Median: 0.0
  - Stddev: 881.8
  - Non-zero count: 2,428,558.494216919


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1,496.3
  - Median: 1,434.3
  - Stddev: 751.4
  - Non-zero count: 26,975,405.34729004


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1,326.4
  - Median: 1,418.2
  - Stddev: 859.0
  - Non-zero count: 24,800,738.154541016


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
  - Mean: 3,008.4
  - Median: -52.0
  - Stddev: 4,221.4
  - Non-zero count: 11,699,710.715679169


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 49.4
  - Median: 0.0
  - Stddev: 339.3
  - Non-zero count: 2,124,521.3208236694


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 35.8
  - Median: 0.0
  - Stddev: 621.9
  - Non-zero count: 664,293.7918395996


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
  - Mean: 2,278.4
  - Median: 0.0
  - Stddev: 5,618.7
  - Non-zero count: 7,490,337.32724762


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 842.3
  - Median: -52.0
  - Stddev: 2,093.5
  - Non-zero count: 7,464,408.846168518


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 411.6
  - Median: 0.0
  - Stddev: 1,299.7
  - Non-zero count: 17,404,846.38948059


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1,252.1
  - Median: 0.0
  - Stddev: 3,035.7
  - Non-zero count: 11,699,710.715679169


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 28.8
  - Median: 0.0
  - Stddev: 172.5
  - Non-zero count: 2,085,966.885169983


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 384.7
  - Median: 358.8
  - Stddev: 252.8
  - Non-zero count: 26,779,095.25894165


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 17.0
  - Non-zero count: 2,428,558.494216919


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
  - Mean: 12,395.2
  - Median: 6,470.8
  - Stddev: 16,512.4
  - Non-zero count: 27,718,312.51246643


- tax:
  - Type: float
  - Entity: person
  - Description: Taxes
  - Mean: 3,942.7
  - Median: 31.8
  - Stddev: 9,463.7
  - Non-zero count: 33,932,594.03930664


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3,942.7
  - Median: 31.8
  - Stddev: 9,463.7
  - Non-zero count: 33,932,594.03930664


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
  - Mean: 9.1
  - Median: 0.0
  - Stddev: 33.8
  - Non-zero count: 3,881,959.060783386


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 9.1
  - Median: 0.0
  - Stddev: 33.8
  - Non-zero count: 3,881,959.060783386


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.3
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 22,866,955.889442444


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 838.6
  - Median: 0.0
  - Stddev: 1,563.6
  - Non-zero count: 23,320,426.683937073


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1,212.8
  - Median: 0.0
  - Stddev: 2,917.4
  - Non-zero count: 23,795,346.481002808


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1,212.8
  - Median: 0.0
  - Stddev: 2,917.4
  - Non-zero count: 23,795,346.481002808


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2,157.3
  - Median: 0.0
  - Stddev: 4,365.8
  - Non-zero count: 27,295,169.312095642


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 113.8
  - Median: 0.0
  - Stddev: 487.7
  - Non-zero count: 3,536,670.199661255


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 838.6
  - Median: 0.0
  - Stddev: 1,563.6
  - Non-zero count: 23,320,426.683937073


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 944.5
  - Median: 0.0
  - Stddev: 1,602.0
  - Non-zero count: 26,518,083.046035767


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 122.9
  - Median: 0.0
  - Stddev: 510.7
  - Non-zero count: 3,881,959.060783386


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 900.5
  - Median: 0.0
  - Stddev: 8,395.7
  - Non-zero count: 431,039.7362976074


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 405.2
  - Median: 0.0
  - Stddev: 3,775.3
  - Non-zero count: 431,039.7362976074


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 21.4
  - Non-zero count: 12,536.208129882812


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7,759.6
  - Median: 0.0
  - Stddev: 11,526.2
  - Non-zero count: 31,272,217.114189148


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1,551.9
  - Median: 0.0
  - Stddev: 2,305.8
  - Non-zero count: 31,272,217.114189148


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 16.0
  - Median: 0.0
  - Stddev: 404.9
  - Non-zero count: 131,601.2092590332


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 23.3
  - Median: 0.0
  - Stddev: 419.6
  - Non-zero count: 649,533.8683013916


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 32.9
  - Median: 0.0
  - Stddev: 463.2
  - Non-zero count: 1,052,273.9729003906


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2,932.4
  - Median: 0.0
  - Stddev: 8,148.0
  - Non-zero count: 31,272,217.114189148


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 11,079.3
  - Median: 0.0
  - Stddev: 23,425.4
  - Non-zero count: 31,272,217.114189148


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 2,419.3
  - Median: 0.0
  - Stddev: 11,067.2
  - Non-zero count: 4,373,399.865852356


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 967.7
  - Median: 0.0
  - Stddev: 4,425.9
  - Non-zero count: 4,373,399.865852356


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 4.9
  - Median: 0.0
  - Stddev: 210.4
  - Non-zero count: 40,648.446533203125


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2,998.3
  - Median: 0.0
  - Stddev: 8,331.0
  - Non-zero count: 31,659,388.288963318


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2,970.6
  - Median: 0.0
  - Stddev: 8,229.5
  - Non-zero count: 31,659,388.288963318


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 35,950,989.61675644


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,455,755.056091309


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 5.3
  - Median: 0.0
  - Stddev: 129.7
  - Non-zero count: 171,311.65103149414


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4,985.7
  - Median: 5,000.0
  - Stddev: 191.3
  - Non-zero count: 67,311,822.27305222


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 153.0
  - Median: 0.0
  - Stddev: 1,814.4
  - Non-zero count: 1,052,273.9729003906


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 11,253.6
  - Median: 0.0
  - Stddev: 23,679.5
  - Non-zero count: 31,659,388.288963318


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 21.3
  - Median: 0.0
  - Stddev: 497.4
  - Non-zero count: 171,311.65103149414


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
  - Mean: 15.8
  - Median: 0.0
  - Stddev: 378.5
  - Non-zero count: 139,556.93923950195


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 6.4
  - Median: 0.0
  - Stddev: 170.3
  - Non-zero count: 113,215.05683898926


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,484.5
  - Median: 10,633.0
  - Stddev: 25,692.8
  - Non-zero count: 46,988,555.442489624


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
  - Mean: 22.2
  - Median: 0.0
  - Stddev: 417.2
  - Non-zero count: 250,619.3952484131


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
  - Mean: 440.4
  - Median: 0.0
  - Stddev: 1,319.8
  - Non-zero count: 18,757,364.74167633


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1,685.0
  - Median: 0.0
  - Stddev: 2,065.8
  - Non-zero count: 30,798,390.683929443


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 46.1
  - Median: 0.0
  - Stddev: 380.0
  - Non-zero count: 9,124,797.696533203


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 196.9
  - Median: 0.0
  - Stddev: 1,944.9
  - Non-zero count: 3,874,752.3265533447


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 11,723.2
  - Median: 0.0
  - Stddev: 22,898.1
  - Non-zero count: 32,534,500.96270752


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 49.0
  - Median: 0.0
  - Stddev: 828.2
  - Non-zero count: 748,346.7191314697


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1,969.7
  - Median: 0.0
  - Stddev: 6,889.5
  - Non-zero count: 9,308,185.06049347


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 240.8
  - Median: 0.0
  - Stddev: 2,039.8
  - Non-zero count: 1,894,803.254058838


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 72.5
  - Median: 0.0
  - Stddev: 590.1
  - Non-zero count: 21,283,443.14728546


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 2,637.4
  - Median: 0.0
  - Stddev: 11,744.1
  - Non-zero count: 4,658,825.651954651


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1,595.0
  - Median: 0.0
  - Stddev: 3,522.1
  - Non-zero count: 13,038,488.209480286


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 18,921.8
  - Median: 10,696.1
  - Stddev: 26,418.8
  - Non-zero count: 44,716,496.43069458


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
  - Mean: 196.9
  - Median: 0.0
  - Stddev: 1,944.9
  - Non-zero count: 3,874,752.3265533447


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 12,126.7
  - Median: 0.0
  - Stddev: 23,698.4
  - Non-zero count: 26,435,584.852737427


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1,969.7
  - Median: 0.0
  - Stddev: 6,889.5
  - Non-zero count: 9,308,185.06049347


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 167.3
  - Median: -108.1
  - Stddev: 2,138.6
  - Non-zero count: 2,341,602.6748199463


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 118.5
  - Median: 0.0
  - Stddev: 758.1
  - Non-zero count: 21,283,443.14728546


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 2,698.6
  - Median: 0.0
  - Stddev: 11,885.6
  - Non-zero count: 4,791,502.459815979


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1,595.0
  - Median: 0.0
  - Stddev: 3,522.1
  - Non-zero count: 13,038,488.209480286


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12,337.1
  - Median: 12,500.0
  - Stddev: 1,156.1
  - Non-zero count: 66,697,791.92078781


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
  - Non-zero count: 67,391,291.62257004


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
  - Mean: 39,895.2
  - Median: 40,000.0
  - Stddev: 1,290.1
  - Non-zero count: 67,391,291.62257004


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12,337.1
  - Median: 12,500.0
  - Stddev: 1,156.1
  - Non-zero count: 66,697,791.92078781


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 67,391,291.62257004


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: -73.5
  - Median: -108.1
  - Stddev: 180.0
  - Non-zero count: 2,341,602.6748199463


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 962.8
  - Median: 1,000.0
  - Stddev: 136.4
  - Non-zero count: 66,950,506.42167282


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1,000.0
  - Median: 1,000.0
  - Stddev: 0.0
  - Non-zero count: 67,391,291.62257004


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 61.3
  - Median: 0.0
  - Stddev: 615.9
  - Non-zero count: 4,791,502.459815979


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3,582.0
  - Median: 0.0
  - Stddev: 5,441.5
  - Non-zero count: 25,966,563.207904816


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 306.7
  - Median: 0.0
  - Stddev: 2,782.6
  - Non-zero count: 11,677,600.179531097


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
  - Mean: 3,275.3
  - Median: 0.0
  - Stddev: 5,207.4
  - Non-zero count: 24,300,490.65465164


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
  - Mean: 1,414.9
  - Median: 0.0
  - Stddev: 3,272.5
  - Non-zero count: 14,025,426.393489838


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 1,360.2
  - Median: 0.0
  - Stddev: 3,105.0
  - Non-zero count: 14,177,869.307144165


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 8,676.5
  - Median: 8,127.2
  - Stddev: 8,240.4
  - Non-zero count: 20,445,139.659175873


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,200,738.961105347


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,673,870.674171448


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
  - Mean: -306.7
  - Median: 0.0
  - Stddev: 2,782.6
  - Non-zero count: 7,753,205.598026276


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 2,167.1
  - Median: 0.0
  - Stddev: 4,263.1
  - Non-zero count: 17,211,864.659236908


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1,915.1
  - Median: 0.0
  - Stddev: 4,002.5
  - Non-zero count: 15,449,282.256473541


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
  - Non-zero count: 748,063.1516265869


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
  - Non-zero count: 3,634,959.69190979


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 11,674.846572875977


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,617,873.531162262


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
  - Mean: 10.1
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 124,805.4274597168


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 10.1
  - Median: 0.0
  - Stddev: 383.7
  - Non-zero count: 124,805.4274597168


- maternity_allowance:
  - Type: float
  - Entity: person
  - Description: Maternity Allowance
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 12,233.358711242676

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
  - Mean: 1.2
  - Median: 0.0
  - Stddev: 106.5
  - Non-zero count: 12,233.358711242676


- ssmg:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant
  - Mean: 12.4
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 34,264.33116149902


- ssmg_reported:
  - Type: float
  - Entity: person
  - Description: Sure Start Maternity Grant (reported)
  - Mean: 12.4
  - Median: 0.0
  - Stddev: 496.2
  - Non-zero count: 34,264.33116149902


- PIP:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 180.3
  - Median: 0.0
  - Stddev: 952.6
  - Non-zero count: 2,329,971.6440734863


- PIP_DL:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 122.4
  - Median: 0.0
  - Stddev: 634.2
  - Non-zero count: 2,200,387.753555298


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 122.4
  - Median: 0.0
  - Stddev: 634.2
  - Non-zero count: 2,200,387.753555298


- PIP_M:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 57.9
  - Median: 0.0
  - Stddev: 373.6
  - Non-zero count: 1,654,362.7935256958


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 57.9
  - Median: 0.0
  - Stddev: 373.6
  - Non-zero count: 1,654,362.7935256958


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 9,793,415.792549133


- state_pension:
  - Type: float
  - Entity: person
  - Description: State Pension
  - Mean: 1,529.1
  - Median: 0.0
  - Stddev: 3,497.4
  - Non-zero count: 12,010,588.189529419


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 67,391,291.62257004


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1,529.1
  - Median: 0.0
  - Stddev: 3,497.4
  - Non-zero count: 12,010,588.189529419


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,391,291.62257004


- DLA:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 96.8
  - Median: 0.0
  - Stddev: 770.4
  - Non-zero count: 1,315,449.5515594482


- DLA_M:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 35.3
  - Median: 0.0
  - Stddev: 350.5
  - Non-zero count: 947,463.7344245911


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 35.3
  - Median: 0.0
  - Stddev: 350.5
  - Non-zero count: 947,463.7344245911


- DLA_SC:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 61.5
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 1,207,359.1027832031


- DLA_SC_middle_plus:
  - Type: bool
  - Entity: person
  - Description: Receives at least DLA (self-care) middle rate
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 1,207,359.1027832031


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 61.5
  - Median: 0.0
  - Stddev: 490.4
  - Non-zero count: 1,207,359.1027832031


- ESA_contrib:
  - Type: float
  - Entity: person
  - Description: ESA (contribution-based)
  - Mean: 26.2
  - Median: 0.0
  - Stddev: 513.4
  - Non-zero count: 283,487.2979736328


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 26.2
  - Median: 0.0
  - Stddev: 513.4
  - Non-zero count: 283,487.2979736328


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
  - Mean: 37.7
  - Median: 0.0
  - Stddev: 366.3
  - Non-zero count: 748,063.1516265869


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 37.7
  - Median: 0.0
  - Stddev: 366.3
  - Non-zero count: 748,063.1516265869


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 748,063.1516265869


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 5.3
  - Median: 0.0
  - Stddev: 206.8
  - Non-zero count: 104,604.42175292969


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 5.3
  - Median: 0.0
  - Stddev: 206.8
  - Non-zero count: 104,604.42175292969


- SDA:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 6,560.351013183594


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 77.1
  - Non-zero count: 6,560.351013183594


- access_fund:
  - Type: float
  - Entity: person
  - Description: Access Fund
  - Mean: 3.2
  - Median: 0.0
  - Stddev: 261.5
  - Non-zero count: 25,459.423095703125


- adult_ema:
  - Type: float
  - Entity: person
  - Description: Adult EMA
  - Mean: 3.8
  - Median: 0.0
  - Stddev: 143.3
  - Non-zero count: 54,217.2177734375


- child_ema:
  - Type: float
  - Entity: person
  - Description: Child EMA
  - Mean: 1.4
  - Median: 0.0
  - Stddev: 52.5
  - Non-zero count: 71,485.13821411133


- education_grants:
  - Type: float
  - Entity: person
  - Description: Education grants
  - Mean: 27.1
  - Median: 0.0
  - Stddev: 630.1
  - Non-zero count: 416,741.12115478516


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 180.6
  - Median: 0.0
  - Stddev: 1,334.3
  - Non-zero count: 1,227,586.0073699951


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: 35.5
  - Median: 0.0
  - Stddev: 710.7
  - Non-zero count: 542,195.1104736328


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 2.7
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 37,217.06997680664


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 2.7
  - Median: 0.0
  - Stddev: 192.3
  - Non-zero count: 37,217.06997680664


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 36,744.376457214355


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 2.0
  - Median: 0.0
  - Stddev: 79.9
  - Non-zero count: 36,744.376457214355


- winter_fuel_allowance:
  - Type: float
  - Entity: household
  - Description: Winter Fuel Allowance
  - Mean: 69.8
  - Median: 0.0
  - Stddev: 111.1
  - Non-zero count: 9,062,857.45313263


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 29.1
  - Median: 0.0
  - Stddev: 74.7
  - Non-zero count: 11,884,647.240867615


- AA:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 24.7
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 421,464.2433395386


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 24.7
  - Median: 0.0
  - Stddev: 486.0
  - Non-zero count: 421,464.2433395386


- CTC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit child element
  - Mean: 152.9
  - Median: 0.0
  - Stddev: 1,070.6
  - Non-zero count: 894,326.5


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.6
  - Median: 0.0
  - Stddev: 45.3
  - Non-zero count: 5,948.5


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 13.8
  - Median: 0.0
  - Stddev: 92.4
  - Non-zero count: 894,326.5


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 167.4
  - Median: 0.0
  - Stddev: 1,164.4
  - Non-zero count: 894,326.5


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 11.2
  - Non-zero count: 2,249.0


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 38.4
  - Median: 0.0
  - Stddev: 361.3
  - Non-zero count: 445,457.0


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 6.0
  - Median: 0.0
  - Stddev: 200.4
  - Non-zero count: 85,580.0


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 11.4
  - Median: 0.0
  - Stddev: 155.3
  - Non-zero count: 196,855.0


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 2.4
  - Median: 0.0
  - Stddev: 97.8
  - Non-zero count: 26,488.5


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 12.6
  - Median: 0.0
  - Stddev: 177.0
  - Non-zero count: 217,094.5


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 77.7
  - Median: 0.0
  - Stddev: 769.8
  - Non-zero count: 445,457.0


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 0.8
  - Median: 0.0
  - Stddev: 38.0
  - Non-zero count: 19,511.5


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 6.0
  - Median: 0.0
  - Stddev: 73.5
  - Non-zero count: 257,380.5


- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit
  - Mean: 130.2
  - Median: 0.0
  - Stddev: 1,009.8
  - Non-zero count: 789,613.0


- child_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit pre-minimum
  - Mean: 130.2
  - Median: 0.0
  - Stddev: 1,009.8
  - Non-zero count: 791,912.5


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 230.7
  - Median: 0.0
  - Stddev: 1,165.8
  - Non-zero count: 3,070,928.0785484314


- claims_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 935,411.0


- claims_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.1
  - Non-zero count: 517,887.0


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit child limit
  - Mean: 0.9
  - Median: 1.0
  - Stddev: 0.2
  - Non-zero count: 63,461,675.930454254


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 7,635,545.0


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 18,220,510.0


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 13,673,870.674171448


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 166.6
  - Median: 0.0
  - Stddev: 1,306.8
  - Non-zero count: 847,052.0


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 34,348.3
  - Median: 23,611.9
  - Stddev: 39,771.9
  - Non-zero count: 30,518,261.5


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 11,791.0
  - Median: 6,923.8
  - Stddev: 16,011.9
  - Non-zero count: 28,639,865.0


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 36.3
  - Median: 0.0
  - Stddev: 463.1
  - Non-zero count: 352,784.0


- working_tax_credit_pre_minimum:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit pre-minimum
  - Mean: 36.3
  - Median: 0.0
  - Stddev: 463.1
  - Non-zero count: 352,784.0


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 61.7
  - Median: 0.0
  - Stddev: 440.5
  - Non-zero count: 1,942,042.1648406982


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,870,822.0


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,035,774.0


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
  - Mean: 70.7
  - Median: 0.0
  - Stddev: 217.0
  - Non-zero count: 5,685,782.876205444


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 86.4
  - Median: 0.0
  - Stddev: 261.1
  - Non-zero count: 4,965,470.581733704


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
  - Mean: 396.9
  - Median: 0.0
  - Stddev: 1,103.3
  - Non-zero count: 5,288,426.796825409


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
  - Mean: 19.9
  - Median: 0.0
  - Stddev: 243.0
  - Non-zero count: 344,144.4315032959


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
  - Mean: 78.8
  - Median: 0.0
  - Stddev: 739.9
  - Non-zero count: 571,651.0648498535


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
  - Non-zero count: 4,791,502.459815979


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 15,087.4
  - Median: 0.0
  - Stddev: 25,921.2
  - Non-zero count: 31,417,656.899673462


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
  - Mean: 643.0
  - Median: 0.0
  - Stddev: 1,273.1
  - Non-zero count: 13,969,328.88710785


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 2.1
  - Median: 0.0
  - Stddev: 44.9
  - Non-zero count: 90,203.77499389648


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 80.2
  - Median: 0.0
  - Stddev: 216.5
  - Non-zero count: 5,962,167.951271057


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 3.8
  - Median: 0.0
  - Stddev: 103.2
  - Non-zero count: 53,140.720153808594


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
  - Mean: 14,013.4
  - Median: 15,870.4
  - Stddev: 3,172.6
  - Non-zero count: 67,391,291.62257004


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 5,721,868.792064667


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
  - Non-zero count: 10,809,377.56136322


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
  - Non-zero count: 3,634,959.69190979


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
  - Mean: 262.5
  - Median: 0.0
  - Stddev: 1,446.9
  - Non-zero count: 2,108,777.862876892


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
  - Mean: 114.6
  - Median: 0.0
  - Stddev: 578.8
  - Non-zero count: 2,295,370.804916382


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
  - Mean: 30.7
  - Median: 0.0
  - Stddev: 382.1
  - Non-zero count: 560,234.1896705627


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
  - Stddev: 0.2
  - Non-zero count: 1,864,896.4374542236


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 680,190.4249343872


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 5,333,132.49886322


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 4,370,469.120353699


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 1,033.5
  - Median: 0.0
  - Stddev: 3,068.7
  - Non-zero count: 5,333,132.49886322


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 623.3
  - Median: 0.0
  - Stddev: 2,659.0
  - Non-zero count: 4,370,469.120353699


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 14,806.5
  - Median: 13,731.9
  - Stddev: 5,659.6
  - Non-zero count: 28,047,312.09782791


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 17,296.3
  - Median: 16,026.9
  - Stddev: 5,495.2
  - Non-zero count: 28,047,312.09782791


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
  - Mean: 38.8
  - Median: 39.0
  - Stddev: 23.6
  - Non-zero count: 66,751,021.528842926


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 42,179,480.738918304


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 10,472,817.63017273


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 14,738,993.253479004


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1,982.2
  - Median: 1,982.0
  - Stddev: 23.6
  - Non-zero count: 67,391,291.62257004


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 78.5
  - Median: 100.0
  - Stddev: 41.2
  - Non-zero count: 67,391,291.62257004


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
  - Non-zero count: 13,798,282.16438675


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 42,858,882.5765419


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.8
  - Median: 1.0
  - Stddev: 0.4
  - Non-zero count: 52,652,298.369091034


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,331,204.723773956


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 35,950,989.61675644


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 14,738,993.253479004


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.1
  - Median: 0.0
  - Stddev: 0.3
  - Non-zero count: 8,721,980.768222809


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 34,187,105.44128418


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.4
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 28,047,312.09782791


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.5
  - Median: 0.0
  - Stddev: 0.5
  - Non-zero count: 33,204,186.18128586


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 3,144,465.147289276


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.2
  - Median: 0.0
  - Stddev: 0.4
  - Non-zero count: 11,594,528.106189728


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
  - Non-zero count: 54,317,751.52567673


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 67,391,291.62257004


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 9,517,139.8
  - Median: 9,477,111.0
  - Stddev: 5,543,055.9
  - Non-zero count: 67,391,291.62257004


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight (region-adjusted)
  - Mean: 1,583.7
  - Median: 1,216.1
  - Stddev: 791.8
  - Non-zero count: 67,391,291.62257004


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 984.8
  - Median: 834.0
  - Stddev: 429.3
  - Non-zero count: 67,391,291.62257004


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 9,517,119.4
  - Median: 9,477,101.0
  - Stddev: 5,543,020.5
  - Non-zero count: 67,391,291.62257004


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 9,517,001.7
  - Median: 9,477,001.0
  - Stddev: 5,543,019.5
  - Non-zero count: 67,391,291.62257004


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
  - Non-zero count: 28,047,312.09782791


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.1
  - Median: 1.0
  - Stddev: 0.3
  - Non-zero count: 28,047,312.09782791


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 9,501,636.4
  - Median: 9,439,095.8
  - Stddev: 5,545,521.5
  - Non-zero count: 28,047,312.09782791


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.3
  - Median: 1.0
  - Stddev: 0.5
  - Non-zero count: 28,047,312.09782791


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.4
  - Median: 2.0
  - Stddev: 1.3
  - Non-zero count: 28,047,312.09782791


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 1,707.3
  - Median: 1,266.7
  - Stddev: 844.6
  - Non-zero count: 28,047,312.09782791


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28,047,312.09782791


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
  - Mean: 2.8
  - Median: 3.0
  - Stddev: 1.0
  - Non-zero count: 28,047,312.09782791


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
  - Mean: 11.5
  - Median: 0.0
  - Stddev: 137.1
  - Non-zero count: 335,536.7046508789


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 213.3
  - Median: 0.0
  - Stddev: 2,539.1
  - Non-zero count: 335,536.7046508789


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.2
  - Non-zero count: 1,381,967.4725646973


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
  - Mean: 1.1
  - Median: 0.0
  - Stddev: 102.3
  - Non-zero count: 2,252.63427734375


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
  - Mean: 5,899.0
  - Median: 0.0
  - Stddev: 19,402.6
  - Non-zero count: 8,496,665.474945068


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 5,900.1
  - Median: 0.0
  - Stddev: 19,404.7
  - Non-zero count: 8,496,665.474945068


# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2020) 2018-19 Family Resources Survey, with simulation turned on.

<<<<<<< HEAD

- baseline_hbai_excluded_income:
  - Type: float
  - Entity: household
  - Description: HBAI-excluded income (baseline)
  - Mean: -1163.4261311584235
  - Median: -249.5087870279948
  - Stddev: 2671.602783203125
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
  - Mean: 1163.4261311584235
  - Median: 249.50878702799483
  - Stddev: 2671.602783203125
  - Non-zero count: 21397787.0


- baseline_corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations, baseline)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- corporate_sdlt:
  - Type: float
  - Entity: household
  - Description: Stamp Duty (corporations)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- sdlt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Stamp Duty
  - Mean: 0.8619471134743236
  - Median: 1.0
  - Stddev: 0.38597379928653364
  - Non-zero count: 24155043.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- sdlt_on_transactions:
  - Type: float
  - Entity: household
  - Description: SDLT on property transactions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- stamp_duty_land_tax:
  - Type: float
  - Entity: household
  - Description: Stamp Duty Land Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit
  - Mean: 314.8930726863979
  - Median: 0.0
  - Stddev: 716.9161987304688
  - Non-zero count: 7043208.0


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit (less tax charge)
  - Mean: 261.02690069351746
  - Median: 0.0
  - Stddev: 669.400634765625
  - Non-zero count: 6041335.0


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 154.51670582132456
  - Median: 0.0
  - Stddev: 537.6369018554688
  - Non-zero count: 6386423.667999268


- child_benefit_respective_amount:
  - Type: float
  - Entity: person
  - Description: Child Benefit (respective amount)
  - Mean: 183.4299327974457
  - Median: 0.0
  - Stddev: 381.4557800292969
  - Non-zero count: 13484571.868041992


- would_claim_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Benefit
  - Mean: 0.9199200720595514
  - Median: 1.0
  - Stddev: 0.27186765866293655
  - Non-zero count: 32417746.0


- baseline_business_rates:
  - Type: float
  - Entity: household
  - Description: Baseline business rates incidence
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- business_rates:
  - Type: float
  - Entity: household
  - Description: Business rates incidence
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- business_rates_change_incidence:
  - Type: float
  - Entity: household
  - Description: Business rates changes
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 164.438644692977
  - Median: 0.0
  - Stddev: 433.6144714355469
  - Non-zero count: 9184561.494934082


- meets_marriage_allowance_income_conditions:
  - Type: bool
  - Entity: person
  - Description: Meets Marriage Allowance income conditions
  - Mean: 0.9360369750268943
  - Median: 1.0
  - Stddev: 0.23650999693079475
  - Non-zero count: 62657397.34184265


- partners_unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Partner's unused personal allowance
  - Mean: 136.62931180809156
  - Median: 0.0
  - Stddev: 5850.37890625
  - Non-zero count: 14088647.33493042


- unused_personal_allowance:
  - Type: float
  - Entity: person
  - Description: Unused personal allowance
  - Mean: 5177.989169079567
  - Median: 1974.9235644510334
  - Stddev: 5622.69189453125
  - Non-zero count: 36127898.927215576


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 28.93287825026539
  - Median: 0.0
  - Stddev: 213.99942016601562
  - Non-zero count: 1443712.1872253418


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- shareholding:
  - Type: float
  - Entity: household
  - Description: Share in the corporate sector
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- main_residence_value:
  - Type: float
  - Entity: household
  - Description: Main residence value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- non_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Non-residential property value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- other_residential_property_value:
  - Type: float
  - Entity: household
  - Description: Other residence value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- property_wealth:
  - Type: float
  - Entity: household
  - Description: Property wealth
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- residential_property_value:
  - Type: float
  - Entity: household
  - Description: Residential property value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- corporate_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- household_land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- land_value:
  - Type: float
  - Entity: household
  - Description: Land value
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- owned_land:
  - Type: float
  - Entity: household
  - Description: Owned land
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- expected_lbtt:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- land_and_buildings_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land and Buildings Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- lbtt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land and Buildings Transaction Tax
  - Mean: 0.08940190183269506
  - Median: 0.0
  - Stddev: 0.3490154380400467
  - Non-zero count: 2505382.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- lbtt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LBTT on property transactions
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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- main_residential_property_purchased_is_first_home:
  - Type: bool
  - Entity: household
  - Description: Residential property bought is first home
  - Mean: 0.1969045894578721
  - Median: 0.0
  - Stddev: 0.39157297346490233
  - Non-zero count: 5518017.0


- non_residential_property_purchased:
  - Type: float
  - Entity: household
  - Description: Non-residential property bought
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Non-zero count: 28023811.0


- property_sale_rate:
  - Type: float
  - Entity: state
  - Description: Residential property sale rate
  - Mean: 0.05399347469210625
  - Median: 0.05399347469210625
  - Stddev: nan
  - Non-zero count: 1.0


- rent:
  - Type: float
  - Entity: household
  - Description: Rent
  - Mean: 2587.238890527773
  - Median: -52.0
  - Stddev: 4221.08203125
  - Non-zero count: 9879081.0


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
  - Mean: 236.0216659577236
  - Median: 0.0
  - Stddev: 2069.2353515625
  - Non-zero count: 23191038.490585327


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 16015.548467189203
  - Median: 6982.1376953125
  - Stddev: 25153.765625
  - Non-zero count: 39823576.73939514


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income (HBAI)
  - Mean: 32907.62056056647
  - Median: 27997.08155366104
  - Stddev: 22987.078125
  - Non-zero count: 27551667.0


- equiv_hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs (HBAI)
  - Mean: 29458.51201636299
  - Median: 25156.079277187637
  - Stddev: 23488.830078125
  - Non-zero count: 26823411.0


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 31763.712179706756
  - Median: 27099.24992688837
  - Stddev: 21857.298828125
  - Non-zero count: 27492245.0


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 18796.49244417136
  - Median: 12922.5869140625
  - Stddev: 25346.955078125
  - Non-zero count: 48571023.2759552


- hbai_household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income (HBAI definition)
  - Mean: 35530.36992170216
  - Median: 28751.689254602068
  - Stddev: 27567.7890625
  - Non-zero count: 27551667.0


- hbai_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 31379.21685894469
  - Median: 24948.973007272463
  - Stddev: 27194.150390625
  - Non-zero count: 26823411.0


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 887.9201239842093
  - Median: 0.0
  - Stddev: 1034.43212890625
  - Non-zero count: 32117315.76449585


- household_gross_income:
  - Type: float
  - Entity: household
  - Description: Household gross income
  - Mean: 44008.7635005187
  - Median: 32733.515835164097
  - Stddev: 40432.2734375
  - Non-zero count: 27663492.0


- household_market_income:
  - Type: float
  - Entity: household
  - Description: Household market income
  - Mean: 37631.39329630992
  - Median: 26751.874533621714
  - Stddev: 42722.984375
  - Non-zero count: 23967982.0


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 34366.94380809423
  - Median: 27805.73561809553
  - Stddev: 26450.712890625
  - Non-zero count: 27492245.0


- in_work:
  - Type: bool
  - Entity: person
  - Description: Worked some hours
  - Mean: 0.4798624551675097
  - Median: 0.0
  - Stddev: 0.49602900033758385
  - Non-zero count: 32121522.25289917


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
  - Mean: 77.30694152133891
  - Median: -1.0
  - Stddev: 1944.638427734375
  - Non-zero count: 247572.66751098633


- maintenance_income:
  - Type: float
  - Entity: person
  - Description: Maintenance payments
  - Mean: 35.5499960423806
  - Median: 0.0
  - Stddev: 512.8590698242188
  - Non-zero count: 758699.893737793


- market_income:
  - Type: float
  - Entity: person
  - Description: Market income
  - Mean: 16072.798309163285
  - Median: 7227.6373392290725
  - Stddev: 25574.83984375
  - Non-zero count: 41478373.99822998


- minimum_wage:
  - Type: float
  - Entity: person
  - Description: Minimum wage
  - Mean: 7.265339087722091
  - Median: 8.210000038146973
  - Stddev: 1.6121838092803955
  - Non-zero count: 66939019.51901245


- minimum_wage_category:
  - Type: Categorical
  - Entity: person
  - Description: Minimum wage category


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: -142.57142809390643
  - Median: -208.0
  - Stddev: 836.8568115234375
  - Non-zero count: 762582.2368774414


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income
  - Mean: 15288.091795521708
  - Median: 12674.846140078305
  - Stddev: 17086.978515625
  - Non-zero count: 48571023.2759552


- private_transfer_income:
  - Type: float
  - Entity: person
  - Description: Private transfers
  - Mean: -126.43259790388616
  - Median: -312.0
  - Stddev: 1242.374755859375
  - Non-zero count: 1193704.971069336


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
  - Mean: 17.075386999743618
  - Median: 0.0
  - Stddev: 19.89482307434082
  - Non-zero count: 32117315.76449585


- benunit_rent:
  - Type: float
  - Entity: benunit
  - Description: Rent
  - Mean: 2131.11778638959
  - Median: 0.0
  - Stddev: 3792.383056640625
  - Non-zero count: 10896012.0


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 112.0411069482166
  - Median: 0.0
  - Stddev: 881.93017578125
  - Non-zero count: 2497856.0710601807


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1427.7471050246736
  - Median: 1391.36376953125
  - Stddev: 737.1819458007812
  - Non-zero count: 26940280.0


- council_tax_band:
  - Type: Categorical
  - Entity: household
  - Description: Council Tax Band


- council_tax_less_benefit:
  - Type: float
  - Entity: household
  - Description: Council Tax (less CTB)
  - Mean: 1313.0192511871614
  - Median: 1351.9088134765625
  - Stddev: 845.73583984375
  - Non-zero count: 25319643.0


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
  - Mean: 2057.4581300850614
  - Median: -52.0
  - Stddev: 3968.763427734375
  - Non-zero count: 9879081.0


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 4151.153079144052
  - Median: 2987.284423828125
  - Stddev: 4296.388671875
  - Non-zero count: 27890292.0


- housing_service_charges:
  - Type: float
  - Entity: household
  - Description: Housing service charges
  - Mean: 66.26883210897633
  - Median: 0.0
  - Stddev: 339.31939697265625
  - Non-zero count: 2515150.0


- maintenance_expenses:
  - Type: float
  - Entity: person
  - Description: Maintenance expenses
  - Mean: 42.05511928023534
  - Median: 0.0
  - Stddev: 621.5613403320312
  - Non-zero count: 742590.1577453613


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
  - Mean: 2275.824089424156
  - Median: 0.0
  - Stddev: 5618.78857421875
  - Non-zero count: 7987042.0


- mortgage_interest_repayment:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 878.4846129758552
  - Median: -52.0
  - Stddev: 2093.639404296875
  - Non-zero count: 7964552.0


- occupational_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Occupational pension contributions
  - Mean: 471.63668715436575
  - Median: 0.0
  - Stddev: 1300.089599609375
  - Non-zero count: 18470174.480056763


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Rent liable
  - Mean: 1105.1028563340763
  - Median: 0.0
  - Stddev: 3035.36083984375
  - Non-zero count: 10078481.801437378


- private_pension_contributions:
  - Type: float
  - Entity: person
  - Description: Private pension contributions
  - Mean: 29.044929673625962
  - Median: 0.0
  - Stddev: 172.5945281982422
  - Non-zero count: 2094149.3220367432


- water_and_sewerage_charges:
  - Type: float
  - Entity: household
  - Description: Water and sewerage charges
  - Mean: 376.41656889320853
  - Median: 358.79998779296875
  - Stddev: 252.75648498535156
  - Non-zero count: 26722365.0


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.154636669973241
  - Median: 0.0
  - Stddev: 16.96702003479004
  - Non-zero count: 2497856.0710601807


- weekly_rent:
  - Type: float
  - Entity: household
  - Description: Weekly average rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- benunit_tax:
  - Type: float
  - Entity: benunit
  - Description: Benefit unit tax paid
  - Mean: 6532.102823171771
  - Median: 2295.6711116507317
  - Stddev: 13490.6767578125
  - Non-zero count: 24514575.0


- household_tax:
  - Type: float
  - Entity: household
  - Description: Total tax
  - Mean: 9641.8197092942
  - Median: 5022.849734017053
  - Stddev: 14914.052734375
  - Non-zero count: 27722133.0


- tax:
  - Type: float
  - Entity: person
  - Description: Total tax
  - Mean: 3508.40064856236
  - Median: 21.3304183235294
  - Stddev: 9046.5634765625
  - Non-zero count: 33627838.67700195


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: 3508.40064856236
  - Median: 21.3304183235294
  - Stddev: 9046.5634765625
  - Non-zero count: 33627838.67700195


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
  - Mean: 7.921734036076048
  - Median: 0.0
  - Stddev: 33.1730842590332
  - Non-zero count: 3399186.5978546143


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 7.921734036076048
  - Median: 0.0
  - Stddev: 33.1730842590332
  - Non-zero count: 3399186.5978546143


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Exempt from National Insurance
  - Mean: 0.3518837001619885
  - Median: 0.0
  - Stddev: 0.48921027982484017
  - Non-zero count: 23554749.873565674


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 930.990021229418
  - Median: 0.0
  - Stddev: 1557.903076171875
  - Non-zero count: 24724746.691879272


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1288.866399514135
  - Median: 0.0
  - Stddev: 2806.648193359375
  - Non-zero count: 24724746.691879272


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1288.866399514135
  - Median: 0.0
  - Stddev: 2806.648193359375
  - Non-zero count: 24724746.691879272


- total_NI:
  - Type: float
  - Entity: person
  - Description: National Insurance (total)
  - Mean: 2297.295505792205
  - Median: 0.0
  - Stddev: 4251.294921875
  - Non-zero count: 27836186.81790161


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 80.16023437417311
  - Median: 0.0
  - Stddev: 484.12127685546875
  - Non-zero count: 3137034.91696167


- employee_NI:
  - Type: float
  - Entity: person
  - Description: Employee-side National Insurance
  - Mean: 930.990021229418
  - Median: 0.0
  - Stddev: 1557.903076171875
  - Non-zero count: 24724746.691879272


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 1008.4291041118092
  - Median: 0.0
  - Stddev: 1595.98046875
  - Non-zero count: 27567736.43737793


- self_employed_NI:
  - Type: float
  - Entity: person
  - Description: Self-employed National Insurance
  - Mean: 88.08196843262705
  - Median: 0.0
  - Stddev: 507.18316650390625
  - Non-zero count: 3399186.5978546143


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 418.64139000195047
  - Median: 0.0
  - Stddev: 7837.92431640625
  - Non-zero count: 328374.33572387695


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 188.38862386147738
  - Median: 0.0
  - Stddev: 3528.70068359375
  - Non-zero count: 328374.33572387695


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.17723171520614558
  - Median: 0.0
  - Stddev: 18.239437103271484
  - Non-zero count: 7295.53271484375


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7372.805126783051
  - Median: 0.0
  - Stddev: 11172.712890625
  - Non-zero count: 30269692.63267517


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1474.5610427875965
  - Median: 0.0
  - Stddev: 2234.134521484375
  - Non-zero count: 30269692.63267517


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 9.660677219854984
  - Median: 0.0
  - Stddev: 402.9035949707031
  - Non-zero count: 98536.70007324219


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 16.577985889599997
  - Median: 0.0
  - Stddev: 418.107666015625
  - Non-zero count: 1220970.4629058838


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 18.601583043740956
  - Median: 0.0
  - Stddev: 439.98077392578125
  - Non-zero count: 721386.1418457031


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2449.7064268201393
  - Median: 0.0
  - Stddev: 7752.41015625
  - Non-zero count: 30269692.63267517


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 9738.809967492802
  - Median: 0.0
  - Stddev: 22411.185546875
  - Non-zero count: 30269692.63267517


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 1947.3634507077986
  - Median: 0.0
  - Stddev: 10566.54296875
  - Non-zero count: 4060569.3588409424


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 778.9453905292849
  - Median: 0.0
  - Stddev: 4225.7060546875
  - Non-zero count: 4060569.3588409424


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 1.796924148521434
  - Median: 0.0
  - Stddev: 195.0550537109375
  - Non-zero count: 21462.797485351562


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2499.97154650088
  - Median: 0.0
  - Stddev: 7923.9453125
  - Non-zero count: 30531591.09237671


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2471.0386696997116
  - Median: 0.0
  - Stddev: 7830.25048828125
  - Non-zero count: 30531591.09237671


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5370703740643783
  - Median: 1.0
  - Stddev: 0.4993882658360249
  - Non-zero count: 35950964.252578735


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.0816362421077014
  - Median: 0.0
  - Stddev: 0.33504804968833923
  - Non-zero count: 5464650.00390625


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 2.7306594016891803
  - Median: 0.0
  - Stddev: 121.77336883544922
  - Non-zero count: 115731.55752563477


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4988.20859859976
  - Median: 5000.0
  - Stddev: 191.11741638183594
  - Non-zero count: 66887122.95770264


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 101.67700699307146
  - Median: 0.0
  - Stddev: 1744.8206787109375
  - Non-zero count: 721386.1418457031


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 9852.121806627007
  - Median: 0.0
  - Stddev: 22642.181640625
  - Non-zero count: 30531591.09237671


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 11.634833083582564
  - Median: 0.0
  - Stddev: 477.5115661621094
  - Non-zero count: 115731.55752563477


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
  - Mean: 18.448759701583143
  - Median: 0.0
  - Stddev: 378.63031005859375
  - Non-zero count: 166600.64082336426


- SSP:
  - Type: float
  - Entity: person
  - Description: Statutory Sick Pay
  - Mean: 6.330732578674407
  - Median: 0.0
  - Stddev: 170.36541748046875
  - Non-zero count: 113481.8217010498


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17186.147405205305
  - Median: 10525.076435548966
  - Stddev: 24703.37109375
  - Non-zero count: 45230284.593948364


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
  - Mean: 24.779492271374636
  - Median: 0.0
  - Stddev: 416.91510009765625
  - Non-zero count: 278864.6945800781


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
  - Mean: 500.68161682366815
  - Median: 0.0
  - Stddev: 1319.6109619140625
  - Non-zero count: 19754630.06919861


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1742.029101255042
  - Median: 0.0
  - Stddev: 2059.193603515625
  - Non-zero count: 31402338.512573242


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 41.824441423885396
  - Median: 0.0
  - Stddev: 380.0399169921875
  - Non-zero count: 9431074.227493286


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 138.3549122312596
  - Median: 0.0
  - Stddev: 1876.1827392578125
  - Non-zero count: 3719918.471847534


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 12307.374723462304
  - Median: 0.0
  - Stddev: 22057.103515625
  - Non-zero count: 32948136.619430542


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: -142.57142809390643
  - Median: -208.0
  - Stddev: 836.8568115234375
  - Non-zero count: 762582.2368774414


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1611.9296672385178
  - Median: 0.0
  - Stddev: 6644.4736328125
  - Non-zero count: 9835008.620605469


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 172.5007483217983
  - Median: 0.0
  - Stddev: 1964.2427978515625
  - Non-zero count: 1644595.4401397705


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 55.84231255440554
  - Median: 0.0
  - Stddev: 566.6817016601562
  - Non-zero count: 22327380.87992859


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1578.9263148155771
  - Median: 0.0
  - Stddev: 11325.3271484375
  - Non-zero count: 4193736.715484619


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1419.686359613158
  - Median: 0.0
  - Stddev: 3399.83203125
  - Non-zero count: 12498182.855072021


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17625.42239124273
  - Median: 10618.434289464954
  - Stddev: 25462.03515625
  - Non-zero count: 45260133.50524902


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
  - Mean: 138.3549122312596
  - Median: 0.0
  - Stddev: 1876.1827392578125
  - Non-zero count: 3719918.471847534


- employment_income:
  - Type: float
  - Entity: person
  - Description: Employment income
  - Mean: 12769.235493277492
  - Median: 0.0
  - Stddev: 22854.279296875
  - Non-zero count: 27502644.837768555


- pension_income:
  - Type: float
  - Entity: person
  - Description: Pension income
  - Mean: 1611.9296672385178
  - Median: 0.0
  - Stddev: 6644.4736328125
  - Non-zero count: 9835008.620605469


- property_income:
  - Type: float
  - Entity: person
  - Description: Rental income
  - Mean: 96.73734149051195
  - Median: -104.21101379394531
  - Stddev: 2062.394287109375
  - Non-zero count: 2075915.686050415


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Savings interest income
  - Mean: 97.66675396275838
  - Median: 0.0
  - Stddev: 730.8330688476562
  - Non-zero count: 22327380.87992859


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Self-employment income
  - Mean: 1634.383307936686
  - Median: 0.0
  - Stddev: 11460.0390625
  - Non-zero count: 4333441.3693237305


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1419.686359613158
  - Median: 0.0
  - Stddev: 3399.83203125
  - Non-zero count: 12498182.855072021


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12376.675019511831
  - Median: 12500.0
  - Stddev: 1100.0692138671875
  - Non-zero count: 66441413.710754395


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
  - Mean: 2000.0
  - Median: 2000.0
  - Stddev: 0.0
  - Non-zero count: 66939019.51901245


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
  - Mean: 39946.27307834589
  - Median: 40000.0
  - Stddev: 1160.57177734375
  - Non-zero count: 66939019.51901245


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12376.675019511831
  - Median: 12500.0
  - Stddev: 1100.0692138671875
  - Non-zero count: 66441413.710754395


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1000.0
  - Median: 1000.0
  - Stddev: 0.0
  - Non-zero count: 66939019.51901245


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: -75.76340683128636
  - Median: -104.21101379394531
  - Stddev: 178.6578369140625
  - Non-zero count: 2075915.686050415


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 947.9679257014329
  - Median: 1000.0
  - Stddev: 203.40594482421875
  - Non-zero count: 65429667.65185547


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1000.0
  - Median: 1000.0
  - Stddev: 0.0
  - Non-zero count: 66939019.51901245


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 55.456993121108574
  - Median: 0.0
  - Stddev: 597.523193359375
  - Non-zero count: 4333441.3693237305


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 2590.7564245454682
  - Median: 0.0
  - Stddev: 5046.05859375
  - Non-zero count: 23097541.493423462


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 2.1754790418061236
  - Median: 0.0
  - Stddev: 2507.56787109375
  - Non-zero count: 8811536.010025024


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 364.2496460490749
  - Median: 0.0
  - Stddev: 1605.589111328125
  - Non-zero count: 3058263.0


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2588.580945774993
  - Median: 0.0
  - Stddev: 5125.93212890625
  - Non-zero count: 21850404.152633667


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 31.793419850137077
  - Median: 35.0
  - Stddev: 31.36081886291504
  - Non-zero count: 22380905.0


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
  - Mean: 0.4089037030974858
  - Median: 0.0
  - Stddev: 0.491968164818645
  - Non-zero count: 14409661.0


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 878.5180614785351
  - Median: 0.0
  - Stddev: 3115.12158203125
  - Non-zero count: 12511382.850631714


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 876.3425827441658
  - Median: 0.0
  - Stddev: 3104.987548828125
  - Non-zero count: 10751177.566177368


- household_benefits:
  - Type: float
  - Entity: household
  - Description: Benefits
  - Mean: 6066.112030650108
  - Median: 1788.800048828125
  - Stddev: 7467.91943359375
  - Non-zero count: 18066958.0


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.14833607413312047
  - Median: 0.0
  - Stddev: 0.36686190514836653
  - Non-zero count: 9929471.36177063


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.2014456137083397
  - Median: 0.0
  - Stddev: 0.4102249556804412
  - Non-zero count: 13484571.868041992


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.4837999097723247
  - Median: 0.0
  - Stddev: 0.4999099531700998
  - Non-zero count: 17048984.0


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.06944137105203552
  - Median: 0.0
  - Stddev: 0.26656652776956896
  - Non-zero count: 2447096.0


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5162000902276753
  - Median: 1.0
  - Stddev: 0.4999099531700998
  - Non-zero count: 18190758.0


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.46940556488750684
  - Median: 0.0
  - Stddev: 0.4977298838221244
  - Non-zero count: 16541731.0


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -2.1754790418061236
  - Median: 0.0
  - Stddev: 2507.56787109375
  - Non-zero count: 7373134.796417236


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1712.2383628397658
  - Median: 0.0
  - Stddev: 3888.78955078125
  - Non-zero count: 14398596.588851929


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1712.2383628397658
  - Median: 0.0
  - Stddev: 3888.78955078125
  - Non-zero count: 14398596.588851929


- benunit_has_carer:
  - Type: bool
  - Entity: benunit
  - Description: Benefit unit has a carer
  - Mean: 0.018670653150638844
  - Median: 0.0
  - Stddev: 0.14566112217446758
  - Non-zero count: 657949.0


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 36.40777364374575
  - Median: 0.0
  - Stddev: 284.046142578125
  - Non-zero count: 657949.0


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.010102400915290128
  - Median: 0.0
  - Stddev: 0.10671487700786582
  - Non-zero count: 676244.8120574951


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: Number of carers in the family
  - Mean: 0.018812424903678352
  - Median: 0.0
  - Stddev: 0.1483154747090402
  - Non-zero count: 657949.0


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 165.3213980322027
  - Median: 0.0
  - Stddev: 637.502197265625
  - Non-zero count: 2682027.0


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 0.2874294489588408
  - Median: 0.0
  - Stddev: 23.07422637939453
  - Non-zero count: 8557.0


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a disability
  - Mean: 0.04334649986001734
  - Median: 0.0
  - Stddev: 0.22247959311895188
  - Non-zero count: 2901572.2002105713


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.00013038315238859342
  - Median: 0.0
  - Stddev: 0.014413418520820459
  - Non-zero count: 8727.72038269043


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Has a severe disability
  - Mean: 0.017573796183878013
  - Median: 0.0
  - Stddev: 0.14540685254618094
  - Non-zero count: 1176372.6857757568


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.0792900810681304
  - Median: 0.0
  - Stddev: 0.3114640053342676
  - Non-zero count: 2682027.0


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.0006841991067925526
  - Median: 0.0
  - Stddev: 0.028898573901527055
  - Non-zero count: 24111.0


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.00024282243610069564
  - Median: 0.0
  - Stddev: 0.019893740353175038
  - Non-zero count: 8557.0


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
  - Mean: 0.031909966877737075
  - Median: 0.0
  - Stddev: 0.1997590970740198
  - Non-zero count: 1111908.0


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.00031595009974817636
  - Median: 0.0
  - Stddev: 0.020969382157258923
  - Non-zero count: 11134.0


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 162.23304011793945
  - Median: 0.0
  - Stddev: 1041.0634765625
  - Non-zero count: 1111908.0


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 13.545932229618732
  - Median: 0.0
  - Stddev: 383.7933654785156
  - Non-zero count: 173943.27313232422


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 13.545932229618732
  - Median: 0.0
  - Stddev: 383.7933654785156
  - Non-zero count: 173943.27313232422


- maternity_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Maternity allowance
  - Mean: 1.450526227907768
  - Median: 0.0
  - Stddev: 106.53939819335938
  - Non-zero count: 14244.229034423828


- PIP:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 135.04778867664626
  - Median: 0.0
  - Stddev: 952.6376342773438
  - Non-zero count: 1735327.4683532715


- PIP_DL:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 91.77267486801037
  - Median: 0.0
  - Stddev: 633.8505859375
  - Non-zero count: 1649134.5835113525


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 91.77267486801037
  - Median: 0.0
  - Stddev: 633.8505859375
  - Non-zero count: 1649134.5835113525


- PIP_M:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 43.27511468449866
  - Median: 0.0
  - Stddev: 373.4668884277344
  - Non-zero count: 1233987.7626190186


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 43.27511468449866
  - Median: 0.0
  - Stddev: 373.4668884277344
  - Non-zero count: 1233987.7626190186


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.1613662116714247
  - Median: 0.0
  - Stddev: 0.39623673527502545
  - Non-zero count: 10801695.992782593


- state_pension:
  - Type: float
  - Entity: person
  - Description: Income from the State Pension
  - Mean: 1355.5138891562924
  - Median: 0.0
  - Stddev: 3373.0751953125
  - Non-zero count: 11530381.907089233


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 66939019.51901245


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1355.5138891562924
  - Median: 0.0
  - Stddev: 3373.0751953125
  - Non-zero count: 11530381.907089233


- triple_lock_uprating:
  - Type: float
  - Entity: person
  - Description: Triple lock relative increase
  - Mean: 1.007855772972107
  - Median: 1.007855772972107
  - Stddev: 4.2081010178662837e-05
  - Non-zero count: 66939019.51901245


- DLA:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 82.17028811344112
  - Median: 0.0
  - Stddev: 770.2195434570312
  - Non-zero count: 1173002.9984588623


- DLA_M:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 32.763997210017564
  - Median: 0.0
  - Stddev: 350.33184814453125
  - Non-zero count: 845480.8999481201


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 32.763997210017564
  - Median: 0.0
  - Stddev: 350.33184814453125
  - Non-zero count: 845480.8999481201


- DLA_SC:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 49.4062914560634
  - Median: 0.0
  - Stddev: 490.4149169921875
  - Non-zero count: 1033985.3511199951


- DLA_SC_middle_plus:
  - Type: bool
  - Entity: person
  - Description: Receives at least DLA (self-care) middle rate
  - Mean: 0.015446676072485883
  - Median: 0.0
  - Stddev: 0.13806516717685316
  - Non-zero count: 1033985.3511199951


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 49.4062914560634
  - Median: 0.0
  - Stddev: 490.4149169921875
  - Non-zero count: 1033985.3511199951


- ESA_contrib:
  - Type: float
  - Entity: person
  - Description: ESA (contribution-based)
  - Mean: 27.92210783485922
  - Median: 0.0
  - Stddev: 513.2649536132812
  - Non-zero count: 296955.13931274414


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 27.92210783485922
  - Median: 0.0
  - Stddev: 513.2649536132812
  - Non-zero count: 296955.13931274414


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
  - Mean: 34.61129250881716
  - Median: 0.0
  - Stddev: 366.1167297363281
  - Non-zero count: 676244.8120574951


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 34.61129250881716
  - Median: 0.0
  - Stddev: 366.1167297363281
  - Non-zero count: 676244.8120574951


- receives_carers_allowance:
  - Type: bool
  - Entity: person
  - Description: Receives Carer's Allowance
  - Mean: 0.010102400915290128
  - Median: 0.0
  - Stddev: 0.10671487700786582
  - Non-zero count: 676244.8120574951


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 7.556481563606927
  - Median: 0.0
  - Stddev: 206.8660125732422
  - Non-zero count: 155098.71185302734


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 7.556481563606927
  - Median: 0.0
  - Stddev: 206.8660125732422
  - Non-zero count: 155098.71185302734


- SDA:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 0.9910351268707269
  - Median: 0.0
  - Stddev: 77.07752990722656
  - Non-zero count: 15415.105407714844


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.9910351268707269
  - Median: 0.0
  - Stddev: 77.07752990722656
  - Non-zero count: 15415.105407714844


- student_loans:
  - Type: float
  - Entity: person
  - Description: Student loans
  - Mean: 224.54891737915744
  - Median: -1.0
  - Stddev: 1334.06884765625
  - Non-zero count: 1469383.1759796143


- student_payments:
  - Type: float
  - Entity: person
  - Description: Student payments
  - Mean: -48.20293282322555
  - Median: -106.0
  - Stddev: 710.353271484375
  - Non-zero count: 580407.9644165039


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 4.271211061958754
  - Median: 0.0
  - Stddev: 192.32044982910156
  - Non-zero count: 59344.32162475586


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 4.271211061958754
  - Median: 0.0
  - Stddev: 192.32044982910156
  - Non-zero count: 59344.32162475586


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: JSA (contribution-based)
  - Mean: 1.6390701293691798
  - Median: 0.0
  - Stddev: 79.90789031982422
  - Non-zero count: 29444.367797851562


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 1.6390701293691798
  - Median: 0.0
  - Stddev: 79.90789031982422
  - Non-zero count: 29444.367797851562


- winter_fuel_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Winter fuel allowance
  - Mean: 29.562904152365256
  - Median: 0.0
  - Stddev: 74.6936264038086
  - Non-zero count: 11711646.841567993


- AA:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 48.969265938587675
  - Median: 0.0
  - Stddev: 485.9969177246094
  - Non-zero count: 830562.9617919922


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 48.969265938587675
  - Median: 0.0
  - Stddev: 485.9969177246094
  - Non-zero count: 830562.9617919922


- CTC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit child element
  - Mean: 410.3179875720997
  - Median: 0.0
  - Stddev: 1597.8712158203125
  - Non-zero count: 2582172.0


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 0.42813693130897496
  - Median: 0.0
  - Stddev: 49.74927520751953
  - Non-zero count: 4497.0


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 39.93456422013532
  - Median: 0.0
  - Stddev: 147.22927856445312
  - Non-zero count: 2582172.0


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Maximum Child Tax Credit
  - Mean: 450.7876679403612
  - Median: 0.0
  - Stddev: 1743.156982421875
  - Non-zero count: 2582172.0


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.10697921681719463
  - Median: 0.0
  - Stddev: 12.755636215209961
  - Non-zero count: 2772.0


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit basic element
  - Mean: 269.4905155662036
  - Median: 0.0
  - Stddev: 667.5195922851562
  - Non-zero count: 4845294.0


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit childcare element
  - Mean: 37.52262666517946
  - Median: 0.0
  - Stddev: 460.3104553222656
  - Non-zero count: 499687.0


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit couple element
  - Mean: 186.0949081295771
  - Median: 0.0
  - Stddev: 578.8170166015625
  - Non-zero count: 3262655.0


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit disabled element
  - Mean: 7.240843732624376
  - Median: 0.0
  - Stddev: 151.2201385498047
  - Non-zero count: 80621.0


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit lone parent element
  - Mean: 20.578409739776188
  - Median: 0.0
  - Stddev: 210.48147583007812
  - Non-zero count: 360785.0


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit maximum rate
  - Mean: 626.729412755392
  - Median: 0.0
  - Stddev: 1687.63330078125
  - Non-zero count: 4845294.0


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit severely disabled element
  - Mean: 2.317185806865442
  - Median: 0.0
  - Stddev: 60.67620849609375
  - Non-zero count: 59822.0


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit worker element
  - Mean: 103.48492335727089
  - Median: 0.0
  - Stddev: 265.55181884765625
  - Non-zero count: 4502200.0


- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Child Tax Credit
  - Mean: 170.74188349681938
  - Median: 0.0
  - Stddev: 1122.754150390625
  - Non-zero count: 1141145.0


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 156.1961643321299
  - Median: 0.0
  - Stddev: 1165.629638671875
  - Non-zero count: 1908532.5493011475


- claims_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates
  - Mean: 0.3370239203226857
  - Median: 0.0
  - Stddev: 0.4735074490310292
  - Non-zero count: 11876636.0


- claims_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates
  - Mean: 0.2652464084441935
  - Median: 0.0
  - Stddev: 0.44270948572407465
  - Non-zero count: 9347215.0


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Exemption from Child Tax Credit two-child limit
  - Mean: 0.9647482270093594
  - Median: 1.0
  - Stddev: 0.18500449480933656
  - Non-zero count: 64579300.39871216


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Child Tax Credit eligibility
  - Mean: 0.21667425941994695
  - Median: 0.0
  - Stddev: 0.42127591518038066
  - Non-zero count: 7635545.0


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Working Tax Credit eligibility
  - Mean: 0.5170443642862085
  - Median: 1.0
  - Stddev: 0.4999838241559579
  - Non-zero count: 18220510.0


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Child eligible for Child Tax Credit
  - Mean: 0.2014456137083397
  - Median: 0.0
  - Stddev: 0.4102249556804412
  - Non-zero count: 13484571.868041992


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Tax Credits
  - Mean: 215.3253576537501
  - Median: 0.0
  - Stddev: 1351.1290283203125
  - Non-zero count: 1410067.0


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 32784.34385077638
  - Median: 22440.579548239457
  - Stddev: 38294.3359375
  - Non-zero count: 30402804.0


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 11185.69686541145
  - Median: 6512.122546126995
  - Stddev: 15364.8115234375
  - Non-zero count: 28403756.0


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Working Tax Credit
  - Mean: 44.58347447583309
  - Median: 0.0
  - Stddev: 439.42657470703125
  - Non-zero count: 569880.0


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 36.78016997229851
  - Median: 0.0
  - Stddev: 440.1995849609375
  - Non-zero count: 1056705.4703826904


- would_claim_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Child Tax Credit
  - Mean: 0.8275463821500169
  - Median: 1.0
  - Stddev: 0.3766961581383781
  - Non-zero count: 29162521.0


- would_claim_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Working Tax Credit
  - Mean: 0.2652464084441935
  - Median: 0.0
  - Stddev: 0.44270948572407465
  - Non-zero count: 9347215.0


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: inf
  - Median: 13399.8798828125
  - Stddev: nan
  - Non-zero count: 35239742.0


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.08152786703148962
  - Median: 0.0
  - Stddev: 0.29685466461331833
  - Non-zero count: 2873021.0


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA rate
  - Mean: 8105.503219421859
  - Median: 8439.080078125
  - Stddev: 1814.366943359375
  - Non-zero count: 35239742.0


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 1.973590186897509
  - Median: 2.0
  - Stddev: 1.081260323524475
  - Non-zero count: 35239742.0


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 1717.7993485326353
  - Median: 0.0
  - Stddev: 2693.46875
  - Non-zero count: 10896012.0


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


- council_tax_benefit:
  - Type: float
  - Entity: benunit
  - Description: Council Tax Benefit
  - Mean: 91.23539247251016
  - Median: 0.0
  - Stddev: 291.9368591308594
  - Non-zero count: 3839052.0


- council_tax_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Council Tax Benefit (reported)
  - Mean: 49.004448004766886
  - Median: 0.0
  - Stddev: 217.170654296875
  - Non-zero count: 3916764.921508789


- HB_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Non-dependent deduction (individual)
  - Mean: 562.7499903421665
  - Median: 0.0
  - Stddev: 589.02099609375
  - Non-zero count: 32031464.654312134


- HB_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Non-dependent deductions
  - Mean: 388.0652107351703
  - Median: 0.0
  - Stddev: 748.3641967773438
  - Non-zero count: 7270795.0


- claims_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 0.32923722880831535
  - Median: 0.0
  - Stddev: 0.4708886593812739
  - Non-zero count: 11602235.0


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 157.24307508999985
  - Median: 0.0
  - Stddev: 916.9949951171875
  - Non-zero count: 1368201.0


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 1145.848727250069
  - Median: 0.0
  - Stddev: 3210.087158203125
  - Non-zero count: 6076929.0


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 25247.47416630031
  - Median: 19242.508114402597
  - Stddev: 23438.06640625
  - Non-zero count: 32101502.0


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.1724453317507262
  - Median: 0.0
  - Stddev: 0.38967020427238125
  - Non-zero count: 6076929.0


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 204.31902068427735
  - Median: 0.0
  - Stddev: 1103.3013916015625
  - Non-zero count: 2915624.53515625


- would_claim_HB:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Housing Benefit
  - Mean: 0.8077165831690822
  - Median: 1.0
  - Stddev: 0.3925432954023976
  - Non-zero count: 28463724.0


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 18.27452611438981
  - Median: 0.0
  - Stddev: 249.63267517089844
  - Non-zero count: 185510.0


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: JSA (income-based)
  - Mean: 15.222795635260958
  - Median: 0.0
  - Stddev: 223.9781951904297
  - Non-zero count: 158627.0


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 16.249995702830276
  - Median: 0.0
  - Stddev: 229.1869354248047
  - Non-zero count: 168894.0


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 25285.272973883923
  - Median: 19246.029291690367
  - Stddev: 24441.9609375
  - Non-zero count: 30587483.0


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligibility for income-based JSA
  - Mean: 0.021028020012178295
  - Median: 0.0
  - Stddev: 0.1324436080385611
  - Non-zero count: 741022.0


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 12.096171455058087
  - Median: 0.0
  - Stddev: 242.96307373046875
  - Non-zero count: 210169.91046142578


- claims_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim JSA based on survey response and take-up rates
  - Mean: 0.22708228113588347
  - Median: 0.0
  - Stddev: 0.4209379681483722
  - Non-zero count: 8002321.0


- would_claim_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based JSA
  - Mean: 0.5614444623345994
  - Median: 1.0
  - Stddev: 0.49588897032499973
  - Non-zero count: 19785158.0


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 116.86323374478488
  - Median: 0.0
  - Stddev: 1024.6025390625
  - Non-zero count: 628035.0


- ESA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: ESA (income) eligible
  - Mean: 0.017821782009641275
  - Median: 0.0
  - Stddev: 0.14391625994661672
  - Non-zero count: 628035.0


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 62.75225414083879
  - Median: 0.0
  - Stddev: 740.1025390625
  - Non-zero count: 647712.4231872559


- claims_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Claims ESA (income)
  - Mean: 0.006713074119555132
  - Median: 0.0
  - Stddev: 0.0905642604059077
  - Non-zero count: 236567.0


- would_claim_ESA_income:
  - Type: bool
  - Entity: benunit
  - Description: Would claim income-based ESA
  - Mean: 0.017821782009641275
  - Median: 0.0
  - Stddev: 0.14391625994661672
  - Non-zero count: 628035.0


- UC_LCWRA_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit limited capability for work-related-activity element
  - Mean: 325.6672956656359
  - Median: 0.0
  - Stddev: 1270.150634765625
  - Non-zero count: 2723708.0


- UC_MIF_applies:
  - Type: bool
  - Entity: person
  - Description: Minimum Income Floor applies
  - Mean: 0.06473715032669276
  - Median: 0.0
  - Stddev: 0.23907227822031465
  - Non-zero count: 4333441.3693237305


- UC_MIF_capped_earned_income:
  - Type: float
  - Entity: person
  - Description: Universal Credit gross earned income (incl. MIF)
  - Mean: 14465.065985243049
  - Median: -104.0
  - Stddev: 24992.673828125
  - Non-zero count: 32075799.0111084


- UC_carer_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit carer element
  - Mean: 35.89246407261461
  - Median: 0.0
  - Stddev: 280.04815673828125
  - Non-zero count: 657949.0


- UC_child_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit child element
  - Mean: 1180.1091184306279
  - Median: 0.0
  - Stddev: 2443.221923828125
  - Non-zero count: 8311716.0


- UC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit childcare element
  - Mean: 151.8639029985376
  - Median: 0.0
  - Stddev: 1029.9124755859375
  - Non-zero count: 1541416.0


- UC_childcare_work_condition:
  - Type: bool
  - Entity: benunit
  - Description: Meets Universal Credit childcare work condition
  - Mean: 0.5404914712485693
  - Median: 1.0
  - Stddev: 0.49992847516301825
  - Non-zero count: 19046780.0


- UC_claimant_type:
  - Type: Categorical
  - Entity: benunit
  - Description: UC claimant type


- UC_disability_elements:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit disability elements
  - Mean: 331.6852836882462
  - Median: 0.0
  - Stddev: 1307.529052734375
  - Non-zero count: 2723708.0


- UC_earned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit earned income (after disregards and tax)
  - Mean: 18780.949014073987
  - Median: 13252.014217414435
  - Stddev: 23849.615234375
  - Non-zero count: 22013849.0


- UC_housing_costs_element:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit housing costs element
  - Mean: 1003.632505690662
  - Median: 0.0
  - Stddev: 2673.6044921875
  - Non-zero count: 8136435.0


- UC_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 15340.238682382042
  - Median: 11183.290437410571
  - Stddev: 17019.83984375
  - Non-zero count: 29777389.0


- UC_individual_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit child element
  - Mean: 633.8091248109582
  - Median: 0.0
  - Stddev: 1263.4989013671875
  - Non-zero count: 13873354.862472534


- UC_individual_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit disabled child element
  - Mean: 1.1642044033640204
  - Median: 0.0
  - Stddev: 44.20281982421875
  - Non-zero count: 51496.51365661621


- UC_individual_non_dep_deduction:
  - Type: float
  - Entity: person
  - Description: Universal Credit non-dependent deduction (individual)
  - Mean: 439.45171679624514
  - Median: 0.0
  - Stddev: 452.8752136230469
  - Non-zero count: 32455610.93132019


- UC_individual_severely_disabled_child_element:
  - Type: float
  - Entity: person
  - Description: Universal Credit severely disabled child element
  - Mean: 2.0674860782740736
  - Median: 0.0
  - Stddev: 101.06744384765625
  - Non-zero count: 29414.807373046875


- UC_maximum_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit amount
  - Mean: 7438.863461144439
  - Median: 5986.68017578125
  - Stddev: 4837.759765625
  - Non-zero count: 35126890.0


- UC_maximum_childcare:
  - Type: float
  - Entity: benunit
  - Description: Maximum Universal Credit childcare element
  - Mean: 8433.631448630254
  - Median: 7756.2001953125
  - Stddev: 1884.7008056640625
  - Non-zero count: 35239742.0


- UC_minimum_income_floor:
  - Type: float
  - Entity: person
  - Description: Minimum Income Floor
  - Mean: 13222.917274344236
  - Median: 14942.2001953125
  - Stddev: 2934.35107421875
  - Non-zero count: 66939019.51901245


- UC_non_dep_deduction_exempt:
  - Type: bool
  - Entity: person
  - Description: Not expected to contribute to housing costs for Universal Credit
  - Mean: 0.07718933499767701
  - Median: 0.0
  - Stddev: 0.2876920637992598
  - Non-zero count: 5166978.402069092


- UC_non_dep_deductions:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit non-dependent deductions
  - Mean: 334.74375192647136
  - Median: 0.0
  - Stddev: 624.2067260742188
  - Non-zero count: 7723397.0


- UC_standard_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit standard allowance
  - Mean: 4735.6801848913365
  - Median: 3813.840087890625
  - Stddev: 1164.0791015625
  - Non-zero count: 35239742.0


- UC_unearned_income:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit unearned income
  - Mean: 3508.2409018189337
  - Median: 2.498209238052368
  - Stddev: 10897.169921875
  - Non-zero count: 18593152.0


- UC_work_allowance:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit work allowance
  - Mean: 1585.5546256836953
  - Median: 0.0
  - Stddev: 2546.999267578125
  - Non-zero count: 10518640.0


- claims_UC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Universal Credit
  - Mean: 0.17916623793670225
  - Median: 0.0
  - Stddev: 0.393270389515399
  - Non-zero count: 6313772.0


- is_UC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Universal Credit eligible
  - Mean: 0.7889775413225216
  - Median: 1.0
  - Stddev: 0.43380038938941456
  - Non-zero count: 27803365.0


- is_UC_work_allowance_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Family receives a Universal Credit Work Allowance
  - Mean: 0.2984879968758001
  - Median: 0.0
  - Stddev: 0.46765365639450296
  - Non-zero count: 10518640.0


- is_child_born_before_child_limit:
  - Type: bool
  - Entity: person
  - Description: Born before child limit (exempt)
  - Mean: 0.1689522418641324
  - Median: 0.0
  - Stddev: 0.3827328987763219
  - Non-zero count: 11309497.415924072


- is_in_startup_period:
  - Type: bool
  - Entity: person
  - Description: In a start-up period
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- limited_capability_for_WRA:
  - Type: bool
  - Entity: person
  - Description: Assessed to have limited capability for work-related activity
  - Mean: 0.04334649986001734
  - Median: 0.0
  - Stddev: 0.22247959311895188
  - Non-zero count: 2901572.2002105713


- num_UC_eligible_children:
  - Type: int
  - Entity: benunit
  - Description: Children eligible for Universal Credit
  - Mean: 0.38589195687073985
  - Median: 0.0
  - Stddev: 0.8099179001320962
  - Non-zero count: 8311716.0


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 631.7751092940397
  - Median: 0.0
  - Stddev: 2819.947998046875
  - Non-zero count: 2779324.0


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Universal Credit (reported)
  - Mean: 177.78617596587668
  - Median: 0.0
  - Stddev: 1446.98681640625
  - Non-zero count: 1373379.3212738037


- claims_PC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Pension Credit
  - Mean: 0.6346426429569206
  - Median: 1.0
  - Stddev: 0.48127326937373555
  - Non-zero count: 22364643.0


- guarantee_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 27862.704090081006
  - Median: 21450.895132486505
  - Stddev: 25343.359375
  - Non-zero count: 32535497.0


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit
  - Mean: 58.20340390252605
  - Median: 0.0
  - Stddev: 528.3330688476562
  - Non-zero count: 1102982.0


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 45.28318031525382
  - Median: 0.0
  - Stddev: 493.52215576171875
  - Non-zero count: 650002.0


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 1337.8482976519672
  - Median: 0.0
  - Stddev: 4004.49169921875
  - Non-zero count: 4406184.0


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 12.92022357477748
  - Median: 0.0
  - Stddev: 173.66802978515625
  - Non-zero count: 706527.0


- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Eligible for Pension Credit
  - Mean: 0.1960823095696898
  - Median: 0.0
  - Stddev: 0.4275223473307704
  - Non-zero count: 6909890.0


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 50.83380117653684
  - Median: 0.0
  - Stddev: 578.7509155273438
  - Non-zero count: 1151151.482559204


- savings_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Savings Credit
  - Mean: 27695.84899341102
  - Median: 21255.850761578236
  - Stddev: 25397.943359375
  - Non-zero count: 32470750.0


- would_claim_PC:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Pension Credit
  - Mean: 0.6346426429569206
  - Median: 1.0
  - Stddev: 0.48127326937373555
  - Non-zero count: 22364643.0


- claims_IS:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Income Support
  - Mean: 0.36699408866273764
  - Median: 0.0
  - Stddev: 0.48240720200675785
  - Non-zero count: 12932777.0


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 35.01699705171057
  - Median: 0.0
  - Stddev: 544.0704345703125
  - Non-zero count: 244866.0


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 80.21088782017131
  - Median: 0.0
  - Stddev: 913.9200439453125
  - Non-zero count: 424837.0


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 25285.272973883923
  - Median: 19246.029291690367
  - Stddev: 24441.9609375
  - Non-zero count: 30587483.0


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.032897431541922185
  - Median: 0.0
  - Stddev: 0.19280252055940614
  - Non-zero count: 1159297.0


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 21.06211868406385
  - Median: 0.0
  - Stddev: 382.022216796875
  - Non-zero count: 385600.9823913574


- would_claim_IS:
  - Type: bool
  - Entity: benunit
  - Description: Would claim Income Support
  - Mean: 0.8981577390663076
  - Median: 1.0
  - Stddev: 0.3025527785847836
  - Non-zero count: 31650847.0


- in_deep_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), after housing costs
  - Mean: 0.10039430397243258
  - Median: 0.0
  - Stddev: 0.2942301776984689
  - Non-zero count: 2813431.0


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.055788165285585174
  - Median: 0.0
  - Stddev: 0.22402580778799863
  - Non-zero count: 1563397.0


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.2223014921132604
  - Median: 0.0
  - Stddev: 0.41710372284243735
  - Non-zero count: 6229735.0


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.19767539825329253
  - Median: 0.0
  - Stddev: 0.4031384541435088
  - Non-zero count: 5539618.0


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 1632.283013428154
  - Median: 0.0
  - Stddev: 4192.33154296875
  - Non-zero count: 6229735.0


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 1126.765148062497
  - Median: 0.0
  - Stddev: 3114.61865234375
  - Non-zero count: 5539618.0


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 14331.512101062823
  - Median: 13556.5732421875
  - Stddev: 5587.47119140625
  - Non-zero count: 28023811.0


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 16799.262668331223
  - Median: 15822.294921875
  - Stddev: 5425.37451171875
  - Non-zero count: 28023811.0


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
  - Mean: 39.261013462662824
  - Median: 39.0
  - Stddev: 23.648786818116807
  - Non-zero count: 66205795.1907959


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6124304055763132
  - Median: 1.0
  - Stddev: 0.49555872207518314
  - Non-zero count: 40995490.872909546


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.17128312714128785
  - Median: 0.0
  - Stddev: 0.40539378928130615
  - Non-zero count: 11465524.59098816


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.21628646728239886
  - Median: 0.0
  - Stddev: 0.4183352569428601
  - Non-zero count: 14478004.055114746


- birth_year:
  - Type: int
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1980.7389865373373
  - Median: 1981.0
  - Stddev: 23.648786818116815
  - Non-zero count: 66939019.51901245


- child_index:
  - Type: int
  - Entity: person
  - Description: Child reference number
  - Mean: 78.70912690065151
  - Median: 100.0
  - Stddev: 41.170164546599146
  - Non-zero count: 66939019.51901245


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
  - Mean: 0.16278496177134408
  - Median: 0.0
  - Stddev: 0.37780549089136584
  - Non-zero count: 10896665.733413696


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6223473210461764
  - Median: 1.0
  - Stddev: 0.4937540588260953
  - Non-zero count: 41659319.47111511


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.7837135327176011
  - Median: 1.0
  - Stddev: 0.4183352569428601
  - Non-zero count: 52461015.463897705


- is_benunit_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Eldest child in the benefit unit
  - Mean: 0.11982461408587235
  - Median: 0.0
  - Stddev: 0.3304804204558162
  - Non-zero count: 8020942.181152344


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5370703740643783
  - Median: 1.0
  - Stddev: 0.4993882658360249
  - Non-zero count: 35950964.252578735


- is_child:
  - Type: bool
  - Entity: person
  - Description: Is a child
  - Mean: 0.21628646728239886
  - Median: 0.0
  - Stddev: 0.4183352569428601
  - Non-zero count: 14478004.055114746


- is_eldest_child:
  - Type: bool
  - Entity: person
  - Description: Is the eldest child
  - Mean: 0.12667467900348664
  - Median: 0.0
  - Stddev: 0.3351397621808881
  - Non-zero count: 8479478.810379028


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.5063018776517798
  - Median: 1.0
  - Stddev: 0.4996619537061989
  - Non-zero count: 33891351.27064514


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.42709313952404715
  - Median: 0.0
  - Stddev: 0.49680386165484386
  - Non-zero count: 28589196.0030365


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 0.4936981223482202
  - Median: 0.0
  - Stddev: 0.4996619537061989
  - Non-zero count: 33047668.24836731


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.048541240974316884
  - Median: 0.0
  - Stddev: 0.21590012114739232
  - Non-zero count: 3249303.0770568848


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.167745226308082
  - Median: 0.0
  - Stddev: 0.38177901330435976
  - Non-zero count: 11228700.978057861


- marital_status:
  - Type: Categorical
  - Entity: person
  - Description: Marital status


- over_16:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 16
  - Mean: 0.8094825115094362
  - Median: 1.0
  - Stddev: 0.4012150589689833
  - Non-zero count: 54185965.63822937


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 66939019.51901245


- person_id:
  - Type: int
  - Entity: person
  - Description: ID for the person
  - Mean: 959653.1925843834
  - Median: 959528.96713811
  - Stddev: 554308.7927831486
  - Non-zero count: 66939019.51901245


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight (region-adjusted)
  - Mean: 2042.6312240415673
  - Median: 1733.8243408203125
  - Stddev: 876.5885009765625
  - Non-zero count: 66939019.51901245


- raw_person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor
  - Mean: 2001.8910841153647
  - Median: 1699.0
  - Stddev: 858.664306640625
  - Non-zero count: 66939019.51901245


- person_benunit_id:
  - Type: float
  - Entity: person
  - Description: Person's benefit unit ID
  - Mean: 959651.1687663301
  - Median: 959527.96713811
  - Stddev: 554307.75
  - Non-zero count: 66939019.51901245


- person_household_id:
  - Type: float
  - Entity: person
  - Description: Person's household ID
  - Mean: 959639.5106735906
  - Median: 959517.96713811
  - Stddev: 554307.875
  - Non-zero count: 66939019.51901245


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
  - Mean: 1.0571633053463658
  - Median: 1.0
  - Stddev: 0.41218996047973633
  - Non-zero count: 28023811.0


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 1.0617462691963264
  - Median: 1.0
  - Stddev: 0.3428944945335388
  - Non-zero count: 28023811.0


- household_id:
  - Type: int
  - Entity: household
  - Description: ID for the household
  - Mean: 958404.5237316224
  - Median: 958313.664790494
  - Stddev: 554559.3671255285
  - Non-zero count: 28023811.0


- household_num_benunits:
  - Type: int
  - Entity: household
  - Description: Number of benefit units
  - Mean: 1.2574928513470205
  - Median: 1.0
  - Stddev: 0.520039498560071
  - Non-zero count: 28023811.0


- household_num_people:
  - Type: int
  - Entity: household
  - Description: Number of people
  - Mean: 2.3413876149821307
  - Median: 2.0
  - Stddev: 1.2539736242005226
  - Non-zero count: 28023811.0


- household_random_number:
  - Type: float
  - Entity: household
  - Description: Randomness
  - Mean: 0.4947288814453084
  - Median: 0.493000848577249
  - Stddev: 0.2904878258705139
  - Non-zero count: 28023811.0


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 1938.489101178994
  - Median: 1639.0
  - Stddev: 836.5348510742188
  - Non-zero count: 28023811.0


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 28023811.0


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
  - Mean: 2.775578025415601
  - Median: 3.0
  - Stddev: 1.0121163086230742
  - Non-zero count: 28023811.0


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
  - Mean: 959451.5537894687
  - Median: 961134.1430700447
  - Stddev: 553578.6907779488
  - Non-zero count: 35239742.0


- benunit_is_renting:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is renting
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- benunit_random_number:
  - Type: float
  - Entity: benunit
  - Description: Randomness
  - Mean: 0.49849895021690316
  - Median: 0.4991260703653097
  - Stddev: 0.290429949760437
  - Non-zero count: 35239742.0


- benunit_tenure_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Tenure type of the family's household


- benunit_weight:
  - Type: float
  - Entity: benunit
  - Description: Weight factor for the benefit unit
  - Mean: 2072.443922319295
  - Median: 1742.0
  - Stddev: 899.8135375976562
  - Non-zero count: 35239742.0


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 47.662654737937636
  - Median: 48.0
  - Stddev: 18.706043243408203
  - Non-zero count: 35239742.0


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: -inf
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7532484.0


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 35239742.0


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
  - Mean: 1.4592390035091631
  - Median: 1.0
  - Stddev: 0.5370500709057318
  - Non-zero count: 34684149.0


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.4027100425423092
  - Median: 0.0
  - Stddev: 0.8681971273016468
  - Non-zero count: 8311716.0


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 45.935262636145296
  - Median: 45.0
  - Stddev: 18.577775955200195
  - Non-zero count: 35239742.0


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: inf
  - Median: inf
  - Stddev: nan
  - Non-zero count: 34527020.0


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


- expected_ltt:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax (expected)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- land_transaction_tax:
  - Type: float
  - Entity: household
  - Description: Land Transaction Tax
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ltt_liable:
  - Type: bool
  - Entity: household
  - Description: Liable for Land Transaction Tax
  - Mean: 0.048650984692981264
  - Median: 0.0
  - Stddev: 0.19640362298074734
  - Non-zero count: 1363386.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- ltt_on_transactions:
  - Type: float
  - Entity: household
  - Description: LTT on property transactions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0

=======
* baseline_hbai_excluded_income:
  + Type: float
  + Entity: household
  + Description: HBAI-excluded income (baseline)
  + Mean: -1041.8182101039463
  + Median: 0.0
  + Stddev: 4469.97998046875
  + Non-zero count: 0.0

* hbai_excluded_income:
  + Type: float
  + Entity: household
  + Description: HBAI-excluded income
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* hbai_excluded_income_change:
  + Type: float
  + Entity: household
  + Description: Change in HBAI-excluded income
  + Mean: 1041.8182101039463
  + Median: 0.0
  + Stddev: 4469.97998046875
  + Non-zero count: 13565526.0

* baseline_corporate_sdlt:
  + Type: float
  + Entity: household
  + Description: Stamp Duty (corporations, baseline)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* corporate_sdlt:
  + Type: float
  + Entity: household
  + Description: Stamp Duty (corporations)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* corporate_sdlt_change_incidence:
  + Type: float
  + Entity: household
  + Description: Corporate Stamp Duty
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* expected_sdlt:
  + Type: float
  + Entity: household
  + Description: Stamp Duty (expected)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* sdlt_liable:
  + Type: bool
  + Entity: household
  + Description: Liable for Stamp Duty
  + Mean: 0.8619471134743236
  + Median: 1.0
  + Stddev: 0.38597379928653364
  + Non-zero count: 24155043.0

* sdlt_on_non_residential_property_rent:
  + Type: float
  + Entity: household
  + Description: Stamp Duty on non-residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* sdlt_on_non_residential_property_transactions:
  + Type: float
  + Entity: household
  + Description: Stamp Duty on non-residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* sdlt_on_rent:
  + Type: float
  + Entity: household
  + Description: SDLT on property rental
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* sdlt_on_residential_property_rent:
  + Type: float
  + Entity: household
  + Description: Stamp Duty on residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* sdlt_on_residential_property_transactions:
  + Type: float
  + Entity: household
  + Description: Stamp Duty on residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* sdlt_on_transactions:
  + Type: float
  + Entity: household
  + Description: SDLT on property transactions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* stamp_duty_land_tax:
  + Type: float
  + Entity: household
  + Description: Stamp Duty Land Tax
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* child_benefit:
  + Type: float
  + Entity: benunit
  + Description: Child Benefit
  + Mean: 314.8930726863979
  + Median: 0.0
  + Stddev: 716.9161987304688
  + Non-zero count: 7043208.0

* child_benefit_less_tax_charge:
  + Type: float
  + Entity: benunit
  + Description: Child Benefit (less tax charge)
  + Mean: 261.0269008413712
  + Median: 0.0
  + Stddev: 669.400634765625
  + Non-zero count: 6041335.0

* child_benefit_reported:
  + Type: float
  + Entity: person
  + Description: Child Benefit (reported amount)
  + Mean: 154.51670582132456
  + Median: 0.0
  + Stddev: 537.6369018554688
  + Non-zero count: 6386423.667999268

* child_benefit_respective_amount:
  + Type: float
  + Entity: person
  + Description: Child Benefit (respective amount)
  + Mean: 183.4299327974457
  + Median: 0.0
  + Stddev: 381.4557800292969
  + Non-zero count: 13484571.868041992

* would_claim_child_benefit:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Child Benefit
  + Mean: 0.9199200720595514
  + Median: 1.0
  + Stddev: 0.27186765866293655
  + Non-zero count: 32417746.0

* baseline_business_rates:
  + Type: float
  + Entity: household
  + Description: Baseline business rates incidence
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* business_rates:
  + Type: float
  + Entity: household
  + Description: Business rates incidence
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* business_rates_change_incidence:
  + Type: float
  + Entity: household
  + Description: Business rates changes
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* corporate_tax_incidence:
  + Type: float
  + Entity: household
  + Description: Corporate tax incidence
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* corporate_wealth:
  + Type: float
  + Entity: household
  + Description: Corporate wealth
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* shareholding:
  + Type: float
  + Entity: household
  + Description: Share in the corporate sector
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* main_residence_value:
  + Type: float
  + Entity: household
  + Description: Main residence value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* non_residential_property_value:
  + Type: float
  + Entity: household
  + Description: Non-residential property value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* other_residential_property_value:
  + Type: float
  + Entity: household
  + Description: Other residence value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* property_wealth:
  + Type: float
  + Entity: household
  + Description: Property wealth
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* residential_property_value:
  + Type: float
  + Entity: household
  + Description: Residential property value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* corporate_land_value:
  + Type: float
  + Entity: household
  + Description: Land value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* household_land_value:
  + Type: float
  + Entity: household
  + Description: Land value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* land_value:
  + Type: float
  + Entity: household
  + Description: Land value
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* owned_land:
  + Type: float
  + Entity: household
  + Description: Owned land
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* expected_lbtt:
  + Type: float
  + Entity: household
  + Description: Land and Buildings Transaction Tax (expected)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* land_and_buildings_transaction_tax:
  + Type: float
  + Entity: household
  + Description: Land and Buildings Transaction Tax
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lbtt_liable:
  + Type: bool
  + Entity: household
  + Description: Liable for Land and Buildings Transaction Tax
  + Mean: 0.08940190183269506
  + Median: 0.0
  + Stddev: 0.3490154380400467
  + Non-zero count: 2505382.0

* lbtt_on_non_residential_property_rent:
  + Type: float
  + Entity: household
  + Description: LBTT on non-residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lbtt_on_non_residential_property_transactions:
  + Type: float
  + Entity: household
  + Description: LBTT on non-residential property transactions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lbtt_on_rent:
  + Type: float
  + Entity: household
  + Description: LBTT on property rental
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lbtt_on_residential_property_rent:
  + Type: float
  + Entity: household
  + Description: LBTT on residential property rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lbtt_on_residential_property_transactions:
  + Type: float
  + Entity: household
  + Description: LBTT on residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lbtt_on_transactions:
  + Type: float
  + Entity: household
  + Description: LBTT on property transactions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* carbon_consumption:
  + Type: float
  + Entity: household
  + Description: Carbon consumption
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* alcohol_and_tobacco_consumption:
  + Type: float
  + Entity: household
  + Description: Alcohol and tobacco
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* clothing_and_footwear_consumption:
  + Type: float
  + Entity: household
  + Description: Clothing and footwear
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* communication_consumption:
  + Type: float
  + Entity: household
  + Description: Communication
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* education_consumption:
  + Type: float
  + Entity: household
  + Description: Education
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* food_and_non_alcoholic_beverages_consumption:
  + Type: float
  + Entity: household
  + Description: Food and alcoholic beverages
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* health_consumption:
  + Type: float
  + Entity: household
  + Description: Health
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* household_furnishings_consumption:
  + Type: float
  + Entity: household
  + Description: Household furnishings
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* housing_water_and_electricity_consumption:
  + Type: float
  + Entity: household
  + Description: Housing, water and electricity
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* miscellaneous_consumption:
  + Type: float
  + Entity: household
  + Description: Miscellaneous
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* recreation_consumption:
  + Type: float
  + Entity: household
  + Description: Recreation
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* restaurants_and_hotels_consumption:
  + Type: float
  + Entity: household
  + Description: Restaurants and hotels
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* transport_consumption:
  + Type: float
  + Entity: household
  + Description: Transport
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* additional_residential_property_purchased:
  + Type: float
  + Entity: household
  + Description: Residential property bought (additional)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* cumulative_non_residential_rent:
  + Type: float
  + Entity: household
  + Description: Cumulative non-residential rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* cumulative_residential_rent:
  + Type: float
  + Entity: household
  + Description: Cumulative residential rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* main_residential_property_purchased:
  + Type: float
  + Entity: household
  + Description: Residential property bought (main)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* main_residential_property_purchased_is_first_home:
  + Type: bool
  + Entity: household
  + Description: Residential property bought is first home
  + Mean: 0.1969045894578721
  + Median: 0.0
  + Stddev: 0.39157297346490233
  + Non-zero count: 5518017.0

* non_residential_property_purchased:
  + Type: float
  + Entity: household
  + Description: Non-residential property bought
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* non_residential_rent:
  + Type: float
  + Entity: household
  + Description: Non-residential rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* property_purchased:
  + Type: bool
  + Entity: household
  + Description: All property bought this year
  + Mean: 1.0
  + Median: 1.0
  + Stddev: 0.0
  + Non-zero count: 28023811.0

* property_sale_rate:
  + Type: float
  + Entity: state
  + Description: Residential property sale rate
  + Mean: 0.05399347469210625
  + Median: 0.05399347469210625
  + Stddev: nan
  + Non-zero count: 1.0

* rent:
  + Type: float
  + Entity: household
  + Description: Rent
  + Mean: 2587.238890527773
  + Median: -52.0
  + Stddev: 4221.08203125
  + Non-zero count: 9879081.0

* base_net_income:
  + Type: float
  + Entity: person
  + Description: Existing net income for the person to use as a base in microsimulation
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* capital_income:
  + Type: float
  + Entity: person
  + Description: Income from savings or dividends
  + Mean: 236.0216659577236
  + Median: 0.0
  + Stddev: 2069.2353515625
  + Non-zero count: 23191038.490585327

* earned_income:
  + Type: float
  + Entity: person
  + Description: Total earned income
  + Mean: 16015.548467189203
  + Median: 6982.1376953125
  + Stddev: 25153.765625
  + Non-zero count: 39823576.73939514

* employment_status:
  + Type: Categorical
  + Entity: person
  + Description: Employment status of the person

* equiv_hbai_household_net_income:
  + Type: float
  + Entity: household
  + Description: Equivalised household net income (HBAI)
  + Mean: 32940.16243299035
  + Median: 27990.282807884047
  + Stddev: 23121.50390625
  + Non-zero count: 27528718.0

* equiv_hbai_household_net_income_ahc:
  + Type: float
  + Entity: household
  + Description: Equivalised household net income, after housing costs (HBAI)
  + Mean: 29492.47590520277
  + Median: 25222.284309223156
  + Stddev: 23509.021484375
  + Non-zero count: 26911887.0

* equiv_household_net_income:
  + Type: float
  + Entity: household
  + Description: Equivalised household net income
  + Mean: 31990.78612610447
  + Median: 27461.119318641573
  + Stddev: 21769.8359375
  + Non-zero count: 27492245.0

* gross_income:
  + Type: float
  + Entity: person
  + Description: Gross income, including benefits
  + Mean: 18896.062196489773
  + Median: 13224.222533595286
  + Stddev: 25344.11328125
  + Non-zero count: 48574182.32209778

* hbai_household_net_income:
  + Type: float
  + Entity: household
  + Description: Household net income (HBAI definition)
  + Mean: 35600.99417337193
  + Median: 28725.006893677702
  + Stddev: 27947.359375
  + Non-zero count: 27528718.0

* hbai_household_net_income_ahc:
  + Type: float
  + Entity: household
  + Description: Household net income, after housing costs
  + Mean: 31449.84110679653
  + Median: 24866.352727557634
  + Stddev: 27529.150390625
  + Non-zero count: 26911887.0

* hours_worked:
  + Type: float
  + Entity: person
  + Description: Total amount of hours worked by this person
  + Mean: 887.9201239842093
  + Median: 0.0
  + Stddev: 1034.43212890625
  + Non-zero count: 32117315.76449585

* household_gross_income:
  + Type: float
  + Entity: household
  + Description: Household gross income
  + Mean: 44241.896710634894
  + Median: 32974.082001124676
  + Stddev: 40326.97265625
  + Non-zero count: 27664165.0

* household_market_income:
  + Type: float
  + Entity: household
  + Description: Household market income
  + Mean: 37631.39329630992
  + Median: 26751.874533621714
  + Stddev: 42722.984375
  + Non-zero count: 23967982.0

* household_net_income:
  + Type: float
  + Entity: household
  + Description: Household net income
  + Mean: 34559.17597469817
  + Median: 28021.101067243304
  + Stddev: 26356.55859375
  + Non-zero count: 27492245.0

* in_work:
  + Type: bool
  + Entity: person
  + Description: Worked some hours
  + Mean: 0.4798624551675097
  + Median: 0.0
  + Stddev: 0.49602900033758385
  + Non-zero count: 32121522.25289917

* is_apprentice:
  + Type: bool
  + Entity: person
  + Description: In an apprenticeship programme
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* lump_sum_income:
  + Type: float
  + Entity: person
  + Description: Lump sum income
  + Mean: 77.30694152133891
  + Median: -1.0
  + Stddev: 1944.638427734375
  + Non-zero count: 247572.66751098633

* maintenance_income:
  + Type: float
  + Entity: person
  + Description: Maintenance payments
  + Mean: 35.5499960423806
  + Median: 0.0
  + Stddev: 512.8590698242188
  + Non-zero count: 758699.893737793

* market_income:
  + Type: float
  + Entity: person
  + Description: Market income
  + Mean: 16072.798309163285
  + Median: 7227.6373392290725
  + Stddev: 25574.83984375
  + Non-zero count: 41478373.99822998

* minimum_wage:
  + Type: float
  + Entity: person
  + Description: Minimum wage
  + Mean: 7.265339087722091
  + Median: 8.210000038146973
  + Stddev: 1.6121838092803955
  + Non-zero count: 66939019.51901245

* minimum_wage_category:
  + Type: Categorical
  + Entity: person
  + Description: Minimum wage category

* miscellaneous_income:
  + Type: float
  + Entity: person
  + Description: Income from other sources
  + Mean: -142.57142809390643
  + Median: -208.0
  + Stddev: 836.8568115234375
  + Non-zero count: 762582.2368774414

* net_income:
  + Type: float
  + Entity: person
  + Description: Net income
  + Mean: 15370.192819846785
  + Median: 12898.025097814236
  + Stddev: 17092.869140625
  + Non-zero count: 48574182.32209778

* private_transfer_income:
  + Type: float
  + Entity: person
  + Description: Private transfers
  + Mean: -126.43259790388616
  + Median: -312.0
  + Stddev: 1242.374755859375
  + Non-zero count: 1193704.971069336

* sublet_income:
  + Type: float
  + Entity: person
  + Description: Income received from sublet agreements
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* weekly_hours:
  + Type: float
  + Entity: person
  + Description: Weekly hours
  + Mean: 17.075386999743618
  + Median: 0.0
  + Stddev: 19.89482307434082
  + Non-zero count: 32117315.76449585

* benunit_rent:
  + Type: float
  + Entity: benunit
  + Description: Rent
  + Mean: 2131.11778638959
  + Median: 0.0
  + Stddev: 3792.383056640625
  + Non-zero count: 10896012.0

* childcare_expenses:
  + Type: float
  + Entity: person
  + Description: Cost of childcare
  + Mean: 112.0411069482166
  + Median: 0.0
  + Stddev: 881.93017578125
  + Non-zero count: 2497856.0710601807

* council_tax:
  + Type: float
  + Entity: household
  + Description: Council Tax
  + Mean: 1427.7471050246736
  + Median: 1391.36376953125
  + Stddev: 737.1819458007812
  + Non-zero count: 26940280.0

* council_tax_band:
  + Type: Categorical
  + Entity: household
  + Description: Council Tax Band

* employer_pension_contributions:
  + Type: float
  + Entity: person
  + Description: Employer pension contributions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* family_rent:
  + Type: float
  + Entity: benunit
  + Description: Gross rent for the family
  + Mean: 2057.4581300850614
  + Median: -52.0
  + Stddev: 3968.763427734375
  + Non-zero count: 9879081.0

* housing_costs:
  + Type: float
  + Entity: household
  + Description: Total housing costs
  + Mean: 4151.153079144052
  + Median: 2987.284423828125
  + Stddev: 4296.388671875
  + Non-zero count: 27890292.0

* housing_service_charges:
  + Type: float
  + Entity: household
  + Description: Housing service charges
  + Mean: 66.26883210897633
  + Median: 0.0
  + Stddev: 339.31939697265625
  + Non-zero count: 2515150.0

* maintenance_expenses:
  + Type: float
  + Entity: person
  + Description: Maintenance expenses
  + Mean: 42.05511928023534
  + Median: 0.0
  + Stddev: 621.5613403320312
  + Non-zero count: 742590.1577453613

* mortgage:
  + Type: float
  + Entity: household
  + Description: Total mortgage payments
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* mortgage_capital_repayment:
  + Type: float
  + Entity: household
  + Description: Mortgage payments
  + Mean: 2275.824089424156
  + Median: 0.0
  + Stddev: 5618.78857421875
  + Non-zero count: 7987042.0

* mortgage_interest_repayment:
  + Type: float
  + Entity: household
  + Description: Total mortgage payments
  + Mean: 878.4846129758552
  + Median: -52.0
  + Stddev: 2093.639404296875
  + Non-zero count: 7964552.0

* occupational_pension_contributions:
  + Type: float
  + Entity: person
  + Description: Occupational pension contributions
  + Mean: 471.63668715436575
  + Median: 0.0
  + Stddev: 1300.089599609375
  + Non-zero count: 18470174.480056763

* personal_rent:
  + Type: float
  + Entity: person
  + Description: Rent liable
  + Mean: 1105.1028563340763
  + Median: 0.0
  + Stddev: 3035.36083984375
  + Non-zero count: 10078481.801437378

* private_pension_contributions:
  + Type: float
  + Entity: person
  + Description: Private pension contributions
  + Mean: 29.044929673625962
  + Median: 0.0
  + Stddev: 172.5945281982422
  + Non-zero count: 2094149.3220367432

* water_and_sewerage_charges:
  + Type: float
  + Entity: household
  + Description: Water and sewerage charges
  + Mean: 376.41656889320853
  + Median: 358.79998779296875
  + Stddev: 252.75648498535156
  + Non-zero count: 26722365.0

* weekly_childcare_expenses:
  + Type: float
  + Entity: person
  + Description: Average cost of childcare
  + Mean: 2.154636669973241
  + Median: 0.0
  + Stddev: 16.96702003479004
  + Non-zero count: 2497856.0710601807

* weekly_rent:
  + Type: float
  + Entity: household
  + Description: Weekly average rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* benunit_tax:
  + Type: float
  + Entity: benunit
  + Description: Benefit unit tax paid
  + Mean: 6564.628687958526
  + Median: 2374.049313798441
  + Stddev: 13486.2236328125
  + Non-zero count: 24700685.0

* household_tax:
  + Type: float
  + Entity: household
  + Description: Total tax
  + Mean: 9682.720751177972
  + Median: 5100.979012998791
  + Stddev: 14907.83984375
  + Non-zero count: 27723649.0

* tax:
  + Type: float
  + Entity: person
  + Description: Total tax
  + Mean: 3525.8693763207298
  + Median: 46.13752413743917
  + Stddev: 9046.7783203125
  + Non-zero count: 33827934.29107666

* tax_modelling:
  + Type: float
  + Entity: person
  + Description: Difference between reported and imputed tax liabilities
  + Mean: 3525.8693763207298
  + Median: 46.13752413743917
  + Stddev: 9046.7783203125
  + Non-zero count: 33827934.29107666

* tax_reported:
  + Type: float
  + Entity: person
  + Description: Reported tax paid
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* NI_class_2:
  + Type: float
  + Entity: person
  + Description: Class 2 Contributions for National Insurance for the year
  + Mean: 7.921734036076048
  + Median: 0.0
  + Stddev: 33.1730842590332
  + Non-zero count: 3399186.5978546143

* weekly_NI_class_2:
  + Type: float
  + Entity: person
  + Description: Class 2 Contributions for National Insurance
  + Mean: 7.921734036076048
  + Median: 0.0
  + Stddev: 33.1730842590332
  + Non-zero count: 3399186.5978546143

* NI_exempt:
  + Type: bool
  + Entity: person
  + Description: Whether is exempt from National Insurance
  + Mean: 0.3518837001619885
  + Median: 0.0
  + Stddev: 0.48921027982484017
  + Non-zero count: 23554749.873565674

* employee_NI_class_1:
  + Type: float
  + Entity: person
  + Description: Employee Class 1 Contributions for National Insurance
  + Mean: 930.990021229418
  + Median: 0.0
  + Stddev: 1557.903076171875
  + Non-zero count: 24724746.691879272

* employer_NI:
  + Type: float
  + Entity: person
  + Description: Employer contributions to National Insurance
  + Mean: 1288.866399514135
  + Median: 0.0
  + Stddev: 2806.648193359375
  + Non-zero count: 24724746.691879272

* employer_NI_class_1:
  + Type: float
  + Entity: person
  + Description: Employer Class 1 Contributions for National Insurance
  + Mean: 1288.866399514135
  + Median: 0.0
  + Stddev: 2806.648193359375
  + Non-zero count: 24724746.691879272

* total_NI:
  + Type: float
  + Entity: person
  + Description: NI (total)
  + Mean: 2297.295505792205
  + Median: 0.0
  + Stddev: 4251.294921875
  + Non-zero count: 27836186.81790161

* NI_class_4:
  + Type: float
  + Entity: person
  + Description: Class 4 Contributions for National Insurance for the year
  + Mean: 80.16023437417311
  + Median: 0.0
  + Stddev: 484.12127685546875
  + Non-zero count: 3137034.91696167

* employee_NI:
  + Type: float
  + Entity: person
  + Description: Employee-side NI
  + Mean: 930.990021229418
  + Median: 0.0
  + Stddev: 1557.903076171875
  + Non-zero count: 24724746.691879272

* national_insurance:
  + Type: float
  + Entity: person
  + Description: National Insurance
  + Mean: 1008.4291041118092
  + Median: 0.0
  + Stddev: 1595.98046875
  + Non-zero count: 27567736.43737793

* self_employed_NI:
  + Type: float
  + Entity: person
  + Description: Self-employed NI
  + Mean: 88.08196843262705
  + Median: 0.0
  + Stddev: 507.18316650390625
  + Non-zero count: 3399186.5978546143

* CB_HITC:
  + Type: float
  + Entity: person
  + Description: Child Benefit High-Income Tax Charge
  + Mean: 28.9328781664014
  + Median: 0.0
  + Stddev: 213.99942016601562
  + Non-zero count: 1443712.1872253418

* add_rate_earned_income:
  + Type: float
  + Entity: person
  + Description: Earned income (non-savings, non-dividend) at the additional rate
  + Mean: 418.64139000195047
  + Median: 0.0
  + Stddev: 7837.92431640625
  + Non-zero count: 328374.33572387695

* add_rate_earned_income_tax:
  + Type: float
  + Entity: person
  + Description: Income tax on earned income at the additional rate
  + Mean: 188.38862386147738
  + Median: 0.0
  + Stddev: 3528.70068359375
  + Non-zero count: 328374.33572387695

* add_rate_savings_income:
  + Type: float
  + Entity: person
  + Description: Savings income at the higher rate
  + Mean: 0.17723171520614558
  + Median: 0.0
  + Stddev: 18.239437103271484
  + Non-zero count: 7295.53271484375

* basic_rate_earned_income:
  + Type: float
  + Entity: person
  + Description: Earned income (non-savings, non-dividend) at the basic rate
  + Mean: 7460.0513440032255
  + Median: 0.0
  + Stddev: 11220.6259765625
  + Non-zero count: 30555503.245010376

* basic_rate_earned_income_tax:
  + Type: float
  + Entity: person
  + Description: Income tax on earned income at the basic rate
  + Mean: 1492.010286381717
  + Median: 0.0
  + Stddev: 2243.9375
  + Non-zero count: 30555503.245010376

* basic_rate_savings_income:
  + Type: float
  + Entity: person
  + Description: Savings income at the basic rate
  + Mean: 9.660677162685584
  + Median: 0.0
  + Stddev: 402.9035949707031
  + Non-zero count: 98536.70007324219

* basic_rate_savings_income_pre_starter:
  + Type: float
  + Entity: person
  + Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  + Mean: 16.57798587595027
  + Median: 0.0
  + Stddev: 418.107666015625
  + Non-zero count: 1220970.4629058838

* dividend_income_tax:
  + Type: float
  + Entity: person
  + Description: Income tax on dividend income
  + Mean: 18.60158314757755
  + Median: 0.0
  + Stddev: 439.98077392578125
  + Non-zero count: 721386.1418457031

* earned_income_tax:
  + Type: float
  + Entity: person
  + Description: Income tax on earned income
  + Mean: 2467.175154276781
  + Median: 0.0
  + Stddev: 7754.91943359375
  + Non-zero count: 30555503.245010376

* earned_taxable_income:
  + Type: float
  + Entity: person
  + Description: Non-savings, non-dividend income for Income Tax
  + Mean: 9826.056182404225
  + Median: 0.0
  + Stddev: 22425.236328125
  + Non-zero count: 30555503.245010376

* higher_rate_earned_income:
  + Type: float
  + Entity: person
  + Description: Earned income (non-savings, non-dividend) at the higher rate
  + Mean: 1947.3634483990488
  + Median: 0.0
  + Stddev: 10566.54296875
  + Non-zero count: 4060569.3588409424

* higher_rate_earned_income_tax:
  + Type: float
  + Entity: person
  + Description: Income tax on earned income at the higher rate
  + Mean: 778.945389637167
  + Median: 0.0
  + Stddev: 4225.7060546875
  + Non-zero count: 4060569.3588409424

* higher_rate_savings_income:
  + Type: float
  + Entity: person
  + Description: Savings income at the higher rate
  + Mean: 1.796924148521434
  + Median: 0.0
  + Stddev: 195.0550537109375
  + Non-zero count: 21462.797485351562

* income_tax:
  + Type: float
  + Entity: person
  + Description: Income Tax
  + Mean: 2517.4402742161283
  + Median: 0.0
  + Stddev: 7924.3564453125
  + Non-zero count: 30811229.739135742

* income_tax_pre_charges:
  + Type: float
  + Entity: person
  + Description: Income Tax before any tax charges
  + Mean: 2488.5073973991566
  + Median: 0.0
  + Stddev: 7831.2646484375
  + Non-zero count: 30811229.739135742

* is_higher_earner:
  + Type: bool
  + Entity: person
  + Description: Whether this person is the highest earner in a family
  + Mean: 0.5370703740643783
  + Median: 1.0
  + Stddev: 0.4993882658360249
  + Non-zero count: 35950964.252578735

* pays_scottish_income_tax:
  + Type: float
  + Entity: person
  + Description: Whether the individual pays Scottish Income Tax rates
  + Mean: 0.0816362421077014
  + Median: 0.0
  + Stddev: 0.33504804968833923
  + Non-zero count: 5464650.00390625

* savings_income_tax:
  + Type: float
  + Entity: person
  + Description: Income tax on savings income
  + Mean: 2.730659387396831
  + Median: 0.0
  + Stddev: 121.77336883544922
  + Non-zero count: 115731.55752563477

* savings_starter_rate_income:
  + Type: float
  + Entity: person
  + Description: Savings income which is tax-free under the starter rate
  + Mean: 4988.208598552544
  + Median: 5000.0
  + Stddev: 191.11741638183594
  + Non-zero count: 66887122.95770264

* tax_band:
  + Type: Categorical
  + Entity: person
  + Description: Tax band of the individual

* taxed_dividend_income:
  + Type: float
  + Entity: person
  + Description: Dividend income which is taxed
  + Mean: 101.67700699307146
  + Median: 0.0
  + Stddev: 1744.8206787109375
  + Non-zero count: 721386.1418457031

* taxed_income:
  + Type: float
  + Entity: person
  + Description: Income which is taxed
  + Mean: 9939.368021975113
  + Median: 0.0
  + Stddev: 22655.001953125
  + Non-zero count: 30811229.739135742

* taxed_savings_income:
  + Type: float
  + Entity: person
  + Description: Savings income which advances the person's income tax schedule
  + Mean: 11.634833026413164
  + Median: 0.0
  + Stddev: 477.5115661621094
  + Non-zero count: 115731.55752563477

* ISA_interest_income:
  + Type: float
  + Entity: person
  + Description: Amount received in interest from Individual Savings Accounts
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* SMP:
  + Type: float
  + Entity: person
  + Description: SMP
  + Mean: 18.448759701583143
  + Median: 0.0
  + Stddev: 378.63031005859375
  + Non-zero count: 166600.64082336426

* SSP:
  + Type: float
  + Entity: person
  + Description: Statutory Sick Pay
  + Mean: 6.330732578674407
  + Median: 0.0
  + Stddev: 170.36541748046875
  + Non-zero count: 113481.8217010498

* adjusted_net_income:
  + Type: float
  + Entity: person
  + Description: Taxable income after tax reliefs and before allowances
  + Mean: 17186.147405205305
  + Median: 10525.076435548966
  + Stddev: 24703.37109375
  + Non-zero count: 45230284.593948364

* capital_allowances:
  + Type: float
  + Entity: person
  + Description: Full relief from capital expenditure allowances
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* deficiency_relief:
  + Type: float
  + Entity: person
  + Description: Deficiency relief
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* employment_benefits:
  + Type: float
  + Entity: person
  + Description: Employment benefits
  + Mean: 24.779492271374636
  + Median: 0.0
  + Stddev: 416.91510009765625
  + Non-zero count: 278864.6945800781

* employment_deductions:
  + Type: float
  + Entity: person
  + Description: Deductions from employment income
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* employment_expenses:
  + Type: float
  + Entity: person
  + Description: Cost of expenses necessarily incurred and reimbursed by employment
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* loss_relief:
  + Type: float
  + Entity: person
  + Description: Tax relief from trading losses
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* pension_contributions:
  + Type: float
  + Entity: person
  + Description: Amount contributed to registered pension schemes paid by the individual (not the employer)
  + Mean: 500.68161682366815
  + Median: 0.0
  + Stddev: 1319.6109619140625
  + Non-zero count: 19754630.06919861

* pension_contributions_relief:
  + Type: float
  + Entity: person
  + Description: Reduction in taxable income from pension contributions
  + Mean: 1742.029101255042
  + Median: 0.0
  + Stddev: 2059.193603515625
  + Non-zero count: 31402338.512573242

* tax_free_savings_income:
  + Type: float
  + Entity: person
  + Description: Income from savings in tax-free accounts
  + Mean: 41.824441423885396
  + Median: 0.0
  + Stddev: 380.0399169921875
  + Non-zero count: 9431074.227493286

* taxable_dividend_income:
  + Type: float
  + Entity: person
  + Description: Amount of dividend income that is taxable
  + Mean: 138.3549122312596
  + Median: 0.0
  + Stddev: 1876.1827392578125
  + Non-zero count: 3719918.471847534

* taxable_employment_income:
  + Type: float
  + Entity: person
  + Description: Net taxable earnings
  + Mean: 12307.374723462304
  + Median: 0.0
  + Stddev: 22057.103515625
  + Non-zero count: 32948136.619430542

* taxable_miscellaneous_income:
  + Type: float
  + Entity: person
  + Description: Amount of miscellaneous income that is taxable
  + Mean: -142.57142809390643
  + Median: -208.0
  + Stddev: 836.8568115234375
  + Non-zero count: 762582.2368774414

* taxable_pension_income:
  + Type: float
  + Entity: person
  + Description: Amount of pension income that is taxable
  + Mean: 1611.9296672385178
  + Median: 0.0
  + Stddev: 6644.4736328125
  + Non-zero count: 9835008.620605469

* taxable_property_income:
  + Type: float
  + Entity: person
  + Description: Amount of property income that is taxable
  + Mean: 172.5007483217983
  + Median: 0.0
  + Stddev: 1964.2427978515625
  + Non-zero count: 1644595.4401397705

* taxable_savings_interest_income:
  + Type: float
  + Entity: person
  + Description: Amount of savings interest which is taxable
  + Mean: 55.84231255440554
  + Median: 0.0
  + Stddev: 566.6817016601562
  + Non-zero count: 22327380.87992859

* taxable_self_employment_income:
  + Type: float
  + Entity: person
  + Description: Amount of trading income that is taxable
  + Mean: 1578.9263148155771
  + Median: 0.0
  + Stddev: 11325.3271484375
  + Non-zero count: 4193736.715484619

* taxable_social_security_income:
  + Type: float
  + Entity: person
  + Description: Amount of social security income that is taxable
  + Mean: 1419.686359613158
  + Median: 0.0
  + Stddev: 3399.83203125
  + Non-zero count: 12498182.855072021

* total_income:
  + Type: float
  + Entity: person
  + Description: Taxable income after tax reliefs and before allowances
  + Mean: 17625.42239124273
  + Median: 10618.434289464954
  + Stddev: 25462.03515625
  + Non-zero count: 45260133.50524902

* trading_loss:
  + Type: float
  + Entity: person
  + Description: Loss from trading in the current year.
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* dividend_income:
  + Type: float
  + Entity: person
  + Description: Income from dividends
  + Mean: 138.3549122312596
  + Median: 0.0
  + Stddev: 1876.1827392578125
  + Non-zero count: 3719918.471847534

* employment_income:
  + Type: float
  + Entity: person
  + Description: Employment income
  + Mean: 12769.235493277492
  + Median: 0.0
  + Stddev: 22854.279296875
  + Non-zero count: 27502644.837768555

* pension_income:
  + Type: float
  + Entity: person
  + Description: Pension income
  + Mean: 1611.9296672385178
  + Median: 0.0
  + Stddev: 6644.4736328125
  + Non-zero count: 9835008.620605469

* property_income:
  + Type: float
  + Entity: person
  + Description: Rental income
  + Mean: 96.73734149051195
  + Median: -104.21101379394531
  + Stddev: 2062.394287109375
  + Non-zero count: 2075915.686050415

* savings_interest_income:
  + Type: float
  + Entity: person
  + Description: Savings interest income
  + Mean: 97.66675396275838
  + Median: 0.0
  + Stddev: 730.8330688476562
  + Non-zero count: 22327380.87992859

* self_employment_income:
  + Type: float
  + Entity: person
  + Description: Self-employment income
  + Mean: 1634.383307936686
  + Median: 0.0
  + Stddev: 11460.0390625
  + Non-zero count: 4333441.3693237305

* social_security_income:
  + Type: float
  + Entity: person
  + Description: Income from social security for tax purposes
  + Mean: 1419.686359613158
  + Median: 0.0
  + Stddev: 3399.83203125
  + Non-zero count: 12498182.855072021

* allowances:
  + Type: float
  + Entity: person
  + Description: Allowances applicable to adjusted net income
  + Mean: 12376.675019511831
  + Median: 12500.0
  + Stddev: 1100.0692138671875
  + Non-zero count: 66441413.710754395

* blind_persons_allowance:
  + Type: float
  + Entity: person
  + Description: Blind Person's Allowance for the year (not simulated)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* charitable_investment_gifts:
  + Type: float
  + Entity: person
  + Description: Gifts of qualifying investment or property to charities
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* covenanted_payments:
  + Type: float
  + Entity: person
  + Description: Covenanted payments to charities
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* dividend_allowance:
  + Type: float
  + Entity: person
  + Description: Dividend allowance for the person
  + Mean: 2000.0
  + Median: 2000.0
  + Stddev: 0.0
  + Non-zero count: 66939019.51901245

* gift_aid:
  + Type: float
  + Entity: person
  + Description: Expenditure under Gift Aid
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* marriage_allowance:
  + Type: float
  + Entity: person
  + Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* married_couples_allowance:
  + Type: float
  + Entity: person
  + Description: Married Couples' allowance for the year
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* married_couples_allowance_deduction:
  + Type: float
  + Entity: person
  + Description: Deduction from Married Couples' allowance for the year
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* other_deductions:
  + Type: float
  + Entity: person
  + Description: All other tax deductions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* pension_annual_allowance:
  + Type: float
  + Entity: person
  + Description: Annual Allowance for pension contributions
  + Mean: 39946.27307834589
  + Median: 40000.0
  + Stddev: 1160.57177734375
  + Non-zero count: 66939019.51901245

* personal_allowance:
  + Type: float
  + Entity: person
  + Description: Personal Allowance for the year
  + Mean: 12376.675019511831
  + Median: 12500.0
  + Stddev: 1100.0692138671875
  + Non-zero count: 66441413.710754395

* property_allowance:
  + Type: float
  + Entity: person
  + Description: Property Allowance for the year
  + Mean: 1000.0
  + Median: 1000.0
  + Stddev: 0.0
  + Non-zero count: 66939019.51901245

* property_allowance_deduction:
  + Type: float
  + Entity: person
  + Description: Deduction applied by the property allowance
  + Mean: -75.76340683128636
  + Median: -104.21101379394531
  + Stddev: 178.6578369140625
  + Non-zero count: 2075915.686050415

* savings_allowance:
  + Type: float
  + Entity: person
  + Description: Savings Allowance for the year
  + Mean: 947.9679257014329
  + Median: 1000.0
  + Stddev: 203.40594482421875
  + Non-zero count: 65429667.65185547

* trading_allowance:
  + Type: float
  + Entity: person
  + Description: Trading Allowance for the year
  + Mean: 1000.0
  + Median: 1000.0
  + Stddev: 0.0
  + Non-zero count: 66939019.51901245

* trading_allowance_deduction:
  + Type: float
  + Entity: person
  + Description: Deduction applied by the trading allowance
  + Mean: 55.456993121108574
  + Median: 0.0
  + Stddev: 597.523193359375
  + Non-zero count: 4333441.3693237305

* unused_personal_allowance:
  + Type: float
  + Entity: person
  + Description: Unused personal allowance
  + Mean: 5177.989169079567
  + Median: 1974.9235644510334
  + Stddev: 5622.69189453125
  + Non-zero count: 36127898.927215576

* benefits:
  + Type: float
  + Entity: person
  + Description: Total benefits
  + Mean: 2690.3261763939577
  + Median: 0.0
  + Stddev: 5308.61767578125
  + Non-zero count: 23105414.95500183

* benefits_modelling:
  + Type: float
  + Entity: person
  + Description: Difference between reported and simulated benefits for this person
  + Mean: 101.74523083721907
  + Median: 0.0
  + Stddev: 2610.544677734375
  + Non-zero count: 9712229.850524902

* benefits_premiums:
  + Type: float
  + Entity: benunit
  + Description: Value of premiums for disability and carer status
  + Mean: 457.2711789731099
  + Median: 0.0
  + Stddev: 1763.608154296875
  + Non-zero count: 3749694.0

* benefits_reported:
  + Type: float
  + Entity: person
  + Description: Total simulated
  + Mean: 2588.580945654614
  + Median: 0.0
  + Stddev: 5125.93212890625
  + Non-zero count: 21850404.152633667

* benunit_weekly_hours:
  + Type: float
  + Entity: benunit
  + Description: Average weekly hours worked by adults in the benefit unit
  + Mean: 31.793419850137077
  + Median: 35.0
  + Stddev: 31.36081886291504
  + Non-zero count: 22380905.0

* claims_all_entitled_benefits:
  + Type: bool
  + Entity: benunit
  + Description: Claims all eligible benefits
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* claims_legacy_benefits:
  + Type: bool
  + Entity: benunit
  + Description: Claims legacy benefits
  + Mean: 0.4089037030974858
  + Median: 0.0
  + Stddev: 0.491968164818645
  + Non-zero count: 14409661.0

* family_benefits:
  + Type: float
  + Entity: person
  + Description: Total simulated family benefits for this person
  + Mean: 933.3897580228252
  + Median: 0.0
  + Stddev: 3303.54150390625
  + Non-zero count: 12653225.29536438

* family_benefits_reported:
  + Type: float
  + Entity: person
  + Description: Total reported family benefits for this person
  + Mean: 876.3425826481408
  + Median: 0.0
  + Stddev: 3104.987548828125
  + Non-zero count: 10751177.566177368

* household_benefits:
  + Type: float
  + Entity: household
  + Description: Benefits
  + Mean: 6299.245240427361
  + Median: 1788.800048828125
  + Stddev: 7848.2421875
  + Non-zero count: 18076141.0

* is_QYP:
  + Type: bool
  + Entity: person
  + Description: Whether this person is a qualifying young person for benefits purposes
  + Mean: 0.14833607413312047
  + Median: 0.0
  + Stddev: 0.36686190514836653
  + Non-zero count: 9929471.36177063

* is_child_or_QYP:
  + Type: bool
  + Entity: person
  + Description: Whether this person is a child or qualifying young person for most benefits
  + Mean: 0.2014456137083397
  + Median: 0.0
  + Stddev: 0.4102249556804412
  + Non-zero count: 13484571.868041992

* is_couple:
  + Type: bool
  + Entity: benunit
  + Description: Whether this benefit unit contains a joint couple claimant for benefits
  + Mean: 0.4837999097723247
  + Median: 0.0
  + Stddev: 0.4999099531700998
  + Non-zero count: 17048984.0

* is_lone_parent:
  + Type: bool
  + Entity: benunit
  + Description: Whether the family is a lone parent family
  + Mean: 0.06944137105203552
  + Median: 0.0
  + Stddev: 0.26656652776956896
  + Non-zero count: 2447096.0

* is_single:
  + Type: bool
  + Entity: benunit
  + Description: Whether this benefit unit contains a single claimant for benefits
  + Mean: 0.5162000902276753
  + Median: 1.0
  + Stddev: 0.4999099531700998
  + Non-zero count: 18190758.0

* is_single_person:
  + Type: bool
  + Entity: benunit
  + Description: Whether the family is a single person
  + Mean: 0.46940556488750684
  + Median: 0.0
  + Stddev: 0.4977298838221244
  + Non-zero count: 16541731.0

* other_benefits:
  + Type: float
  + Entity: person
  + Description: Income from benefits not modelled or detailed in the model
  + Mean: -101.74523065690673
  + Median: 0.0
  + Stddev: 2610.544921875
  + Non-zero count: 7049094.832565308

* personal_benefits:
  + Type: float
  + Entity: person
  + Description: Value of personal, non-means-tested benefits
  + Mean: 1756.936417931819
  + Median: 0.0
  + Stddev: 4054.8916015625
  + Non-zero count: 14379546.283676147

* personal_benefits_reported:
  + Type: float
  + Entity: person
  + Description: Value of personal, non-means-tested benefits
  + Mean: 1712.2383628397658
  + Median: 0.0
  + Stddev: 3888.78955078125
  + Non-zero count: 14398596.588851929

* benunit_has_carer:
  + Type: bool
  + Entity: benunit
  + Description: Benefit unit has a carer
  + Mean: 0.018670653150638844
  + Median: 0.0
  + Stddev: 0.14566112217446758
  + Non-zero count: 657949.0

* carer_premium:
  + Type: float
  + Entity: benunit
  + Description: Carer premium
  + Mean: 36.40777364374575
  + Median: 0.0
  + Stddev: 284.046142578125
  + Non-zero count: 657949.0

* is_carer_for_benefits:
  + Type: bool
  + Entity: person
  + Description: Whether this person is a carer for benefits purposes
  + Mean: 0.010102400915290128
  + Median: 0.0
  + Stddev: 0.10671487700786582
  + Non-zero count: 676244.8120574951

* num_carers:
  + Type: int
  + Entity: benunit
  + Description: Number of carers in the family
  + Mean: 0.018812424903678352
  + Median: 0.0
  + Stddev: 0.1483154747090402
  + Non-zero count: 657949.0

* disability_premium:
  + Type: float
  + Entity: benunit
  + Description: Disability premium
  + Mean: 165.3213980322027
  + Median: 0.0
  + Stddev: 637.502197265625
  + Non-zero count: 2682027.0

* enhanced_disability_premium:
  + Type: float
  + Entity: benunit
  + Description: Enhanced disability premium
  + Mean: 0.2874294489588408
  + Median: 0.0
  + Stddev: 23.07422637939453
  + Non-zero count: 8557.0

* is_disabled_for_benefits:
  + Type: bool
  + Entity: person
  + Description: Has a disability
  + Mean: 0.04334649986001734
  + Median: 0.0
  + Stddev: 0.22247959311895188
  + Non-zero count: 2901572.2002105713

* is_enhanced_disabled_for_benefits:
  + Type: bool
  + Entity: person
  + Description: Whether meets the middle disability benefit entitlement
  + Mean: 0.00013038315238859342
  + Median: 0.0
  + Stddev: 0.014413418520820459
  + Non-zero count: 8727.72038269043

* is_severely_disabled_for_benefits:
  + Type: bool
  + Entity: person
  + Description: Has a severe disability
  + Mean: 0.029190550579878863
  + Median: 0.0
  + Stddev: 0.1854097664369735
  + Non-zero count: 1953986.8350372314

* num_disabled_adults:
  + Type: int
  + Entity: benunit
  + Description: Number of disabled adults
  + Mean: 0.0792900810681304
  + Median: 0.0
  + Stddev: 0.3114640053342676
  + Non-zero count: 2682027.0

* num_disabled_children:
  + Type: int
  + Entity: benunit
  + Description: Number of disabled children
  + Mean: 0.0006841991067925526
  + Median: 0.0
  + Stddev: 0.028898573901527055
  + Non-zero count: 24111.0

* num_enhanced_disabled_adults:
  + Type: int
  + Entity: benunit
  + Description: Number of enhanced disabled adults
  + Mean: 0.00024282243610069564
  + Median: 0.0
  + Stddev: 0.019893740353175038
  + Non-zero count: 8557.0

* num_enhanced_disabled_children:
  + Type: int
  + Entity: benunit
  + Description: Number of enhanced disabled children
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* num_severely_disabled_adults:
  + Type: int
  + Entity: benunit
  + Description: Number of severely disabled adults
  + Mean: 0.05354148166010977
  + Median: 0.0
  + Stddev: 0.26111002390157856
  + Non-zero count: 1815863.0

* num_severely_disabled_children:
  + Type: int
  + Entity: benunit
  + Description: Number of severely disabled children
  + Mean: 0.00031595009974817636
  + Median: 0.0
  + Stddev: 0.020969382157258923
  + Non-zero count: 11134.0

* severe_disability_premium:
  + Type: float
  + Entity: benunit
  + Description: Severe disability premium
  + Mean: 255.25457289328594
  + Median: 0.0
  + Stddev: 1282.4947509765625
  + Non-zero count: 1815863.0

* BSP:
  + Type: float
  + Entity: person
  + Description: Bereavement Support Payment
  + Mean: 13.545932229618732
  + Median: 0.0
  + Stddev: 383.7933654785156
  + Non-zero count: 173943.27313232422

* BSP_reported:
  + Type: float
  + Entity: person
  + Description: Bereavement Support Payment (reported)
  + Mean: 13.545932229618732
  + Median: 0.0
  + Stddev: 383.7933654785156
  + Non-zero count: 173943.27313232422

* maternity_allowance_reported:
  + Type: float
  + Entity: person
  + Description: Maternity allowance
  + Mean: 1.450526227907768
  + Median: 0.0
  + Stddev: 106.53939819335938
  + Non-zero count: 14244.229034423828

* PIP:
  + Type: float
  + Entity: person
  + Description: Personal Independence Payment
  + Mean: 135.04778867664626
  + Median: 0.0
  + Stddev: 952.6376342773438
  + Non-zero count: 1735327.4683532715

* PIP_DL:
  + Type: float
  + Entity: person
  + Description: Personal Independence Payment (Daily Living)
  + Mean: 91.77267486801037
  + Median: 0.0
  + Stddev: 633.8505859375
  + Non-zero count: 1649134.5835113525

* PIP_DL_reported:
  + Type: float
  + Entity: person
  + Description: Personal Independence Payment (Daily Living) (reported)
  + Mean: 91.77267486801037
  + Median: 0.0
  + Stddev: 633.8505859375
  + Non-zero count: 1649134.5835113525

* PIP_M:
  + Type: float
  + Entity: person
  + Description: Personal Independence Payment (Mobility)
  + Mean: 43.27511468449866
  + Median: 0.0
  + Stddev: 373.4668884277344
  + Non-zero count: 1233987.7626190186

* PIP_M_reported:
  + Type: float
  + Entity: person
  + Description: Personal Independence Payment (Mobility) (reported)
  + Mean: 43.27511468449866
  + Median: 0.0
  + Stddev: 373.4668884277344
  + Non-zero count: 1233987.7626190186

* is_SP_age:
  + Type: bool
  + Entity: person
  + Description: Whether the person is State Pension Age
  + Mean: 0.1613662116714247
  + Median: 0.0
  + Stddev: 0.39623673527502545
  + Non-zero count: 10801695.992782593

* state_pension:
  + Type: float
  + Entity: person
  + Description: Income from the State Pension
  + Mean: 1355.5138891562924
  + Median: 0.0
  + Stddev: 3373.0751953125
  + Non-zero count: 11530381.907089233

* state_pension_age:
  + Type: float
  + Entity: person
  + Description: State Pension age for this person
  + Mean: 66.0
  + Median: 66.0
  + Stddev: 0.0
  + Non-zero count: 66939019.51901245

* state_pension_reported:
  + Type: float
  + Entity: person
  + Description: Reported income from the State Pension
  + Mean: 1355.5138891562924
  + Median: 0.0
  + Stddev: 3373.0751953125
  + Non-zero count: 11530381.907089233

* triple_lock_uprating:
  + Type: float
  + Entity: person
  + Description: Triple lock relative increase
  + Mean: 1.007855772972107
  + Median: 1.007855772972107
  + Stddev: 4.2081010178662837e-05
  + Non-zero count: 66939019.51901245

* DLA:
  + Type: float
  + Entity: person
  + Description: Disability Living Allowance
  + Mean: 82.17028811344112
  + Median: 0.0
  + Stddev: 770.2195434570312
  + Non-zero count: 1173002.9984588623

* DLA_M:
  + Type: float
  + Entity: person
  + Description: Disability Living Allowance (mobility component)
  + Mean: 32.763997210017564
  + Median: 0.0
  + Stddev: 350.33184814453125
  + Non-zero count: 845480.8999481201

* DLA_M_reported:
  + Type: float
  + Entity: person
  + Description: Disability Living Allowance (mobility component) (reported)
  + Mean: 32.763997210017564
  + Median: 0.0
  + Stddev: 350.33184814453125
  + Non-zero count: 845480.8999481201

* DLA_SC:
  + Type: float
  + Entity: person
  + Description: Disability Living Allowance (self-care)
  + Mean: 49.4062914560634
  + Median: 0.0
  + Stddev: 490.4149169921875
  + Non-zero count: 1033985.3511199951

* DLA_SC_middle_plus:
  + Type: bool
  + Entity: person
  + Description: Receives at least DLA (self-care) middle rate
  + Mean: 0.015446676072485883
  + Median: 0.0
  + Stddev: 0.13806516717685316
  + Non-zero count: 1033985.3511199951

* DLA_SC_reported:
  + Type: float
  + Entity: person
  + Description: Disability Living Allowance (self-care) (reported)
  + Mean: 49.4062914560634
  + Median: 0.0
  + Stddev: 490.4149169921875
  + Non-zero count: 1033985.3511199951

* ESA_contrib:
  + Type: float
  + Entity: person
  + Description: ESA (contribution-based)
  + Mean: 27.92210783485922
  + Median: 0.0
  + Stddev: 513.2649536132812
  + Non-zero count: 296955.13931274414

* ESA_contrib_reported:
  + Type: float
  + Entity: person
  + Description: Employment and Support Allowance (contribution-based) (reported)
  + Mean: 27.92210783485922
  + Median: 0.0
  + Stddev: 513.2649536132812
  + Non-zero count: 296955.13931274414

* incapacity_benefit:
  + Type: float
  + Entity: person
  + Description: Incapacity Benefit
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* incapacity_benefit_reported:
  + Type: float
  + Entity: person
  + Description: Incapacity Benefit (reported)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* carers_allowance:
  + Type: float
  + Entity: person
  + Description: Carer's Allowance
  + Mean: 34.61129250881716
  + Median: 0.0
  + Stddev: 366.1167297363281
  + Non-zero count: 676244.8120574951

* carers_allowance_reported:
  + Type: float
  + Entity: person
  + Description: Carer's Allowance (reported)
  + Mean: 34.61129250881716
  + Median: 0.0
  + Stddev: 366.1167297363281
  + Non-zero count: 676244.8120574951

* receives_carers_allowance:
  + Type: bool
  + Entity: person
  + Description: Receives Carer's Allowance
  + Mean: 0.010102400915290128
  + Median: 0.0
  + Stddev: 0.10671487700786582
  + Non-zero count: 676244.8120574951

* IIDB:
  + Type: float
  + Entity: person
  + Description: Industrial Injuries Disablement Benefit
  + Mean: 7.556481563606927
  + Median: 0.0
  + Stddev: 206.8660125732422
  + Non-zero count: 155098.71185302734

* IIDB_reported:
  + Type: float
  + Entity: person
  + Description: Industrial Injuries Disablement Benefit (reported)
  + Mean: 7.556481563606927
  + Median: 0.0
  + Stddev: 206.8660125732422
  + Non-zero count: 155098.71185302734

* SDA:
  + Type: float
  + Entity: person
  + Description: Severe Disablement Allowance
  + Mean: 0.9910351268707269
  + Median: 0.0
  + Stddev: 77.07752990722656
  + Non-zero count: 15415.105407714844

* SDA_reported:
  + Type: float
  + Entity: person
  + Description: Severe Disablement Allowance (reported)
  + Mean: 0.9910351268707269
  + Median: 0.0
  + Stddev: 77.07752990722656
  + Non-zero count: 15415.105407714844

* student_loans:
  + Type: float
  + Entity: person
  + Description: Student loans
  + Mean: 224.54891737915744
  + Median: -1.0
  + Stddev: 1334.06884765625
  + Non-zero count: 1469383.1759796143

* student_payments:
  + Type: float
  + Entity: person
  + Description: Student payments
  + Mean: -48.20293282322555
  + Median: -106.0
  + Stddev: 710.353271484375
  + Non-zero count: 580407.9644165039

* AFCS:
  + Type: float
  + Entity: person
  + Description: Armed Forces Compensation Scheme
  + Mean: 48.969265938587675
  + Median: 0.0
  + Stddev: 485.9969177246094
  + Non-zero count: 830562.9617919922

* AFCS_reported:
  + Type: float
  + Entity: person
  + Description: Armed Forces Compensation Scheme (reported)
  + Mean: 4.271211061958754
  + Median: 0.0
  + Stddev: 192.32044982910156
  + Non-zero count: 59344.32162475586

* JSA_contrib:
  + Type: float
  + Entity: person
  + Description: JSA (contribution-based)
  + Mean: 1.6390701293691798
  + Median: 0.0
  + Stddev: 79.90789031982422
  + Non-zero count: 29444.367797851562

* JSA_contrib_reported:
  + Type: float
  + Entity: person
  + Description: Job Seeker's Allowance (contribution-based) (reported)
  + Mean: 1.6390701293691798
  + Median: 0.0
  + Stddev: 79.90789031982422
  + Non-zero count: 29444.367797851562

* winter_fuel_allowance_reported:
  + Type: float
  + Entity: person
  + Description: Winter fuel allowance
  + Mean: 29.562904152365256
  + Median: 0.0
  + Stddev: 74.6936264038086
  + Non-zero count: 11711646.841567993

* AA:
  + Type: float
  + Entity: person
  + Description: Attendance Allowance
  + Mean: 48.969265938587675
  + Median: 0.0
  + Stddev: 485.9969177246094
  + Non-zero count: 830562.9617919922

* AA_reported:
  + Type: float
  + Entity: person
  + Description: Attendance Allowance (reported)
  + Mean: 48.969265938587675
  + Median: 0.0
  + Stddev: 485.9969177246094
  + Non-zero count: 830562.9617919922

* CTC_child_element:
  + Type: float
  + Entity: benunit
  + Description: CTC entitlement from child elements
  + Mean: 410.3179875720997
  + Median: 0.0
  + Stddev: 1597.8712158203125
  + Non-zero count: 2582172.0

* CTC_disabled_child_element:
  + Type: float
  + Entity: benunit
  + Description: CTC entitlement from disabled child elements
  + Mean: 0.42813693130897496
  + Median: 0.0
  + Stddev: 49.74927520751953
  + Non-zero count: 4497.0

* CTC_family_element:
  + Type: float
  + Entity: benunit
  + Description: CTC entitlement in the Family Element
  + Mean: 39.93456422013532
  + Median: 0.0
  + Stddev: 147.22927856445312
  + Non-zero count: 2582172.0

* CTC_maximum_rate:
  + Type: float
  + Entity: benunit
  + Description: The maximum rate of CTC
  + Mean: 450.7876679403612
  + Median: 0.0
  + Stddev: 1743.156982421875
  + Non-zero count: 2582172.0

* CTC_severely_disabled_child_element:
  + Type: float
  + Entity: benunit
  + Description: CTC entitlement from severely disabled child elements
  + Mean: 0.10697921681719463
  + Median: 0.0
  + Stddev: 12.755636215209961
  + Non-zero count: 2772.0

* WTC_basic_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the basic element
  + Mean: 267.7196615117103
  + Median: 0.0
  + Stddev: 665.1113891601562
  + Non-zero count: 4813455.0

* WTC_childcare_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the childcare element
  + Mean: 37.52262666517946
  + Median: 0.0
  + Stddev: 460.3104553222656
  + Non-zero count: 499687.0

* WTC_couple_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the couple element
  + Mean: 185.65771281753425
  + Median: 0.0
  + Stddev: 577.9750366210938
  + Non-zero count: 3254990.0

* WTC_disabled_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the disabled element
  + Mean: 6.848089863995032
  + Median: 0.0
  + Stddev: 145.26614379882812
  + Non-zero count: 76248.0

* WTC_lone_parent_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the lone parent element
  + Mean: 20.578409739776188
  + Median: 0.0
  + Stddev: 210.48147583007812
  + Non-zero count: 360785.0

* WTC_maximum_rate:
  + Type: float
  + Entity: benunit
  + Description: The maximum rate of WTC
  + Mean: 621.5734987308228
  + Median: 0.0
  + Stddev: 1680.56640625
  + Non-zero count: 4813455.0

* WTC_severely_disabled_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the severely disabled element
  + Mean: 2.4274634303508806
  + Median: 0.0
  + Stddev: 62.65589141845703
  + Non-zero count: 62669.0

* WTC_worker_element:
  + Type: float
  + Entity: benunit
  + Description: WTC entitlement from the worker element
  + Mean: 100.81953494438183
  + Median: 0.0
  + Stddev: 262.25579833984375
  + Non-zero count: 4386240.0

* child_tax_credit:
  + Type: float
  + Entity: benunit
  + Description: Child Tax Credit
  + Mean: 170.66035423931234
  + Median: 0.0
  + Stddev: 1122.352294921875
  + Non-zero count: 1141145.0

* child_tax_credit_reported:
  + Type: float
  + Entity: person
  + Description: Working Tax Credit
  + Mean: 156.1961643321299
  + Median: 0.0
  + Stddev: 1165.629638671875
  + Non-zero count: 1908532.5493011475

* claims_CTC:
  + Type: bool
  + Entity: benunit
  + Description: Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates
  + Mean: 0.3370239203226857
  + Median: 0.0
  + Stddev: 0.4735074490310292
  + Non-zero count: 11876636.0

* claims_WTC:
  + Type: bool
  + Entity: benunit
  + Description: Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates
  + Mean: 0.2652464084441935
  + Median: 0.0
  + Stddev: 0.44270948572407465
  + Non-zero count: 9347215.0

* is_CTC_child_limit_exempt:
  + Type: bool
  + Entity: person
  + Description: Whether the person was born before 2017 and therefore exempt from the two-child limit for Child Tax Credit
  + Mean: 0.9647482270093594
  + Median: 1.0
  + Stddev: 0.18500449480933656
  + Non-zero count: 64579300.39871216

* is_CTC_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Whether the family is eligible for CTC
  + Mean: 0.21667425941994695
  + Median: 0.0
  + Stddev: 0.42127591518038066
  + Non-zero count: 7635545.0

* is_WTC_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Whether the family is eligible for WTC
  + Mean: 0.5131338362238861
  + Median: 1.0
  + Stddev: 0.49991690528801536
  + Non-zero count: 18082704.0

* is_child_for_CTC:
  + Type: bool
  + Entity: person
  + Description: Whether this person is a child conferring CTC eligibility
  + Mean: 0.2014456137083397
  + Median: 0.0
  + Stddev: 0.4102249556804412
  + Non-zero count: 13484571.868041992

* tax_credits:
  + Type: float
  + Entity: benunit
  + Description: Value of the Tax Credits (benefits) for this family
  + Mean: 213.93419190289057
  + Median: 0.0
  + Stddev: 1344.2196044921875
  + Non-zero count: 1402726.0

* tax_credits_applicable_income:
  + Type: float
  + Entity: benunit
  + Description: Applicable income for Tax Credits
  + Mean: 32784.34385077638
  + Median: 22440.579548239457
  + Stddev: 38294.3359375
  + Non-zero count: 30402804.0

* tax_credits_reduction:
  + Type: float
  + Entity: benunit
  + Description: Reduction in Tax Credits from means-tested income
  + Mean: 11185.625425653114
  + Median: 6512.122546126995
  + Stddev: 15364.8544921875
  + Non-zero count: 28403756.0

* working_tax_credit:
  + Type: float
  + Entity: benunit
  + Description: Working Tax Credit
  + Mean: 43.273837973411865
  + Median: 0.0
  + Stddev: 427.526611328125
  + Non-zero count: 562539.0

* working_tax_credit_reported:
  + Type: float
  + Entity: person
  + Description: Working Tax Credit
  + Mean: 36.78016997229851
  + Median: 0.0
  + Stddev: 440.1995849609375
  + Non-zero count: 1056705.4703826904

* would_claim_CTC:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Child Tax Credit
  + Mean: 0.8275463821500169
  + Median: 1.0
  + Stddev: 0.3766961581383781
  + Non-zero count: 29162521.0

* would_claim_WTC:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Working Tax Credit
  + Mean: 0.2652464084441935
  + Median: 0.0
  + Stddev: 0.44270948572407465
  + Non-zero count: 9347215.0

* benefit_cap:
  + Type: float
  + Entity: benunit
  + Description: Benefit cap for the family
  + Mean: inf
  + Median: 13399.8798828125
  + Stddev: nan
  + Non-zero count: 35239742.0

* is_benefit_cap_exempt:
  + Type: bool
  + Entity: benunit
  + Description: Whether exempt from the benefits cap
  + Mean: 0.08131955109092456
  + Median: 0.0
  + Stddev: 0.29655631625685097
  + Non-zero count: 2865680.0

* BRMA_LHA_rate:
  + Type: float
  + Entity: benunit
  + Description: LHA Rate
  + Mean: 8105.503219421859
  + Median: 8439.080078125
  + Stddev: 1814.366943359375
  + Non-zero count: 35239742.0

* LHA_allowed_bedrooms:
  + Type: float
  + Entity: benunit
  + Description: The number of bedrooms covered by LHA for the benefit unit
  + Mean: 1.973590186897509
  + Median: 2.0
  + Stddev: 1.081260323524475
  + Non-zero count: 35239742.0

* LHA_cap:
  + Type: float
  + Entity: benunit
  + Description: Applicable amount for LHA
  + Mean: 1717.7993485326353
  + Median: 0.0
  + Stddev: 2693.46875
  + Non-zero count: 10896012.0

* LHA_category:
  + Type: Categorical
  + Entity: benunit
  + Description: LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms

* LHA_eligible:
  + Type: float
  + Entity: benunit
  + Description: Whether eligible for Local Housing Allowance
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* council_tax_benefit:
  + Type: float
  + Entity: benunit
  + Description: CTB
  + Mean: 91.23539247251016
  + Median: 0.0
  + Stddev: 291.9368591308594
  + Non-zero count: 3839052.0

* council_tax_benefit_reported:
  + Type: float
  + Entity: person
  + Description: CTB (reported)
  + Mean: 49.004448004766886
  + Median: 0.0
  + Stddev: 217.170654296875
  + Non-zero count: 3916764.921508789

* HB_individual_non_dep_deduction:
  + Type: float
  + Entity: person
  + Description: Non-dependent deduction (individual)
  + Mean: 562.7499903421665
  + Median: 0.0
  + Stddev: 589.02099609375
  + Non-zero count: 32031464.654312134

* HB_non_dep_deductions:
  + Type: float
  + Entity: benunit
  + Description: Non-dependent deductions
  + Mean: 388.0652107351703
  + Median: 0.0
  + Stddev: 748.3641967773438
  + Non-zero count: 7270795.0

* claims_HB:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Housing Benefit
  + Mean: 0.32923722880831535
  + Median: 0.0
  + Stddev: 0.4708886593812739
  + Non-zero count: 11602235.0

* housing_benefit:
  + Type: float
  + Entity: benunit
  + Description: Housing Benefit
  + Mean: 156.85097549828208
  + Median: 0.0
  + Stddev: 916.163818359375
  + Non-zero count: 1366154.0

* housing_benefit_applicable_amount:
  + Type: float
  + Entity: benunit
  + Description: Applicable amount for Housing Benefit
  + Mean: 1171.4499503319253
  + Median: 0.0
  + Stddev: 3327.8779296875
  + Non-zero count: 6076929.0

* housing_benefit_applicable_income:
  + Type: float
  + Entity: benunit
  + Description: Relevant income for Housing Benefit means test
  + Mean: 25314.326084241122
  + Median: 19385.240019899287
  + Stddev: 23444.119140625
  + Non-zero count: 32104338.0

* housing_benefit_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Whether eligible for Housing Benefit
  + Mean: 0.1724453317507262
  + Median: 0.0
  + Stddev: 0.38967020427238125
  + Non-zero count: 6076929.0

* housing_benefit_reported:
  + Type: float
  + Entity: person
  + Description: Housing Benefit (reported amount)
  + Mean: 204.31902068427735
  + Median: 0.0
  + Stddev: 1103.3013916015625
  + Non-zero count: 2915624.53515625

* would_claim_HB:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Housing Benefit
  + Mean: 0.8077165831690822
  + Median: 1.0
  + Stddev: 0.3925432954023976
  + Non-zero count: 28463724.0

* JSA:
  + Type: float
  + Entity: benunit
  + Description: Amount of Jobseeker's Allowance for this family
  + Mean: 18.27452611438981
  + Median: 0.0
  + Stddev: 249.63267517089844
  + Non-zero count: 185510.0

* JSA_income:
  + Type: float
  + Entity: benunit
  + Description: JSA (income-based)
  + Mean: 15.222795635260958
  + Median: 0.0
  + Stddev: 223.9781951904297
  + Non-zero count: 158627.0

* JSA_income_applicable_amount:
  + Type: float
  + Entity: benunit
  + Description: Maximum amount of JSA (income-based)
  + Mean: 16.249995702830276
  + Median: 0.0
  + Stddev: 229.1869354248047
  + Non-zero count: 168894.0

* JSA_income_applicable_income:
  + Type: float
  + Entity: benunit
  + Description: Relevant income for JSA (income-based) means test
  + Mean: 25252.784256885025
  + Median: 19210.947115530762
  + Stddev: 24437.923828125
  + Non-zero count: 30587483.0

* JSA_income_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Whether eligible for JSA (income-based)
  + Mean: 0.02114930353349352
  + Median: 0.0
  + Stddev: 0.13308251767857088
  + Non-zero count: 745296.0

* JSA_income_reported:
  + Type: float
  + Entity: person
  + Description: JSA (income-based) (reported amount)
  + Mean: 12.096171455058087
  + Median: 0.0
  + Stddev: 242.96307373046875
  + Non-zero count: 210169.91046142578

* claims_JSA:
  + Type: bool
  + Entity: benunit
  + Description: Whether this family is imputed to claim JSA based on survey response and take-up rates
  + Mean: 0.22708228113588347
  + Median: 0.0
  + Stddev: 0.4209379681483722
  + Non-zero count: 8002321.0

* would_claim_JSA:
  + Type: bool
  + Entity: benunit
  + Description: Would claim income-based JSA
  + Mean: 0.5614444623345994
  + Median: 1.0
  + Stddev: 0.49588897032499973
  + Non-zero count: 19785158.0

* ESA_income:
  + Type: float
  + Entity: benunit
  + Description: ESA (income-based)
  + Mean: 116.86323374478488
  + Median: 0.0
  + Stddev: 1024.6025390625
  + Non-zero count: 628035.0

* ESA_income_eligible:
  + Type: bool
  + Entity: benunit
  + Description: ESA (income) eligible
  + Mean: 0.017821782009641275
  + Median: 0.0
  + Stddev: 0.14391625994661672
  + Non-zero count: 628035.0

* ESA_income_reported:
  + Type: float
  + Entity: person
  + Description: ESA (income-based) (reported amount)
  + Mean: 62.75225414083879
  + Median: 0.0
  + Stddev: 740.1025390625
  + Non-zero count: 647712.4231872559

* claims_ESA_income:
  + Type: bool
  + Entity: benunit
  + Description: Claims ESA (income)
  + Mean: 0.006713074119555132
  + Median: 0.0
  + Stddev: 0.0905642604059077
  + Non-zero count: 236567.0

* would_claim_ESA_income:
  + Type: bool
  + Entity: benunit
  + Description: Would claim income-based ESA
  + Mean: 0.017821782009641275
  + Median: 0.0
  + Stddev: 0.14391625994661672
  + Non-zero count: 628035.0

* UC_LCWRA_element:
  + Type: float
  + Entity: benunit
  + Description: Limited capability for work-related-activity element of UC
  + Mean: 325.6672956656359
  + Median: 0.0
  + Stddev: 1270.150634765625
  + Non-zero count: 2723708.0

* UC_MIF_applies:
  + Type: bool
  + Entity: person
  + Description: Minimum Income Floor applies
  + Mean: 0.06473715032669276
  + Median: 0.0
  + Stddev: 0.23907227822031465
  + Non-zero count: 4333441.3693237305

* UC_MIF_capped_earned_income:
  + Type: float
  + Entity: person
  + Description: UC gross earned income (incl. MIF)
  + Mean: 14465.065985243049
  + Median: -104.0
  + Stddev: 24992.673828125
  + Non-zero count: 32075799.0111084

* UC_carer_element:
  + Type: float
  + Entity: benunit
  + Description: UC carer element
  + Mean: 35.89246407261461
  + Median: 0.0
  + Stddev: 280.04815673828125
  + Non-zero count: 657949.0

* UC_child_element:
  + Type: float
  + Entity: benunit
  + Description: UC child element
  + Mean: 1180.1091184306279
  + Median: 0.0
  + Stddev: 2443.221923828125
  + Non-zero count: 8311716.0

* UC_childcare_element:
  + Type: float
  + Entity: benunit
  + Description: UC childcare element
  + Mean: 151.8639029985376
  + Median: 0.0
  + Stddev: 1029.9124755859375
  + Non-zero count: 1541416.0

* UC_childcare_work_condition:
  + Type: bool
  + Entity: benunit
  + Description: Meets childcare work condition
  + Mean: 0.5404914712485693
  + Median: 1.0
  + Stddev: 0.49992847516301825
  + Non-zero count: 19046780.0

* UC_claimant_type:
  + Type: Categorical
  + Entity: benunit
  + Description: UC claimant type

* UC_disability_elements:
  + Type: float
  + Entity: benunit
  + Description: UC disability element
  + Mean: 331.6852836882462
  + Median: 0.0
  + Stddev: 1307.529052734375
  + Non-zero count: 2723708.0

* UC_earned_income:
  + Type: float
  + Entity: benunit
  + Description: UC earned income (after disregards and tax)
  + Mean: 18797.659173483746
  + Median: 13257.144385182959
  + Stddev: 23842.9921875
  + Non-zero count: 22033453.0

* UC_housing_costs_element:
  + Type: float
  + Entity: benunit
  + Description: UC housing costs element
  + Mean: 1393.44550707917
  + Median: 0.0
  + Stddev: 2931.84130859375
  + Non-zero count: 10608042.0

* UC_income_reduction:
  + Type: float
  + Entity: benunit
  + Description: Reduction from income for Universal Credit
  + Mean: 15350.766082900447
  + Median: 11177.083268626806
  + Stddev: 17012.0703125
  + Non-zero count: 29794681.0

* UC_individual_child_element:
  + Type: float
  + Entity: person
  + Description: UC child element for this child
  + Mean: 633.8091248109582
  + Median: 0.0
  + Stddev: 1263.4989013671875
  + Non-zero count: 13873354.862472534

* UC_individual_disabled_child_element:
  + Type: float
  + Entity: person
  + Description: Disabled child element of UC
  + Mean: 1.1642044033640204
  + Median: 0.0
  + Stddev: 44.20281982421875
  + Non-zero count: 51496.51365661621

* UC_individual_non_dep_deduction:
  + Type: float
  + Entity: person
  + Description: Non-dependent deduction (individual)
  + Mean: 438.7171123921937
  + Median: 0.0
  + Stddev: 452.8185729980469
  + Non-zero count: 32401356.882888794

* UC_individual_severely_disabled_child_element:
  + Type: float
  + Entity: person
  + Description: Severely disabled element of UC
  + Mean: 2.0674860782740736
  + Median: 0.0
  + Stddev: 101.06744384765625
  + Non-zero count: 29414.807373046875

* UC_maximum_amount:
  + Type: float
  + Entity: benunit
  + Description: Maximum UC amount
  + Mean: 7828.676462913794
  + Median: 5986.68017578125
  + Stddev: 5054.94287109375
  + Non-zero count: 35126890.0

* UC_maximum_childcare:
  + Type: float
  + Entity: benunit
  + Description: Maximum UC childcare element
  + Mean: 8433.631448630254
  + Median: 7756.2001953125
  + Stddev: 1884.7008056640625
  + Non-zero count: 35239742.0

* UC_minimum_income_floor:
  + Type: float
  + Entity: person
  + Description: Minimum Income Floor
  + Mean: 13222.917274344236
  + Median: 14942.2001953125
  + Stddev: 2934.35107421875
  + Non-zero count: 66939019.51901245

* UC_non_dep_deduction_exempt:
  + Type: bool
  + Entity: person
  + Description: Not expected to contribute to housing costs
  + Mean: 0.07826409308603824
  + Median: 0.0
  + Stddev: 0.28965116359671966
  + Non-zero count: 5238921.654724121

* UC_non_dep_deductions:
  + Type: float
  + Entity: benunit
  + Description: Non-dependent deductions
  + Mean: 334.5848034041373
  + Median: 0.0
  + Stddev: 624.0811767578125
  + Non-zero count: 7718928.0

* UC_standard_allowance:
  + Type: float
  + Entity: benunit
  + Description: UC Standard Allowance
  + Mean: 4735.6801848913365
  + Median: 3813.840087890625
  + Stddev: 1164.0791015625
  + Non-zero count: 35239742.0

* UC_unearned_income:
  + Type: float
  + Entity: benunit
  + Description: UC unearned income
  + Mean: 3508.2409018189337
  + Median: 2.498209238052368
  + Stddev: 10897.169921875
  + Non-zero count: 18593152.0

* UC_work_allowance:
  + Type: float
  + Entity: benunit
  + Description: UC Work Allowance
  + Mean: 1497.2670317506866
  + Median: 0.0
  + Stddev: 2426.081298828125
  + Non-zero count: 10518640.0

* claims_UC:
  + Type: bool
  + Entity: benunit
  + Description: Would claim UC
  + Mean: 0.17926428065222497
  + Median: 0.0
  + Stddev: 0.3933739733013179
  + Non-zero count: 6317227.0

* is_UC_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Universal Credit eligible
  + Mean: 0.7889775413225216
  + Median: 1.0
  + Stddev: 0.43380038938941456
  + Non-zero count: 27803365.0

* is_UC_work_allowance_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Family receives a Work Allowance
  + Mean: 0.2984879968758001
  + Median: 0.0
  + Stddev: 0.46765365639450296
  + Non-zero count: 10518640.0

* is_child_born_before_child_limit:
  + Type: bool
  + Entity: person
  + Description: Born before child limit (exempt)
  + Mean: 0.1689522418641324
  + Median: 0.0
  + Stddev: 0.3827328987763219
  + Non-zero count: 11309497.415924072

* is_in_startup_period:
  + Type: bool
  + Entity: person
  + Description: In a start-up period
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* limited_capability_for_WRA:
  + Type: bool
  + Entity: person
  + Description: Assessed to have limited capability for work-related activity
  + Mean: 0.04334649986001734
  + Median: 0.0
  + Stddev: 0.22247959311895188
  + Non-zero count: 2901572.2002105713

* num_UC_eligible_children:
  + Type: int
  + Entity: benunit
  + Description: Number of UC-eligible children
  + Mean: 0.38589195687073985
  + Median: 0.0
  + Stddev: 0.8099179001320962
  + Non-zero count: 8311716.0

* universal_credit:
  + Type: float
  + Entity: benunit
  + Description: Universal Credit
  + Mean: 724.6730037316178
  + Median: 0.0
  + Stddev: 3126.525634765625
  + Non-zero count: 2880945.0

* universal_credit_reported:
  + Type: float
  + Entity: person
  + Description: Universal Credit (reported)
  + Mean: 177.78617596587668
  + Median: 0.0
  + Stddev: 1446.98681640625
  + Non-zero count: 1373379.3212738037

* claims_PC:
  + Type: bool
  + Entity: benunit
  + Description: Whether this family is imputed to claim Pension Credit
  + Mean: 0.6346426429569206
  + Median: 1.0
  + Stddev: 0.48127326937373555
  + Non-zero count: 22364643.0

* guarantee_credit_applicable_income:
  + Type: float
  + Entity: benunit
  + Description: Applicable income for Pension Credit
  + Mean: 27911.65076290768
  + Median: 21524.038542819842
  + Stddev: 25316.537109375
  + Non-zero count: 32533769.0

* pension_credit:
  + Type: float
  + Entity: benunit
  + Description: Pension Credit
  + Mean: 69.25273086704398
  + Median: 0.0
  + Stddev: 563.7106323242188
  + Non-zero count: 1294941.0

* pension_credit_GC:
  + Type: float
  + Entity: benunit
  + Description: Pension Credit (Guarantee Credit) amount
  + Mean: 45.18754965016996
  + Median: 0.0
  + Stddev: 490.9631042480469
  + Non-zero count: 650580.0

* pension_credit_MG:
  + Type: float
  + Entity: benunit
  + Description: Pension Credit (Minimum Guarantee) amount per week
  + Mean: 1391.9502942924341
  + Median: 0.0
  + Stddev: 4203.080078125
  + Non-zero count: 4407544.0

* pension_credit_SC:
  + Type: float
  + Entity: benunit
  + Description: Pension Credit (Savings Credit) amount per week
  + Mean: 24.065181186630962
  + Median: 0.0
  + Stddev: 264.383544921875
  + Non-zero count: 906256.0

* pension_credit_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Eligible for Pension Credit
  + Mean: 0.19612090236074942
  + Median: 0.0
  + Stddev: 0.42754902472222106
  + Non-zero count: 6911250.0

* pension_credit_reported:
  + Type: float
  + Entity: person
  + Description: Reported amount of Pension Credit
  + Mean: 50.83380117653684
  + Median: 0.0
  + Stddev: 578.7509155273438
  + Non-zero count: 1151151.482559204

* savings_credit_applicable_income:
  + Type: float
  + Entity: benunit
  + Description: Applicable income for Savings Credit
  + Mean: 27746.105302807064
  + Median: 21305.151848937847
  + Stddev: 25371.04296875
  + Non-zero count: 32469022.0

* would_claim_PC:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Pension Credit
  + Mean: 0.6346426429569206
  + Median: 1.0
  + Stddev: 0.48127326937373555
  + Non-zero count: 22364643.0

* claims_IS:
  + Type: bool
  + Entity: benunit
  + Description: Whether this family is imputed to claim Income Support
  + Mean: 0.36699408866273764
  + Median: 0.0
  + Stddev: 0.48240720200675785
  + Non-zero count: 12932777.0

* income_support:
  + Type: float
  + Entity: benunit
  + Description: Income Support
  + Mean: 35.01699705171057
  + Median: 0.0
  + Stddev: 544.0704345703125
  + Non-zero count: 244866.0

* income_support_applicable_amount:
  + Type: float
  + Entity: benunit
  + Description: Applicable amount of Income Support
  + Mean: 80.46853699105893
  + Median: 0.0
  + Stddev: 917.71044921875
  + Non-zero count: 424837.0

* income_support_applicable_income:
  + Type: float
  + Entity: benunit
  + Description: Relevant income for Income Support means test
  + Mean: 25252.784256885025
  + Median: 19210.947115530762
  + Stddev: 24437.923828125
  + Non-zero count: 30587483.0

* income_support_eligible:
  + Type: bool
  + Entity: benunit
  + Description: Whether eligible for Income Support
  + Mean: 0.032897431541922185
  + Median: 0.0
  + Stddev: 0.19280252055940614
  + Non-zero count: 1159297.0

* income_support_reported:
  + Type: float
  + Entity: person
  + Description: Income Support (reported amount)
  + Mean: 21.06211868406385
  + Median: 0.0
  + Stddev: 382.022216796875
  + Non-zero count: 385600.9823913574

* would_claim_IS:
  + Type: bool
  + Entity: benunit
  + Description: Would claim Income Support
  + Mean: 0.8981577390663076
  + Median: 1.0
  + Stddev: 0.3025527785847836
  + Non-zero count: 31650847.0

* in_deep_poverty_ahc:
  + Type: bool
  + Entity: household
  + Description: Whether the household is in deep absolute poverty (below half the poverty line), after housing costs
  + Mean: 0.09664142396621216
  + Median: 0.0
  + Stddev: 0.2891568911388552
  + Non-zero count: 2708261.0

* in_deep_poverty_bhc:
  + Type: bool
  + Entity: household
  + Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  + Mean: 0.055053076114451385
  + Median: 0.0
  + Stddev: 0.22214621203654042
  + Non-zero count: 1542797.0

* in_poverty_ahc:
  + Type: bool
  + Entity: household
  + Description: Whether the household is in absolute poverty, after housing costs
  + Mean: 0.21505576097412304
  + Median: 0.0
  + Stddev: 0.412264448261856
  + Non-zero count: 6026682.0

* in_poverty_bhc:
  + Type: bool
  + Entity: household
  + Description: Whether the household is in absolute poverty, before housing costs
  + Mean: 0.1904155005898377
  + Median: 0.0
  + Stddev: 0.3983217270535231
  + Non-zero count: 5336168.0

* poverty_gap_ahc:
  + Type: float
  + Entity: household
  + Description: Positive financial gap between net household income and the poverty line, after housing costs
  + Mean: 1571.4026647839407
  + Median: 0.0
  + Stddev: 4133.63818359375
  + Non-zero count: 6026682.0

* poverty_gap_bhc:
  + Type: float
  + Entity: household
  + Description: Positive financial gap between net household income and the poverty line
  + Mean: 1087.7067825807642
  + Median: 0.0
  + Stddev: 3086.734375
  + Non-zero count: 5336168.0

* poverty_line_ahc:
  + Type: float
  + Entity: household
  + Description: The poverty line for the household, after housing costs
  + Mean: 14331.511851704041
  + Median: 13556.5732421875
  + Stddev: 5587.46923828125
  + Non-zero count: 28023811.0

* poverty_line_bhc:
  + Type: float
  + Entity: household
  + Description: The poverty line for the household, before housing costs
  + Mean: 16799.263650825378
  + Median: 15822.2958984375
  + Stddev: 5425.3759765625
  + Non-zero count: 28023811.0

* BRMA:
  + Type: Categorical
  + Entity: household
  + Description: Broad Rental Market Area

* local_authority:
  + Type: Categorical
  + Entity: household
  + Description: The Local Authority for the household

* age:
  + Type: int
  + Entity: person
  + Description: Age
  + Mean: 39.261013462662824
  + Median: 39.0
  + Stddev: 23.648786818116807
  + Non-zero count: 66205795.1907959

* age_18_64:
  + Type: bool
  + Entity: person
  + Description: Whether the person is age 18 to 64
  + Mean: 0.6124304055763132
  + Median: 1.0
  + Stddev: 0.49555872207518314
  + Non-zero count: 40995490.872909546

* age_over_64:
  + Type: bool
  + Entity: person
  + Description: Whether the person is over age 64
  + Mean: 0.17128312714128785
  + Median: 0.0
  + Stddev: 0.40539378928130615
  + Non-zero count: 11465524.59098816

* age_under_18:
  + Type: bool
  + Entity: person
  + Description: Whether the person is under age 18
  + Mean: 0.21628646728239886
  + Median: 0.0
  + Stddev: 0.4183352569428601
  + Non-zero count: 14478004.055114746

* birth_year:
  + Type: int
  + Entity: person
  + Description: The birth year of the person
  + Mean: 1980.7389865373373
  + Median: 1981.0
  + Stddev: 23.648786818116815
  + Non-zero count: 66939019.51901245

* child_index:
  + Type: int
  + Entity: person
  + Description: Child reference number
  + Mean: 78.70912690065151
  + Median: 100.0
  + Stddev: 41.170164546599146
  + Non-zero count: 66939019.51901245

* current_education:
  + Type: Categorical
  + Entity: person
  + Description: Current education

* gender:
  + Type: Categorical
  + Entity: person
  + Description: Gender of the person

* highest_education:
  + Type: Categorical
  + Entity: person
  + Description: Highest status education completed

* in_FE:
  + Type: bool
  + Entity: person
  + Description: Whether this person is in Further Education
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* in_HE:
  + Type: bool
  + Entity: person
  + Description: In higher education
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* in_social_housing:
  + Type: bool
  + Entity: person
  + Description: Whether this person lives in social housing
  + Mean: 0.16278496177134408
  + Median: 0.0
  + Stddev: 0.37780549089136584
  + Non-zero count: 10896665.733413696

* is_WA_adult:
  + Type: bool
  + Entity: person
  + Description: Whether is a working-age adult
  + Mean: 0.6223473210461764
  + Median: 1.0
  + Stddev: 0.4937540588260953
  + Non-zero count: 41659319.47111511

* is_adult:
  + Type: bool
  + Entity: person
  + Description: Whether this person is an adult
  + Mean: 0.7837135327176011
  + Median: 1.0
  + Stddev: 0.4183352569428601
  + Non-zero count: 52461015.463897705

* is_benunit_eldest_child:
  + Type: bool
  + Entity: person
  + Description: Eldest child in the benefit unit
  + Mean: 0.11982461408587235
  + Median: 0.0
  + Stddev: 0.3304804204558162
  + Non-zero count: 8020942.181152344

* is_benunit_head:
  + Type: bool
  + Entity: person
  + Description: Whether this person is the head-of-family
  + Mean: 0.5370703740643783
  + Median: 1.0
  + Stddev: 0.4993882658360249
  + Non-zero count: 35950964.252578735

* is_child:
  + Type: bool
  + Entity: person
  + Description: Is a child
  + Mean: 0.21628646728239886
  + Median: 0.0
  + Stddev: 0.4183352569428601
  + Non-zero count: 14478004.055114746

* is_eldest_child:
  + Type: bool
  + Entity: person
  + Description: Is the eldest child
  + Mean: 0.12667467900348664
  + Median: 0.0
  + Stddev: 0.3351397621808881
  + Non-zero count: 8479478.810379028

* is_female:
  + Type: bool
  + Entity: person
  + Description: Whether the person is female
  + Mean: 0.5063018776517798
  + Median: 1.0
  + Stddev: 0.4996619537061989
  + Non-zero count: 33891351.27064514

* is_household_head:
  + Type: bool
  + Entity: person
  + Description: Whether this person is the head-of-household
  + Mean: 0.42709313952404715
  + Median: 0.0
  + Stddev: 0.49680386165484386
  + Non-zero count: 28589196.0030365

* is_male:
  + Type: bool
  + Entity: person
  + Description: Whether the person is male
  + Mean: 0.4936981223482202
  + Median: 0.0
  + Stddev: 0.4996619537061989
  + Non-zero count: 33047668.24836731

* is_older_child:
  + Type: bool
  + Entity: person
  + Description: Whether the person is over 14 but under 18
  + Mean: 0.048541240974316884
  + Median: 0.0
  + Stddev: 0.21590012114739232
  + Non-zero count: 3249303.0770568848

* is_young_child:
  + Type: bool
  + Entity: person
  + Description: Whether the person is under 14
  + Mean: 0.167745226308082
  + Median: 0.0
  + Stddev: 0.38177901330435976
  + Non-zero count: 11228700.978057861

* marital_status:
  + Type: Categorical
  + Entity: person
  + Description: Marital status

* over_16:
  + Type: bool
  + Entity: person
  + Description: Whether the person is over 16
  + Mean: 0.8094825115094362
  + Median: 1.0
  + Stddev: 0.4012150589689833
  + Non-zero count: 54185965.63822937

* people:
  + Type: float
  + Entity: person
  + Description: Variable holding people
  + Mean: 1.0
  + Median: 1.0
  + Stddev: 0.0
  + Non-zero count: 66939019.51901245

* person_id:
  + Type: int
  + Entity: person
  + Description: ID for the person
  + Mean: 959653.1925843834
  + Median: 959528.96713811
  + Stddev: 554308.7927831486
  + Non-zero count: 66939019.51901245

* person_weight:
  + Type: float
  + Entity: person
  + Description: Weight (region-adjusted)
  + Mean: 2042.6312240415673
  + Median: 1733.8243408203125
  + Stddev: 876.5885009765625
  + Non-zero count: 66939019.51901245

* raw_person_weight:
  + Type: float
  + Entity: person
  + Description: Weight factor
  + Mean: 2001.8910841153647
  + Median: 1699.0
  + Stddev: 858.664306640625
  + Non-zero count: 66939019.51901245

* person_benunit_id:
  + Type: float
  + Entity: person
  + Description: Person's benefit unit ID
  + Mean: 959651.1687663301
  + Median: 959527.96713811
  + Stddev: 554307.75
  + Non-zero count: 66939019.51901245

* person_household_id:
  + Type: float
  + Entity: person
  + Description: Person's household ID
  + Mean: 959639.5106735906
  + Median: 959517.96713811
  + Stddev: 554307.875
  + Non-zero count: 66939019.51901245

* role:
  + Type: Categorical
  + Entity: person
  + Description: Role (adult/child)

* accommodation_type:
  + Type: Categorical
  + Entity: household
  + Description: Type of accommodation

* country:
  + Type: Categorical
  + Entity: household
  + Description: Country of the UK

* household_equivalisation_ahc:
  + Type: float
  + Entity: household
  + Description: Equivalisation factor to account for household composition, after housing costs
  + Mean: 1.0571633053463658
  + Median: 1.0
  + Stddev: 0.41218996047973633
  + Non-zero count: 28023811.0

* household_equivalisation_bhc:
  + Type: float
  + Entity: household
  + Description: Equivalisation factor to account for household composition, before housing costs
  + Mean: 1.0617462691963264
  + Median: 1.0
  + Stddev: 0.3428944945335388
  + Non-zero count: 28023811.0

* household_id:
  + Type: int
  + Entity: household
  + Description: ID for the household
  + Mean: 958404.5237316224
  + Median: 958313.664790494
  + Stddev: 554559.3671255285
  + Non-zero count: 28023811.0

* household_num_benunits:
  + Type: int
  + Entity: household
  + Description: Number of benefit units
  + Mean: 1.2574928513470205
  + Median: 1.0
  + Stddev: 0.520039498560071
  + Non-zero count: 28023811.0

* household_num_people:
  + Type: int
  + Entity: household
  + Description: Number of people
  + Mean: 2.3413876149821307
  + Median: 2.0
  + Stddev: 1.2539736242005226
  + Non-zero count: 28023811.0

* household_weight:
  + Type: float
  + Entity: household
  + Description: Weight factor for the household
  + Mean: 1938.489101178994
  + Median: 1639.0
  + Stddev: 836.5348510742188
  + Non-zero count: 28023811.0

* households:
  + Type: float
  + Entity: household
  + Description: Variable holding households
  + Mean: 1.0
  + Median: 1.0
  + Stddev: 0.0
  + Non-zero count: 28023811.0

* is_renting:
  + Type: bool
  + Entity: household
  + Description: Is renting
  + Mean: 0.27033642926010315
  + Median: 0.0
  + Stddev: 0.441824443144987
  + Non-zero count: 7575857.0

* is_shared_accommodation:
  + Type: bool
  + Entity: household
  + Description: Whether the household is shared accommodation
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* num_bedrooms:
  + Type: int
  + Entity: household
  + Description: The number of bedrooms in the house
  + Mean: 2.775578025415601
  + Median: 3.0
  + Stddev: 1.0121163086230742
  + Non-zero count: 28023811.0

* region:
  + Type: Categorical
  + Entity: household
  + Description: Region

* tenure_type:
  + Type: Categorical
  + Entity: household
  + Description: Tenure type of the household

* benunit_id:
  + Type: int
  + Entity: benunit
  + Description: ID for the family
  + Mean: 959451.5537894687
  + Median: 961134.1430700447
  + Stddev: 553578.6907779488
  + Non-zero count: 35239742.0

* benunit_is_renting:
  + Type: bool
  + Entity: benunit
  + Description: Whether this family is renting
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* benunit_tenure_type:
  + Type: Categorical
  + Entity: benunit
  + Description: Tenure type of the family's household

* benunit_weight:
  + Type: float
  + Entity: benunit
  + Description: Weight factor for the benefit unit
  + Mean: 2072.443922319295
  + Median: 1742.0
  + Stddev: 899.8135375976562
  + Non-zero count: 35239742.0

* eldest_adult_age:
  + Type: float
  + Entity: benunit
  + Description: Eldest adult age
  + Mean: 47.662654737937636
  + Median: 48.0
  + Stddev: 18.706043243408203
  + Non-zero count: 35239742.0

* eldest_child_age:
  + Type: float
  + Entity: benunit
  + Description: Eldest adult age
  + Mean: -inf
  + Median: -inf
  + Stddev: nan
  + Non-zero count: 7532484.0

* families:
  + Type: float
  + Entity: benunit
  + Description: Variable holding families
  + Mean: 1.0
  + Median: 1.0
  + Stddev: 0.0
  + Non-zero count: 35239742.0

* family_type:
  + Type: Categorical
  + Entity: benunit
  + Description: Family composition

* is_married:
  + Type: bool
  + Entity: benunit
  + Description: Married
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* num_adults:
  + Type: int
  + Entity: benunit
  + Description: The number of adults in the family
  + Mean: 1.4592390035091631
  + Median: 1.0
  + Stddev: 0.5370500709057318
  + Non-zero count: 34684149.0

* num_children:
  + Type: int
  + Entity: benunit
  + Description: The number of children in the family
  + Mean: 0.4027100425423092
  + Median: 0.0
  + Stddev: 0.8681971273016468
  + Non-zero count: 8311716.0

* relation_type:
  + Type: Categorical
  + Entity: benunit
  + Description: Whether single or a couple

* youngest_adult_age:
  + Type: float
  + Entity: benunit
  + Description: Eldest adult age
  + Mean: 45.935262636145296
  + Median: 45.0
  + Stddev: 18.577775955200195
  + Non-zero count: 35239742.0

* youngest_child_age:
  + Type: float
  + Entity: benunit
  + Description: Eldest adult age
  + Mean: inf
  + Median: inf
  + Stddev: nan
  + Non-zero count: 34527020.0

* state_id:
  + Type: int
  + Entity: state
  + Description: State ID
  + Mean: 1.0
  + Median: 1.0
  + Stddev: nan
  + Non-zero count: 1.0

* state_weight:
  + Type: float
  + Entity: state
  + Description: State weight
  + Mean: 1.0
  + Median: 1.0
  + Stddev: nan
  + Non-zero count: 1.0

* expected_ltt:
  + Type: float
  + Entity: household
  + Description: Land Transaction Tax (expected)
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* land_transaction_tax:
  + Type: float
  + Entity: household
  + Description: Land Transaction Tax
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* ltt_liable:
  + Type: bool
  + Entity: household
  + Description: Liable for Land Transaction Tax
  + Mean: 0.048650984692981264
  + Median: 0.0
  + Stddev: 0.19640362298074734
  + Non-zero count: 1363386.0

* ltt_on_non_residential_property_rent:
  + Type: float
  + Entity: household
  + Description: LTT on non-residential property rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* ltt_on_non_residential_property_transactions:
  + Type: float
  + Entity: household
  + Description: LTT on non-residential property transactions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* ltt_on_rent:
  + Type: float
  + Entity: household
  + Description: LTT on property rental
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* ltt_on_residential_property_rent:
  + Type: float
  + Entity: household
  + Description: LTT on residential property rent
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* ltt_on_residential_property_transactions:
  + Type: float
  + Entity: household
  + Description: LTT on residential property
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0

* ltt_on_transactions:
  + Type: float
  + Entity: household
  + Description: LTT on property transactions
  + Mean: 0.0
  + Median: 0.0
  + Stddev: 0.0
  + Non-zero count: 0.0
>>>>>>> 451f3998a257d6a0d575d04d0d0b2ba3d4aa630b

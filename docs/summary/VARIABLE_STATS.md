# OpenFisca-UK Variable Statistics

All statistics generated from the uprated (to 2020) 2018-19 Family Resources Survey, with simulation turned on.


- childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 125.09267839304603
  - Median: 0.0
  - Stddev: 1136.7957763671875
  - Non-zero count: 2610551.0


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1355.3086094727296
  - Median: 1319.4134102849832
  - Stddev: 565.3695068359375
  - Non-zero count: 27793895.0


- family_rent:
  - Type: float
  - Entity: benunit
  - Description: Gross rent for the family
  - Mean: 2103.9165108657767
  - Median: 0.0
  - Stddev: 4989.38671875
  - Non-zero count: 9988990.0


- housing_costs:
  - Type: float
  - Entity: household
  - Description: Total housing costs
  - Mean: 141.25823321009284
  - Median: 64.0
  - Stddev: 1025.5020751953125
  - Non-zero count: 27736446.0


- mortgage:
  - Type: float
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- personal_rent:
  - Type: float
  - Entity: person
  - Description: Personal rent
  - Mean: 1126.1902804055464
  - Median: 0.0
  - Stddev: 3730.41650390625
  - Non-zero count: 9988990.0


- rent:
  - Type: float
  - Entity: household
  - Description: Gross rent for the household
  - Mean: 2650.144389836323
  - Median: 0.0
  - Stddev: 5322.75634765625
  - Non-zero count: 9990064.0


- weekly_childcare_expenses:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 2.405623230358915
  - Median: 0.0
  - Stddev: 21.861448287963867
  - Non-zero count: 2610551.0


- weekly_rent:
  - Type: float
  - Entity: household
  - Description: Weekly average rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- base_net_income:
  - Type: float
  - Entity: person
  - Description: Existing net income for the person to use as a base in microsimulation
  - Mean: 16013.465239778216
  - Median: 13000.0
  - Stddev: 111095.6015625
  - Non-zero count: 49639715.0


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 16603.544036325835
  - Median: 6506.56005859375
  - Stddev: 114504.6171875
  - Non-zero count: 38513248.0


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income
  - Mean: 41913.863429923134
  - Median: 30401.063033328315
  - Stddev: 167061.421875
  - Non-zero count: 27651387.0


- equiv_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs
  - Mean: 44450.39051534499
  - Median: 31515.223478090924
  - Stddev: 167445.90625
  - Non-zero count: 27638175.0


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 20590.518871628872
  - Median: 14339.364783653846
  - Stddev: 114557.6328125
  - Non-zero count: 49047900.0


- hours_worked:
  - Type: float
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 888.956238848766
  - Median: 0.0
  - Stddev: 1013.0665283203125
  - Non-zero count: 31045772.0


- household_net_income:
  - Type: float
  - Entity: household
  - Description: Household net income
  - Mean: 38958.292700738275
  - Median: 29750.959555893456
  - Stddev: 168180.109375
  - Non-zero count: 27651387.0


- household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 38817.03452923758
  - Median: 29597.437292744533
  - Stddev: 168188.0
  - Non-zero count: 27638175.0


- miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Income from other sources
  - Mean: 482.6508979813011
  - Median: 0.0
  - Stddev: 2594.072998046875
  - Non-zero count: 9758936.0


- net_income:
  - Type: float
  - Entity: person
  - Description: Net income for the person
  - Mean: 17104.98470408964
  - Median: 13816.662090551514
  - Stddev: 112196.3671875
  - Non-zero count: 48979992.0


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Income from self-employment. Different to trading profits
  - Mean: 2513.790162083478
  - Median: 0.0
  - Stddev: 112434.7109375
  - Non-zero count: 4170388.0


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
  - Description: Average weekly hours for the year
  - Mean: 17.09531228561137
  - Median: 0.0
  - Stddev: 19.48204803466797
  - Non-zero count: 31045772.0


- disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Disability premium
  - Mean: 179.10591925614628
  - Median: 0.0
  - Stddev: 658.197021484375
  - Non-zero count: 2916234.0


- enhanced_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 0.5436544051951367
  - Median: 0.0
  - Stddev: 27.487537384033203
  - Non-zero count: 16244.0


- is_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is disabled for benefits purposes
  - Mean: 0.047336994532026555
  - Median: 0.0
  - Stddev: 0.22948140031146275
  - Non-zero count: 3099558.0


- is_enhanced_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0002480812229286367
  - Median: 0.0
  - Stddev: 0.01736753013487885
  - Non-zero count: 16244.0


- is_severely_disabled_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is severely disabled for benefits purposes
  - Mean: 0.029661146309658177
  - Median: 0.0
  - Stddev: 0.18366175665180345
  - Non-zero count: 1942169.0


- num_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.08721611577075342
  - Median: 0.0
  - Stddev: 0.3237573547133562
  - Non-zero count: 2916234.0


- num_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.001217505175459777
  - Median: 0.0
  - Stddev: 0.038356358524750576
  - Non-zero count: 40069.0


- num_enhanced_disabled_adults:
  - Type: int
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0004634582539350085
  - Median: 0.0
  - Stddev: 0.024080925619403934
  - Non-zero count: 16244.0


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
  - Mean: 0.05480151338920453
  - Median: 0.0
  - Stddev: 0.2601033122450189
  - Non-zero count: 1852755.0


- num_severely_disabled_children:
  - Type: int
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0006105928399694113
  - Median: 0.0
  - Stddev: 0.02586590835864191
  - Non-zero count: 21401.0


- severe_disability_premium:
  - Type: float
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 262.9372236975554
  - Median: 0.0
  - Stddev: 1294.7279052734375
  - Non-zero count: 1852755.0


- carer_premium:
  - Type: float
  - Entity: benunit
  - Description: Carer premium
  - Mean: 40.273449499755245
  - Median: 0.0
  - Stddev: 302.28387451171875
  - Non-zero count: 723880.0


- is_carer_for_benefits:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.011218650136674519
  - Median: 0.0
  - Stddev: 0.11336199523779618
  - Non-zero count: 734581.0


- num_carers:
  - Type: int
  - Entity: benunit
  - Description: The number of carers for benefits purposes in the family
  - Mean: 0.020958361711021452
  - Median: 0.0
  - Stddev: 0.15879395344224553
  - Non-zero count: 723880.0


- benefits:
  - Type: float
  - Entity: person
  - Description: Total benefits
  - Mean: 3006.0778502690664
  - Median: 0.0
  - Stddev: 5035.77001953125
  - Non-zero count: 26278690.0


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 249.15718543918467
  - Median: 0.0
  - Stddev: 2738.7880859375
  - Non-zero count: 12598242.0


- benefits_premiums:
  - Type: float
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 482.8602513959341
  - Median: 0.0
  - Stddev: 1802.283203125
  - Non-zero count: 3972667.0


- benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2756.9206651993477
  - Median: 0.0
  - Stddev: 5288.43115234375
  - Non-zero count: 22632905.0


- benunit_weekly_hours:
  - Type: float
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 31.93697406325792
  - Median: 35.0
  - Stddev: 30.85429573059082
  - Non-zero count: 22047795.0


- claims_legacy_benefits:
  - Type: float
  - Entity: benunit
  - Description: Whether this family is imputed to claim legacy benefits over Universal Credit
  - Mean: 0.5847983239039665
  - Median: 1.0
  - Stddev: 0.4926054775714874
  - Non-zero count: 20496914.0


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1251.2554179753263
  - Median: 0.0
  - Stddev: 3068.315673828125
  - Non-zero count: 15813086.0


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 896.2004344673302
  - Median: 0.0
  - Stddev: 3085.493896484375
  - Non-zero count: 10893314.0


- is_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.00023813903651355775
  - Median: 0.0
  - Stddev: 0.011799871994737398
  - Non-zero count: 15593.0


- is_child_or_QYP:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.20974355649723792
  - Median: 0.0
  - Stddev: 0.41741013183180975
  - Non-zero count: 13733705.0


- is_couple:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.47088819389171493
  - Median: 0.0
  - Stddev: 0.4997369072587858
  - Non-zero count: 16504416.0


- is_lone_parent:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.05298828004690389
  - Median: 0.0
  - Stddev: 0.2483815473233918
  - Non-zero count: 1857215.0


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.529111806108285
  - Median: 1.0
  - Stddev: 0.4997369072587858
  - Non-zero count: 18545127.0


- is_single_person:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.4761235260613812
  - Median: 0.0
  - Stddev: 0.4975552506534362
  - Non-zero count: 16687912.0


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -249.1571834383448
  - Median: 0.0
  - Stddev: 2738.7880859375
  - Non-zero count: 17446950.0


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1754.82243031236
  - Median: 0.0
  - Stddev: 3929.2294921875
  - Non-zero count: 14627495.0


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1711.0884898733384
  - Median: 0.0
  - Stddev: 3769.971435546875
  - Non-zero count: 14653250.0


- child_benefit:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit for the family
  - Mean: 357.7223320751513
  - Median: 0.0
  - Stddev: 762.013671875
  - Non-zero count: 7786103.0


- child_benefit_less_tax_charge:
  - Type: float
  - Entity: benunit
  - Description: Child Benefit entitlement, less the High Income Tax Charge
  - Mean: 297.39585679395736
  - Median: 0.0
  - Stddev: 709.2188110351562
  - Non-zero count: 6739525.0


- child_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 159.7622510929144
  - Median: 0.0
  - Stddev: 547.518798828125
  - Non-zero count: 6424339.0


- claims_child_benefit:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Benefit, based on survey response and take-up rates
  - Mean: 0.9594976174154396
  - Median: 1.0
  - Stddev: 0.19393539792687098
  - Non-zero count: 33629953.0


- claims_HB:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Housing Benefit
  - Mean: 0.4481035886830251
  - Median: 0.0
  - Stddev: 0.49863700729490523
  - Non-zero count: 15705826.0


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 649.3673901754497
  - Median: 0.0
  - Stddev: 1898.8798828125
  - Non-zero count: 4510475.0


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 6803.651376568376
  - Median: 5972.2001953125
  - Stddev: 4200.65283203125
  - Non-zero count: 35049543.0


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 25207.448296155737
  - Median: 19445.52392416621
  - Stddev: 22586.51171875
  - Non-zero count: 31912975.0


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 35049543.0


- housing_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Housing Benefit (reported amount)
  - Mean: 248.752851693387
  - Median: 0.0
  - Stddev: 1191.31884765625
  - Non-zero count: 3596990.0


- ESA_income:
  - Type: float
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 111.22380234209456
  - Median: 0.0
  - Stddev: 902.1917114257812
  - Non-zero count: 660734.0


- ESA_income_reported:
  - Type: float
  - Entity: person
  - Description: ESA (income-based) (reported amount)
  - Mean: 59.53618618296753
  - Median: 0.0
  - Stddev: 649.055908203125
  - Non-zero count: 669633.0


- claims_PC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Pension Credit
  - Mean: 0.6209874976115951
  - Median: 1.0
  - Stddev: 0.48488194694076
  - Non-zero count: 21765328.0


- pension_credit:
  - Type: float
  - Entity: benunit
  - Description: Pension credit amount
  - Mean: 100.82389268947384
  - Median: 0.0
  - Stddev: 684.5028076171875
  - Non-zero count: 1690704.0


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 88.80662959653392
  - Median: 0.0
  - Stddev: 666.7440795898438
  - Non-zero count: 1211725.0


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 1591.6607888344226
  - Median: 0.0
  - Stddev: 4566.2138671875
  - Non-zero count: 4811156.0


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 12.01726263137759
  - Median: 0.0
  - Stddev: 90.40499114990234
  - Non-zero count: 970878.0


- pension_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 26824.744501124685
  - Median: 20366.140625
  - Stddev: 24358.177734375
  - Non-zero count: 32332538.0


- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Pension Credit
  - Mean: 0.2066710541703782
  - Median: 0.0
  - Stddev: 0.43685648603845284
  - Non-zero count: 7243726.0


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit
  - Mean: 47.055047643335875
  - Median: 0.0
  - Stddev: 547.4176025390625
  - Non-zero count: 1132019.0


- benefit_cap:
  - Type: float
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: inf
  - Median: 13399.8798828125
  - Stddev: nan
  - Non-zero count: 35049543.0


- is_benefit_cap_exempt:
  - Type: bool
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.0926846321505533
  - Median: 0.0
  - Stddev: 0.31523770206740787
  - Non-zero count: 3248554.0


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA Rate
  - Mean: 7144.213197294615
  - Median: 6817.72021484375
  - Stddev: 671.7394409179688
  - Non-zero count: 35049543.0


- LHA_allowed_bedrooms:
  - Type: float
  - Entity: benunit
  - Description: The number of bedrooms covered by LHA for the benefit unit
  - Mean: 1.2048090612764908
  - Median: 1.0
  - Stddev: 0.4163703918457031
  - Non-zero count: 35049543.0


- LHA_cap:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 2096.63574138239
  - Median: 0.0
  - Stddev: 2778.35693359375
  - Non-zero count: 12868102.0


- LHA_category:
  - Type: Categorical
  - Entity: benunit
  - Description: LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms


- LHA_eligible:
  - Type: float
  - Entity: benunit
  - Description: Whether eligible for Local Housing Allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 5.671329591958237
  - Median: 0.0
  - Stddev: 136.25550842285156
  - Non-zero count: 56433.0


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: Job Seeker's Allowance (income-based)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 25848.39575063413
  - Median: 19592.456677483708
  - Stddev: 23569.0703125
  - Non-zero count: 32066756.0


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for JSA (income-based)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- JSA_income_reported:
  - Type: float
  - Entity: person
  - Description: JSA (income-based) (reported amount)
  - Mean: 18.225201296318176
  - Median: 0.0
  - Stddev: 292.56048583984375
  - Non-zero count: 289811.0


- claims_JSA:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim JSA based on survey response and take-up rates
  - Mean: 0.009792709708083783
  - Median: 0.0
  - Stddev: 0.10187601112660134
  - Non-zero count: 343230.0


- CTC_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from child elements
  - Mean: 411.66078770270985
  - Median: 0.0
  - Stddev: 1722.11328125
  - Non-zero count: 2402900.0


- CTC_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 2.7256739124958065
  - Median: 0.0
  - Stddev: 107.4562759399414
  - Non-zero count: 25871.0


- CTC_family_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 37.36369686760253
  - Median: 0.0
  - Stddev: 148.44090270996094
  - Non-zero count: 2402900.0


- CTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: The maximum rate of CTC
  - Mean: 452.3935380555461
  - Median: 0.0
  - Stddev: 1881.0665283203125
  - Non-zero count: 2402900.0


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.6433795727379384
  - Median: 0.0
  - Stddev: 28.72562599182129
  - Non-zero count: 16581.0


- WTC_basic_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the basic element
  - Mean: 69.82268556254785
  - Median: 0.0
  - Stddev: 396.87481689453125
  - Non-zero count: 1187987.0


- WTC_childcare_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the childcare element
  - Mean: 14.562573549009937
  - Median: 0.0
  - Stddev: 306.87872314453125
  - Non-zero count: 212067.0


- WTC_couple_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the couple element
  - Mean: 32.20079731139433
  - Median: 0.0
  - Stddev: 254.30429077148438
  - Non-zero count: 551894.0


- WTC_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the disabled element
  - Mean: 3.7013486880556474
  - Median: 0.0
  - Stddev: 127.16803741455078
  - Non-zero count: 40289.0


- WTC_lone_parent_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the lone parent element
  - Mean: 31.79587619730163
  - Median: 0.0
  - Stddev: 289.07073974609375
  - Non-zero count: 544954.0


- WTC_maximum_rate:
  - Type: float
  - Entity: benunit
  - Description: The maximum rate of WTC
  - Mean: 167.6270274116988
  - Median: 0.0
  - Stddev: 1030.4771728515625
  - Non-zero count: 1187987.0


- WTC_severely_disabled_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the severely disabled element
  - Mean: 0.9038885328690306
  - Median: 0.0
  - Stddev: 39.382568359375
  - Non-zero count: 22792.0


- WTC_worker_element:
  - Type: float
  - Entity: benunit
  - Description: WTC entitlement from the worker element
  - Mean: 14.63985707317211
  - Median: 0.0
  - Stddev: 111.89149475097656
  - Non-zero count: 621964.0


- child_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Amount of Child Tax Credit entitled to
  - Mean: 359.64098710862515
  - Median: 0.0
  - Stddev: 1666.0440673828125
  - Non-zero count: 2137857.0


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 199.98005305082725
  - Median: 0.0
  - Stddev: 1295.7816162109375
  - Non-zero count: 2455681.0


- claims_CTC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates
  - Mean: 0.07006313891168281
  - Median: 0.0
  - Stddev: 0.2750975827810318
  - Non-zero count: 2455681.0


- claims_WTC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates
  - Mean: 0.035888513582045846
  - Median: 0.0
  - Stddev: 0.19771028774279886
  - Non-zero count: 1257876.0


- is_CTC_child_limit_exempt:
  - Type: bool
  - Entity: person
  - Description: Whether the person was born before 2017 and therefore exempt from the two-child limit for Child Tax Credit
  - Mean: 0.9498417306246297
  - Median: 1.0
  - Stddev: 0.21926754530601014
  - Non-zero count: 62194264.0


- is_CTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is eligible for CTC
  - Mean: 0.2242120817381271
  - Median: 0.0
  - Stddev: 0.42816255763543365
  - Non-zero count: 7858531.0


- is_WTC_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether the family is eligible for WTC
  - Mean: 0.509295684682679
  - Median: 1.0
  - Stddev: 0.49997852073009263
  - Non-zero count: 17850581.0


- is_child_for_CTC:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child conferring CTC eligibility
  - Mean: 0.20974355649723792
  - Median: 0.0
  - Stddev: 0.41741013183180975
  - Non-zero count: 13733705.0


- tax_credits:
  - Type: float
  - Entity: benunit
  - Description: Value of the Tax Credits (benefits) for this family
  - Mean: 434.70650491221755
  - Median: 0.0
  - Stddev: 2045.9078369140625
  - Non-zero count: 2244699.0


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 31782.31414078077
  - Median: 21509.30078125
  - Stddev: 36490.18359375
  - Non-zero count: 29854395.0


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 10769.791437752483
  - Median: 6045.225479332176
  - Stddev: 14648.9716796875
  - Non-zero count: 27891658.0


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Amount of Working Tax Credit entitled to
  - Mean: 75.06551677775722
  - Median: 0.0
  - Stddev: 632.8744506835938
  - Non-zero count: 884134.0


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit
  - Mean: 48.72485354905862
  - Median: 0.0
  - Stddev: 502.72576904296875
  - Non-zero count: 1257876.0


- claims_IS:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim Income Support
  - Mean: 0.0147520040418216
  - Median: 0.0
  - Stddev: 0.13562605112848378
  - Non-zero count: 517051.0


- income_support:
  - Type: float
  - Entity: benunit
  - Description: Income Support
  - Mean: 26.626250531551065
  - Median: 0.0
  - Stddev: 352.3977355957031
  - Non-zero count: 320990.0


- income_support_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 74.50721047010184
  - Median: 0.0
  - Stddev: 940.0902099609375
  - Non-zero count: 372395.0


- income_support_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 25848.39575063413
  - Median: 19592.456677483708
  - Stddev: 23569.0703125
  - Non-zero count: 32066756.0


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.034620679647663306
  - Median: 0.0
  - Stddev: 0.2014016234024655
  - Non-zero count: 1213439.0


- income_support_reported:
  - Type: float
  - Entity: person
  - Description: Income Support (reported amount)
  - Mean: 31.67203380580588
  - Median: 0.0
  - Stddev: 436.40301513671875
  - Non-zero count: 517051.0


- UC_eligible_rent:
  - Type: float
  - Entity: benunit
  - Description: Eligible rent in Universal Credit
  - Mean: 2973.9509832695962
  - Median: 0.0
  - Stddev: 5545.31884765625
  - Non-zero count: 12868102.0


- UC_personal_allowance:
  - Type: float
  - Entity: benunit
  - Description: Personal allowance for Universal Credit
  - Mean: 4709.33952855794
  - Median: 3813.840087890625
  - Stddev: 1166.548095703125
  - Non-zero count: 35049543.0


- UC_premiums:
  - Type: float
  - Entity: benunit
  - Description: Premiums for Universal Credit
  - Mean: 1507.5364545722894
  - Median: 0.0
  - Stddev: 2984.473388671875
  - Non-zero count: 10482433.0


- claims_UC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim UC
  - Mean: 0.4271726167727779
  - Median: 0.0
  - Stddev: 0.49451835909050895
  - Non-zero count: 14972205.0


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit
  - Mean: 657.089458065497
  - Median: 0.0
  - Stddev: 2180.377685546875
  - Non-zero count: 3715315.0


- universal_credit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Universal Credit
  - Mean: 9190.826869026461
  - Median: 7037.83984375
  - Stddev: 6572.17626953125
  - Non-zero count: 35049543.0


- universal_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Universal Credit
  - Mean: 0.6418966432743503
  - Median: 1.0
  - Stddev: 0.4932803854592814
  - Non-zero count: 22498184.0


- universal_credit_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 16021.599138654545
  - Median: 11711.180317427805
  - Stddev: 16645.10546875
  - Non-zero count: 29509186.0


- universal_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Universal Credit
  - Mean: 82.49195767988466
  - Median: 0.0
  - Stddev: 918.93798828125
  - Non-zero count: 722795.0


- ESA_contrib:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based)
  - Mean: 59.53618618296753
  - Median: 0.0
  - Stddev: 649.055908203125
  - Non-zero count: 669633.0


- ESA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 59.53618618296753
  - Median: 0.0
  - Stddev: 649.055908203125
  - Non-zero count: 669633.0


- SDA:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 0.49159017165673796
  - Median: 0.0
  - Stddev: 59.633575439453125
  - Non-zero count: 11916.0


- SDA_reported:
  - Type: float
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.49159017165673796
  - Median: 0.0
  - Stddev: 59.633575439453125
  - Non-zero count: 11916.0


- AA:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 47.522835178415896
  - Median: 0.0
  - Stddev: 471.4426574707031
  - Non-zero count: 810520.0


- AA_reported:
  - Type: float
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 47.522835178415896
  - Median: 0.0
  - Stddev: 471.4426574707031
  - Non-zero count: 810520.0


- DLA:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 104.97249687512193
  - Median: 0.0
  - Stddev: 850.8762817382812
  - Non-zero count: 1490840.0


- DLA_M:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 41.1395369681897
  - Median: 0.0
  - Stddev: 386.1026306152344
  - Non-zero count: 1106456.0


- DLA_M_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 41.1395369681897
  - Median: 0.0
  - Stddev: 386.1026306152344
  - Non-zero count: 1106456.0


- DLA_SC:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 63.83296142731909
  - Median: 0.0
  - Stddev: 539.0810546875
  - Non-zero count: 1317063.0


- DLA_SC_reported:
  - Type: float
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 63.83296142731909
  - Median: 0.0
  - Stddev: 539.0810546875
  - Non-zero count: 1317063.0


- JSA_contrib:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based)
  - Mean: 3.0357650745425384
  - Median: 0.0
  - Stddev: 98.28998565673828
  - Non-zero count: 56433.0


- JSA_contrib_reported:
  - Type: float
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 3.0357650745425384
  - Median: 0.0
  - Stddev: 98.28998565673828
  - Non-zero count: 56433.0


- PIP:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 122.76190559222545
  - Median: 0.0
  - Stddev: 869.198486328125
  - Non-zero count: 1619945.0


- PIP_DL:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 83.37038459003494
  - Median: 0.0
  - Stddev: 580.7643432617188
  - Non-zero count: 1521158.0


- PIP_DL_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 83.37038459003494
  - Median: 0.0
  - Stddev: 580.7643432617188
  - Non-zero count: 1521158.0


- PIP_M:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 39.39152241979964
  - Median: 0.0
  - Stddev: 349.8207092285156
  - Non-zero count: 1086010.0


- PIP_M_reported:
  - Type: float
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 39.39152241979964
  - Median: 0.0
  - Stddev: 349.8207092285156
  - Non-zero count: 1086010.0


- carers_allowance:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance
  - Mean: 38.15652685326379
  - Median: 0.0
  - Stddev: 385.40826416015625
  - Non-zero count: 734581.0


- carers_allowance_reported:
  - Type: float
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 38.15652685326379
  - Median: 0.0
  - Stddev: 385.40826416015625
  - Non-zero count: 734581.0


- BSP:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 3.57777213472748
  - Median: 0.0
  - Stddev: 166.6005096435547
  - Non-zero count: 57115.0


- BSP_reported:
  - Type: float
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 3.57777213472748
  - Median: 0.0
  - Stddev: 166.6005096435547
  - Non-zero count: 57115.0


- is_SP_age:
  - Type: bool
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.1695010221285427
  - Median: 0.0
  - Stddev: 0.4039124716918645
  - Non-zero count: 11098682.0


- state_pension:
  - Type: float
  - Entity: person
  - Description: Income from the State Pension
  - Mean: 1319.2645927963013
  - Median: 0.0
  - Stddev: 3253.012939453125
  - Non-zero count: 11554244.0


- state_pension_age:
  - Type: float
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 66.0
  - Median: 66.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- state_pension_reported:
  - Type: float
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1319.2645927963013
  - Median: 0.0
  - Stddev: 3253.012939453125
  - Non-zero count: 11554244.0


- incapacity_benefit:
  - Type: float
  - Entity: person
  - Description: Incapacity Benefit
  - Mean: 1.1138354037085239
  - Median: 0.0
  - Stddev: 90.69267272949219
  - Non-zero count: 14487.0


- incapacity_benefit_reported:
  - Type: float
  - Entity: person
  - Description: Incapacity Benefit (reported)
  - Mean: 1.1138354037085239
  - Median: 0.0
  - Stddev: 90.69267272949219
  - Non-zero count: 14487.0


- IIDB:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 6.86609316418156
  - Median: 0.0
  - Stddev: 182.73867797851562
  - Non-zero count: 151046.0


- IIDB_reported:
  - Type: float
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 6.86609316418156
  - Median: 0.0
  - Stddev: 182.73867797851562
  - Non-zero count: 151046.0


- AFCS:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 47.522835178415896
  - Median: 0.0
  - Stddev: 471.4426574707031
  - Non-zero count: 810520.0


- AFCS_reported:
  - Type: float
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 3.7888937997495638
  - Median: 0.0
  - Stddev: 184.4232635498047
  - Non-zero count: 61193.0


- tax:
  - Type: float
  - Entity: person
  - Description: Total tax
  - Mean: 3485.231870737895
  - Median: 0.0
  - Stddev: 8741.6181640625
  - Non-zero count: 32408922.0


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: -300.8765884544134
  - Median: 0.0
  - Stddev: 26886.5078125
  - Non-zero count: 19892879.0


- tax_reported:
  - Type: float
  - Entity: person
  - Description: Reported tax paid
  - Mean: 3786.1084525765727
  - Median: 52.0
  - Stddev: 28564.7890625
  - Non-zero count: 33916703.0


- NI_class_4:
  - Type: float
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 63.4286241479801
  - Median: 0.0
  - Stddev: 405.5129699707031
  - Non-zero count: 2699756.0


- national_insurance:
  - Type: float
  - Entity: person
  - Description: National Insurance
  - Mean: 978.2806903752779
  - Median: 0.0
  - Stddev: 1575.877197265625
  - Non-zero count: 26707975.0


- NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 7.111138662116169
  - Median: 0.0
  - Stddev: 30.886930465698242
  - Non-zero count: 2984789.0


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 7.111138662116169
  - Median: 0.0
  - Stddev: 30.886930465698242
  - Non-zero count: 2984789.0


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Whether is exempt from National Insurance
  - Mean: 0.3588102394745883
  - Median: 0.0
  - Stddev: 0.49172534222356884
  - Non-zero count: 23494376.0


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 907.740927358405
  - Median: 0.0
  - Stddev: 1547.19482421875
  - Non-zero count: 23855599.0


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 1004.0208076065543
  - Median: 0.0
  - Stddev: 1657.85400390625
  - Non-zero count: 23855599.0


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 1004.0208076065543
  - Median: 0.0
  - Stddev: 1657.85400390625
  - Non-zero count: 23855599.0


- total_NI:
  - Type: float
  - Entity: person
  - Description: Total National Insurance contributions by employers and employees
  - Mean: 1982.3012282364382
  - Median: 0.0
  - Stddev: 3194.5693359375
  - Non-zero count: 26707975.0


- dividend_income:
  - Type: float
  - Entity: person
  - Description: Income from dividends
  - Mean: 156.08652080332337
  - Median: 0.0
  - Stddev: 2217.05517578125
  - Non-zero count: 3636930.0


- employment_income:
  - Type: float
  - Entity: person
  - Description: Income from employment
  - Mean: 12400.056800903936
  - Median: 0.0
  - Stddev: 22424.2109375
  - Non-zero count: 26715128.0


- pension_income:
  - Type: float
  - Entity: person
  - Description: Income from pensions
  - Mean: 1689.6970724372545
  - Median: 0.0
  - Stddev: 7049.89599609375
  - Non-zero count: 9582497.0


- property_income:
  - Type: float
  - Entity: person
  - Description: Income from rental of property
  - Mean: 185.43164759732977
  - Median: 0.0
  - Stddev: 1760.3375244140625
  - Non-zero count: 1874106.0


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Income from interest on savings
  - Mean: 156.72779257495463
  - Median: 0.0
  - Stddev: 1145.89111328125
  - Non-zero count: 13858193.0


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1421.106906374954
  - Median: 0.0
  - Stddev: 3293.616455078125
  - Non-zero count: 12962546.0


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Income from trading profits for owned businesses
  - Mean: 1309.750639036479
  - Median: 0.0
  - Stddev: 9382.640625
  - Non-zero count: 3738272.0


- ISA_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount received in interest from Individual Savings Accounts
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- adjusted_net_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17182.867903272167
  - Median: 10085.7998046875
  - Stddev: 24382.818359375
  - Non-zero count: 44373046.0


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


- employment_deductions:
  - Type: float
  - Entity: person
  - Description: Deductions from employment income
  - Mean: 2.0078684449393553
  - Median: 0.0
  - Stddev: 125.98779296875
  - Non-zero count: 449034.0


- employment_expenses:
  - Type: float
  - Entity: person
  - Description: Cost of expenses necessarily incurred and reimbursed by employment
  - Mean: 0.30243512986855614
  - Median: 0.0
  - Stddev: 5.305002212524414
  - Non-zero count: 423893.0


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
  - Mean: 1.7054333086934788
  - Median: 0.0
  - Stddev: 125.82318878173828
  - Non-zero count: 35875.0


- pension_contributions_relief:
  - Type: float
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1632.5649929093834
  - Median: 0.0
  - Stddev: 1767.40478515625
  - Non-zero count: 29952273.0


- tax_free_savings_income:
  - Type: float
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 52.80939414514773
  - Median: 0.0
  - Stddev: 628.37548828125
  - Non-zero count: 9087589.0


- taxable_dividend_income:
  - Type: float
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 156.08652080332337
  - Median: 0.0
  - Stddev: 2217.05517578125
  - Non-zero count: 3636930.0


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 12398.178578026913
  - Median: 0.0
  - Stddev: 22420.3359375
  - Non-zero count: 26713361.0


- taxable_miscellaneous_income:
  - Type: float
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- taxable_pension_income:
  - Type: float
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1689.6970724372545
  - Median: 0.0
  - Stddev: 7049.89599609375
  - Non-zero count: 9582497.0


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 160.48089211202276
  - Median: 0.0
  - Stddev: 1667.854736328125
  - Non-zero count: 1448910.0


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 104.25036230969793
  - Median: 0.0
  - Stddev: 887.3092651367188
  - Non-zero count: 13456770.0


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1421.106906374954
  - Median: 0.0
  - Stddev: 3293.616455078125
  - Non-zero count: 12962546.0


- taxable_self_employment_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1253.0674617981022
  - Median: 0.0
  - Stddev: 9267.296875
  - Non-zero count: 3686220.0


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17801.508407398447
  - Median: 11137.6904296875
  - Stddev: 24533.25390625
  - Non-zero count: 46219717.0


- trading_loss:
  - Type: float
  - Entity: person
  - Description: Loss from trading in the current year.
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- allowances:
  - Type: float
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 12378.151589318824
  - Median: 12500.0
  - Stddev: 1102.2384033203125
  - Non-zero count: 64999573.0


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
  - Non-zero count: 65478555.0


- gift_aid:
  - Type: float
  - Entity: person
  - Description: Expenditure under Gift Aid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- marriage_allowance:
  - Type: float
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
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
  - Mean: 39964.163944880034
  - Median: 40000.0
  - Stddev: 956.5479125976562
  - Non-zero count: 65478555.0


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 12378.151589318824
  - Median: 12500.0
  - Stddev: 1102.2384033203125
  - Non-zero count: 64999573.0


- property_allowance:
  - Type: float
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1000.0
  - Median: 1000.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- property_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: 24.95075595142822
  - Median: 0.0
  - Stddev: 147.25271606445312
  - Non-zero count: 1874106.0


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 964.2853144819704
  - Median: 1000.0
  - Stddev: 132.6684112548828
  - Non-zero count: 65157849.0


- trading_allowance:
  - Type: float
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1000.0
  - Median: 1000.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- trading_allowance_deduction:
  - Type: float
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 56.683176946974065
  - Median: 0.0
  - Stddev: 219.7801971435547
  - Non-zero count: 3738272.0


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 32.29172391399829
  - Median: 0.0
  - Stddev: 234.63055419921875
  - Non-zero count: 1565156.0


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 338.5705027472814
  - Median: 0.0
  - Stddev: 6768.81591796875
  - Non-zero count: 300735.0


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 152.3567212370323
  - Median: 0.0
  - Stddev: 3045.96728515625
  - Non-zero count: 300735.0


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 2.96691158414476
  - Median: 0.0
  - Stddev: 480.8669128417969
  - Non-zero count: 6756.0


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7571.255554513604
  - Median: 0.0
  - Stddev: 11463.4462890625
  - Non-zero count: 29381696.0


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1514.251139189493
  - Median: 0.0
  - Stddev: 2292.689453125
  - Non-zero count: 29381696.0


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 26.878210930318502
  - Median: 0.0
  - Stddev: 504.34283447265625
  - Non-zero count: 299696.0


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 38.98390237927196
  - Median: 0.0
  - Stddev: 531.0001831054688
  - Non-zero count: 1080067.0


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 24.62290700594721
  - Median: 0.0
  - Stddev: 591.4855346679688
  - Non-zero count: 769422.0


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2441.378389416126
  - Median: 0.0
  - Stddev: 7382.34814453125
  - Non-zero count: 29381696.0


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 9846.752413655537
  - Median: 0.0
  - Stddev: 21900.841796875
  - Non-zero count: 29381696.0


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 1936.9263646380464
  - Median: 0.0
  - Stddev: 10550.546875
  - Non-zero count: 4212385.0


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 774.770549723735
  - Median: 0.0
  - Stddev: 4220.21875
  - Non-zero count: 4212385.0


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 4.868567022118794
  - Median: 0.0
  - Stddev: 238.80410766601562
  - Non-zero count: 61797.0


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2506.951205647026
  - Median: 0.0
  - Stddev: 7587.75830078125
  - Non-zero count: 29712511.0


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2474.6594773847887
  - Median: 0.0
  - Stddev: 7476.05126953125
  - Non-zero count: 29712511.0


- is_higher_earner:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5352827807516523
  - Median: 1.0
  - Stddev: 0.49960493110885895
  - Non-zero count: 35049543.0


- pays_scottish_income_tax:
  - Type: float
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 8.658179099500721
  - Median: 0.0
  - Stddev: 262.0494079589844
  - Non-zero count: 352224.0


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4971.128649887249
  - Median: 5000.0
  - Stddev: 324.33441162109375
  - Non-zero count: 65315219.0


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 119.8482456822422
  - Median: 0.0
  - Stddev: 2098.66943359375
  - Non-zero count: 769422.0


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 10001.314345692554
  - Median: 0.0
  - Stddev: 22192.896484375
  - Non-zero count: 29712511.0


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 34.713689149015174
  - Median: 0.0
  - Stddev: 757.955078125
  - Non-zero count: 352224.0


- in_deep_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), after housing costs
  - Mean: 0.027344274833107172
  - Median: 0.0
  - Stddev: 0.17567018605615467
  - Non-zero count: 760958.0


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.03463826863887384
  - Median: 0.0
  - Stddev: 0.1892454412914924
  - Non-zero count: 963941.0


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.09805946626419614
  - Median: 0.0
  - Stddev: 0.3195687337751294
  - Non-zero count: 2728876.0


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.162340061749727
  - Median: 0.0
  - Stddev: 0.3861227425295218
  - Non-zero count: 4517727.0


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 411.4819857434736
  - Median: 0.0
  - Stddev: 1899.73291015625
  - Non-zero count: 2728876.0


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 760.751967505167
  - Median: 0.0
  - Stddev: 2467.819580078125
  - Non-zero count: 4517727.0


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 12913.257294388308
  - Median: 14040.0
  - Stddev: 4697.22509765625
  - Non-zero count: 27828787.0


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 15675.092923887494
  - Median: 16432.0
  - Stddev: 4724.8349609375
  - Non-zero count: 27828787.0


- age:
  - Type: float
  - Entity: person
  - Description: The age of the person in years
  - Mean: 39.82097914347682
  - Median: 39.3239598278348
  - Stddev: 23.953073501586914
  - Non-zero count: 64672612.0


- age_18_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6106867660717314
  - Median: 1.0
  - Stddev: 0.49670193698795856
  - Non-zero count: 39986887.0


- age_over_64:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.1797574335597357
  - Median: 0.0
  - Stddev: 0.4128768716054247
  - Non-zero count: 11770257.0


- age_under_18:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.20955580036853289
  - Median: 0.0
  - Stddev: 0.41734889359818766
  - Non-zero count: 13721411.0


- birth_year:
  - Type: float
  - Entity: person
  - Description: The birth year of the person
  - Mean: 1981.1790208565233
  - Median: 1981.9896516040008
  - Stddev: 23.953073501586914
  - Non-zero count: 65478555.0


- gender:
  - Type: Categorical
  - Entity: person
  - Description: Gender of the person


- in_FE:
  - Type: bool
  - Entity: person
  - Description: Whether this person is in Further Education
  - Mean: 0.0011779734601656984
  - Median: 0.0
  - Stddev: 0.03194010855649921
  - Non-zero count: 77132.0


- in_HE:
  - Type: bool
  - Entity: person
  - Description: label
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- in_social_housing:
  - Type: bool
  - Entity: person
  - Description: Whether this person lives in social housing
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- is_WA_adult:
  - Type: bool
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6209431775029244
  - Median: 1.0
  - Stddev: 0.49507030025428744
  - Non-zero count: 40658462.0


- is_adult:
  - Type: bool
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.7904441996314672
  - Median: 1.0
  - Stddev: 0.41734889359818766
  - Non-zero count: 51757144.0


- is_benunit_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5352827807516523
  - Median: 1.0
  - Stddev: 0.49960493110885895
  - Non-zero count: 35049543.0


- is_child:
  - Type: bool
  - Entity: person
  - Description: Whether this person is a child
  - Mean: 0.20955580036853289
  - Median: 0.0
  - Stddev: 0.41734889359818766
  - Non-zero count: 13721411.0


- is_female:
  - Type: bool
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- is_household_head:
  - Type: bool
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.424983874491427
  - Median: 0.0
  - Stddev: 0.4969542878692517
  - Non-zero count: 27827330.0


- is_male:
  - Type: bool
  - Entity: person
  - Description: Whether the person is male
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- is_older_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.04104539264802041
  - Median: 0.0
  - Stddev: 0.20292526183413828
  - Non-zero count: 2687593.0


- is_young_child:
  - Type: bool
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.16851040772051246
  - Median: 0.0
  - Stddev: 0.3855266696976094
  - Non-zero count: 11033818.0


- over_16:
  - Type: bool
  - Entity: person
  - Description: Whether the person is over 16
  - Mean: 0.8106907826539544
  - Median: 1.0
  - Stddev: 0.4030461281464062
  - Non-zero count: 53082861.0


- people:
  - Type: float
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- person_id:
  - Type: float
  - Entity: person
  - Description: ID for the person
  - Mean: 967186.0298002901
  - Median: 971928.5385327698
  - Stddev: 552841.8125
  - Non-zero count: 65478555.0


- person_weight:
  - Type: float
  - Entity: person
  - Description: Weight factor for the person
  - Mean: 2260.5343767741974
  - Median: 1658.0
  - Stddev: 1061.07763671875
  - Non-zero count: 65478555.0


- benunit_id:
  - Type: float
  - Entity: benunit
  - Description: ID for the family
  - Mean: 966680.8051235396
  - Median: 970413.9652394106
  - Stddev: 554790.6875
  - Non-zero count: 35049543.0


- benunit_is_renting:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is renting
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 35049543.0


- benunit_tenure_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Tenure type of the family's household


- benunit_weight:
  - Type: float
  - Entity: benunit
  - Description: Weight factor for the benefit unit
  - Mean: 2420.2049674370933
  - Median: 1700.0
  - Stddev: 1157.133056640625
  - Non-zero count: 35049543.0


- eldest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 48.296058068431876
  - Median: 48.0
  - Stddev: 18.609134674072266
  - Non-zero count: 35049543.0


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: -inf
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7508306.0


- families:
  - Type: float
  - Entity: benunit
  - Description: Variable holding families
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 35049543.0


- family_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Family composition


- is_married:
  - Type: bool
  - Entity: benunit
  - Description: Whether the benefit unit adults are married
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_adults:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 1.4766852737566365
  - Median: 1.0
  - Stddev: 0.5187704924003915
  - Non-zero count: 34937614.0


- num_children:
  - Type: int
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.3914861600335274
  - Median: 0.0
  - Stddev: 0.8757651377677853
  - Non-zero count: 7847569.0


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: 46.53864491186091
  - Median: 46.0
  - Stddev: 18.496339797973633
  - Non-zero count: 35049543.0


- youngest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: inf
  - Median: inf
  - Stddev: nan
  - Non-zero count: 34249935.0


- BRMA:
  - Type: Categorical
  - Entity: household
  - Description: Broad Rental Market Area


- local_authority:
  - Type: Categorical
  - Entity: household
  - Description: The Local Authority for the household


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
  - Mean: 0.9197476571536559
  - Median: 1.0
  - Stddev: 0.33456021547317505
  - Non-zero count: 27828787.0


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 0.9539370030046596
  - Median: 1.0
  - Stddev: 0.28753864765167236
  - Non-zero count: 27828787.0


- household_id:
  - Type: float
  - Entity: household
  - Description: ID for the household
  - Mean: 962462.8003009977
  - Median: 967560.3104961187
  - Stddev: 553496.3125
  - Non-zero count: 27828787.0


- household_weight:
  - Type: float
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 2295.636794194443
  - Median: 1561.0
  - Stddev: 1106.8741455078125
  - Non-zero count: 27828787.0


- households:
  - Type: float
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 27828787.0


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
  - Mean: 2.767869867989575
  - Median: 3.0
  - Stddev: 1.0072964082020706
  - Non-zero count: 27828787.0


- region:
  - Type: Categorical
  - Entity: household
  - Description: Region of the UK


- tenure_type:
  - Type: Categorical
  - Entity: household
  - Description: Tenure type of the household


- B_benunit_id:
  - Type: float
  - Entity: benunit
  - Description: None
  - Mean: 966680.8051235396
  - Median: 970413.9652394106
  - Stddev: 554790.6875
  - Non-zero count: 35049543.0


- B_household_id:
  - Type: float
  - Entity: benunit
  - Description: None
  - Mean: 966667.9426833041
  - Median: 970400.0
  - Stddev: 554790.6875
  - Non-zero count: 35049543.0


- H_household_id:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 962462.8003009977
  - Median: 967560.3104961187
  - Stddev: 553496.3125
  - Non-zero count: 27828787.0


- P_benunit_id:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 96718.39929984711
  - Median: 97192.560048806
  - Stddev: 55284.17578125
  - Non-zero count: 65478555.0


- P_household_id:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 9671.723503580675
  - Median: 9719.06222764511
  - Stddev: 5528.41748046875
  - Non-zero count: 65478555.0


- P_person_id:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 967186.0298002901
  - Median: 971928.5385327698
  - Stddev: 552841.8125
  - Non-zero count: 65478555.0


- P_role:
  - Type: Categorical
  - Entity: person
  - Description: None


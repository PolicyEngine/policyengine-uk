# OpenFisca-UK Variable Statistics

All statistics generated from the 2018-19 Family Resources Survey, with simulation turned on.


- childcare_cost:
  - Type: float
  - Entity: person
  - Description: Cost of childcare
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- council_tax:
  - Type: float
  - Entity: household
  - Description: Council Tax
  - Mean: 1356.8126552190693
  - Median: 1322.6252799045665
  - Stddev: 564.69921875
  - Non-zero count: 27802676.0


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


- weekly_childcare_cost:
  - Type: float
  - Entity: person
  - Description: Average cost of childcare
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- weekly_rent:
  - Type: float
  - Entity: household
  - Description: Weekly average rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- earned_income:
  - Type: float
  - Entity: person
  - Description: Total earned income
  - Mean: 16056.016278478626
  - Median: 6292.0
  - Stddev: 110728.6484375
  - Non-zero count: 38513248.0


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_household_net_income:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, before housing costs
  - Mean: 40244.48130392647
  - Median: 29311.497878216556
  - Stddev: 161471.0
  - Non-zero count: 27623492.0


- equiv_household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Equivalised household net income, after housing costs
  - Mean: 42658.176979008866
  - Median: 30355.466796875
  - Stddev: 161820.296875
  - Non-zero count: 27610965.0


- gross_income:
  - Type: float
  - Entity: person
  - Description: Gross income, including benefits
  - Mean: 19866.050948428227
  - Median: 13961.6396484375
  - Stddev: 110775.9609375
  - Non-zero count: 48949439.0


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
  - Description: Household net income, before housing costs
  - Mean: 37446.96544725269
  - Median: 28612.882850698876
  - Stddev: 162588.46875
  - Non-zero count: 27623492.0


- household_net_income_ahc:
  - Type: float
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: 37305.70712646376
  - Median: 28455.962625018317
  - Stddev: 162596.765625
  - Non-zero count: 27610965.0


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
  - Mean: 16463.312156686516
  - Median: 13423.768255196634
  - Stddev: 108488.5390625
  - Non-zero count: 48879248.0


- self_employment_income:
  - Type: float
  - Entity: person
  - Description: Income from self-employmen. Different to trading profits
  - Mean: 2430.8939669713236
  - Median: 0.0
  - Stddev: 108727.0078125
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
  - Type: float
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.0002480812229286367
  - Median: 0.0
  - Stddev: 0.01736753061413765
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
  - Type: float
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.08721611577075342
  - Median: 0.0
  - Stddev: 0.3237573504447937
  - Non-zero count: 2916234.0


- num_disabled_children:
  - Type: float
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.001217505175459777
  - Median: 0.0
  - Stddev: 0.03835635632276535
  - Non-zero count: 40069.0


- num_enhanced_disabled_adults:
  - Type: float
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0004634582539350085
  - Median: 0.0
  - Stddev: 0.024080926552414894
  - Non-zero count: 16244.0


- num_enhanced_disabled_children:
  - Type: float
  - Entity: benunit
  - Description: Number of enhanced disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_severely_disabled_adults:
  - Type: float
  - Entity: benunit
  - Description: Number of severely disabled adults
  - Mean: 0.05480151338920453
  - Median: 0.0
  - Stddev: 0.260103315114975
  - Non-zero count: 1852755.0


- num_severely_disabled_children:
  - Type: float
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0006105928399694113
  - Median: 0.0
  - Stddev: 0.025865908712148666
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
  - Type: float
  - Entity: benunit
  - Description: The number of carers for benefits purposes in the family
  - Mean: 0.020958361711021452
  - Median: 0.0
  - Stddev: 0.15879395604133606
  - Non-zero count: 723880.0


- benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated
  - Mean: 2845.5681535109284
  - Median: 0.0
  - Stddev: 4930.65283203125
  - Non-zero count: 25569878.0


- benefits_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 88.64748305452201
  - Median: 0.0
  - Stddev: 2506.93310546875
  - Non-zero count: 11834859.0


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
  - Mean: 0.7932985602693878
  - Median: 1.0
  - Stddev: 0.4039963483810425
  - Non-zero count: 27804752.0


- family_benefits:
  - Type: float
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 1090.7457238025293
  - Median: 0.0
  - Stddev: 2808.285888671875
  - Non-zero count: 15157150.0


- family_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 896.2004371064002
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
  - Mean: 0.4740214729761241
  - Median: 0.0
  - Stddev: 0.4998159694855555
  - Non-zero count: 16614236.0


- is_lone_parent:
  - Type: float
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.05618173109988909
  - Median: 0.0
  - Stddev: 0.25292670726776123
  - Non-zero count: 1969144.0


- is_single:
  - Type: bool
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5259785270238759
  - Median: 1.0
  - Stddev: 0.4998159694855555
  - Non-zero count: 18435307.0


- is_single_person:
  - Type: float
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.472990246976972
  - Median: 0.0
  - Stddev: 0.4972909092903137
  - Non-zero count: 16578092.0


- other_benefits:
  - Type: float
  - Entity: person
  - Description: Income from benefits not modelled or detailed in the model
  - Mean: -88.64748200843897
  - Median: 0.0
  - Stddev: 2506.93310546875
  - Non-zero count: 17522918.0


- personal_benefits:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1754.8224291901981
  - Median: 0.0
  - Stddev: 3929.2294921875
  - Non-zero count: 14627495.0


- personal_benefits_reported:
  - Type: float
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1711.088488156751
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
  - Mean: 301.673323378532
  - Median: 0.0
  - Stddev: 712.9520874023438
  - Non-zero count: 6836888.0


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
  - Mean: 0.6349119872975234
  - Median: 1.0
  - Stddev: 0.47846810658797023
  - Non-zero count: 22253375.0


- housing_benefit:
  - Type: float
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 701.1057514256474
  - Median: 0.0
  - Stddev: 1777.86474609375
  - Non-zero count: 5441494.0


- housing_benefit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 2232.0541327059523
  - Median: 0.0
  - Stddev: 3861.143798828125
  - Non-zero count: 13041070.0


- housing_benefit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 24586.895358390266
  - Median: 18956.301267484807
  - Stddev: 21984.78515625
  - Non-zero count: 31970932.0


- housing_benefit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.3720753220662535
  - Median: 0.0
  - Stddev: 0.4805899012216294
  - Non-zero count: 13041070.0


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
  - Mean: 106.562602073298
  - Median: 0.0
  - Stddev: 707.0809326171875
  - Non-zero count: 1776255.0


- pension_credit_GC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount
  - Mean: 92.99559577537462
  - Median: 0.0
  - Stddev: 687.2549438476562
  - Non-zero count: 1264922.0


- pension_credit_MG:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 1686.3055314240519
  - Median: 0.0
  - Stddev: 4680.75048828125
  - Non-zero count: 5088596.0


- pension_credit_SC:
  - Type: float
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 13.567007015503963
  - Median: 0.0
  - Stddev: 97.10173034667969
  - Non-zero count: 1074527.0


- pension_credit_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 26000.025983469728
  - Median: 19799.2164792937
  - Stddev: 23499.564453125
  - Non-zero count: 32332538.0


- pension_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Pension Credit
  - Mean: 0.21895001598166344
  - Median: 0.0
  - Stddev: 0.44514989382311815
  - Non-zero count: 7674098.0


- pension_credit_reported:
  - Type: float
  - Entity: person
  - Description: Reported amount of Pension Credit per week
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
  - Mean: 0.09259601473263146
  - Median: 0.0
  - Stddev: 0.314852658198175
  - Non-zero count: 3245448.0


- BRMA_LHA_rate:
  - Type: float
  - Entity: benunit
  - Description: LHA Rate
  - Mean: 6936.044274963174
  - Median: 6619.080078125
  - Stddev: 652.1345825195312
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
  - Mean: 2069.625121191426
  - Median: 0.0
  - Stddev: 2740.007568359375
  - Non-zero count: 12868102.0


- LHA_category:
  - Type: Categorical
  - Entity: benunit
  - Description: LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms


- LHA_eligible:
  - Type: float
  - Entity: benunit
  - Description: Whether eligible for Local Housing Allowance
  - Mean: 0.1963764263631055
  - Median: 0.0
  - Stddev: 0.3740248382091522
  - Non-zero count: 6882904.0


- JSA:
  - Type: float
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 18.313859020358137
  - Median: 0.0
  - Stddev: 267.9992980957031
  - Non-zero count: 185107.0


- JSA_income:
  - Type: float
  - Entity: benunit
  - Description: Job Seeker's Allowance (income-based)
  - Mean: 12.642529431281478
  - Median: 0.0
  - Stddev: 227.42091369628906
  - Non-zero count: 154888.0


- JSA_income_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 18.394719107599116
  - Median: 0.0
  - Stddev: 289.8351745605469
  - Non-zero count: 172909.0


- JSA_income_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 25039.00119177663
  - Median: 19098.638844645113
  - Stddev: 22732.783203125
  - Non-zero count: 32015889.0


- JSA_income_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for JSA (income-based)
  - Mean: 0.02279927016452112
  - Median: 0.0
  - Stddev: 0.13766831158248036
  - Non-zero count: 799104.0


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
  - Mean: 2.660680197741808
  - Median: 0.0
  - Stddev: 104.89398193359375
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
  - Mean: 452.3119867782584
  - Median: 0.0
  - Stddev: 1880.54833984375
  - Non-zero count: 2402900.0


- CTC_severely_disabled_child_element:
  - Type: float
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.6268220102042414
  - Median: 0.0
  - Stddev: 27.986364364624023
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
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


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
  - Mean: 153.0644533653406
  - Median: 0.0
  - Stddev: 892.9992065429688
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
  - Mean: 362.50900650358426
  - Median: 0.0
  - Stddev: 1671.01171875
  - Non-zero count: 2155305.0


- child_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit (reported amount)
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
  - Type: float
  - Entity: benunit
  - Description: Whether the family is eligible for WTC
  - Mean: 0.5106053165942849
  - Median: 1.0
  - Stddev: 0.4999896287918091
  - Non-zero count: 17896483.0


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
  - Mean: 430.421050619223
  - Median: 0.0
  - Stddev: 1990.0296630859375
  - Non-zero count: 2267898.0


- tax_credits_applicable_income:
  - Type: float
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 30804.310059803407
  - Median: 20921.164329769734
  - Stddev: 35270.83203125
  - Non-zero count: 29827673.0


- tax_credits_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 10372.383531329602
  - Median: 5791.655378596306
  - Stddev: 14146.7548828125
  - Non-zero count: 27776290.0


- working_tax_credit:
  - Type: float
  - Entity: benunit
  - Description: Amount of Working Tax Credit entitled to
  - Mean: 67.91204246305571
  - Median: 0.0
  - Stddev: 535.6246948242188
  - Non-zero count: 878028.0


- working_tax_credit_reported:
  - Type: float
  - Entity: person
  - Description: Working Tax Credit (reported amount)
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
  - Mean: 26.636060542961143
  - Median: 0.0
  - Stddev: 352.4854736328125
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
  - Mean: 25039.00119177663
  - Median: 19098.638844645113
  - Stddev: 22732.783203125
  - Non-zero count: 32015889.0


- income_support_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.03459856808974656
  - Median: 0.0
  - Stddev: 0.201198662541204
  - Non-zero count: 1212664.0


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
  - Mean: 2121.0603855996883
  - Median: 0.0
  - Stddev: 2862.447265625
  - Non-zero count: 12868102.0


- UC_personal_allowance:
  - Type: float
  - Entity: benunit
  - Description: Personal allowance for Universal Credit
  - Mean: 4718.705951060894
  - Median: 3813.840087890625
  - Stddev: 1164.7320556640625
  - Non-zero count: 35049543.0


- UC_premiums:
  - Type: float
  - Entity: benunit
  - Description: Premiums for Universal Credit
  - Mean: 1342.6569336846517
  - Median: 0.0
  - Stddev: 2484.4580078125
  - Non-zero count: 10588121.0


- claims_UC:
  - Type: bool
  - Entity: benunit
  - Description: Whether this family is imputed to claim UC
  - Mean: 0.22242298565775878
  - Median: 0.0
  - Stddev: 0.4149079437199698
  - Non-zero count: 7795824.0


- universal_credit:
  - Type: float
  - Entity: benunit
  - Description: Universal Credit amount
  - Mean: 291.3858749537467
  - Median: 0.0
  - Stddev: 1478.595947265625
  - Non-zero count: 1833093.0


- universal_credit_applicable_amount:
  - Type: float
  - Entity: benunit
  - Description: Relevant income for Universal Credit
  - Mean: 8182.423166009792
  - Median: 7138.7998046875
  - Stddev: 4262.4443359375
  - Non-zero count: 35049543.0


- universal_credit_eligible:
  - Type: bool
  - Entity: benunit
  - Description: Whether eligible for Universal Credit
  - Mean: 0.6064413735722602
  - Median: 1.0
  - Stddev: 0.4974836933785528
  - Non-zero count: 21255493.0


- universal_credit_income_reduction:
  - Type: float
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 15760.23601517101
  - Median: 11638.236886302348
  - Stddev: 16192.298828125
  - Non-zero count: 29595972.0


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
  - Mean: 122.76190526008546
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
  - Mean: 0.1797574335597357
  - Median: 0.0
  - Stddev: 0.4128768716054247
  - Non-zero count: 11770257.0


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
  - Mean: 65.0
  - Median: 65.0
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
  - Description: Total tax liability
  - Mean: 3402.4363985100103
  - Median: 0.0
  - Stddev: 8472.6298828125
  - Non-zero count: 32581952.0


- tax_modelling:
  - Type: float
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: -383.67208827965857
  - Median: 0.0
  - Stddev: 26898.91015625
  - Non-zero count: 18579651.0


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
  - Mean: 60.438228113158694
  - Median: 0.0
  - Stddev: 385.0706787109375
  - Non-zero count: 2660037.0


- national_insurance:
  - Type: float
  - Entity: person
  - Description: Total amount of National Insurance liability for this person
  - Mean: 930.8829263768764
  - Median: 0.0
  - Stddev: 1489.799560546875
  - Non-zero count: 26580479.0


- NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 6.9926194061902205
  - Median: 0.0
  - Stddev: 30.372146606445312
  - Non-zero count: 2984789.0


- weekly_NI_class_2:
  - Type: float
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 6.9926194061902205
  - Median: 0.0
  - Stddev: 30.372146606445312
  - Non-zero count: 2984789.0


- NI_exempt:
  - Type: bool
  - Entity: person
  - Description: Whether is exempt from National Insurance
  - Mean: 0.3690666509057813
  - Median: 0.0
  - Stddev: 0.4938962976514026
  - Non-zero count: 24165951.0


- employee_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 863.4520789833097
  - Median: 0.0
  - Stddev: 1462.4686279296875
  - Non-zero count: 23728103.0


- employer_NI:
  - Type: float
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 951.8712249600932
  - Median: 0.0
  - Stddev: 1559.97412109375
  - Non-zero count: 23728103.0


- employer_NI_class_1:
  - Type: float
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 951.8712249600932
  - Median: 0.0
  - Stddev: 1559.97412109375
  - Non-zero count: 23728103.0


- total_NI:
  - Type: float
  - Entity: person
  - Description: Total National Insurance contributions by employers and employees
  - Mean: 1882.7541200020557
  - Median: 0.0
  - Stddev: 3011.73583984375
  - Non-zero count: 26580479.0


- dividend_income:
  - Type: float
  - Entity: person
  - Description: Income from dividends
  - Mean: 150.93934837497827
  - Median: 0.0
  - Stddev: 2143.9443359375
  - Non-zero count: 3636930.0


- employment_income:
  - Type: float
  - Entity: person
  - Description: Income from employment
  - Mean: 11991.145628164344
  - Median: 0.0
  - Stddev: 21684.73828125
  - Non-zero count: 26715128.0


- pension_income:
  - Type: float
  - Entity: person
  - Description: Income from pensions
  - Mean: 1633.9766744699848
  - Median: 0.0
  - Stddev: 6817.41455078125
  - Non-zero count: 9582497.0


- property_income:
  - Type: float
  - Entity: person
  - Description: Income from rental of property
  - Mean: 179.31676262893595
  - Median: 0.0
  - Stddev: 1702.2877197265625
  - Non-zero count: 1874106.0


- savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Income from interest on savings
  - Mean: 151.55951236428982
  - Median: 0.0
  - Stddev: 1108.103515625
  - Non-zero count: 13858193.0


- social_security_income:
  - Type: float
  - Entity: person
  - Description: Income from social security for tax purposes
  - Mean: 1421.106906374954
  - Median: 0.0
  - Stddev: 3293.616455078125
  - Non-zero count: 12962546.0


- trading_income:
  - Type: float
  - Entity: person
  - Description: Income from trading profits
  - Mean: 1266.5595820533408
  - Median: 0.0
  - Stddev: 9073.2333984375
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
  - Mean: 16658.788133388498
  - Median: 9874.737734220907
  - Stddev: 23577.8203125
  - Non-zero count: 44360694.0


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
  - Mean: 1631.7102149967977
  - Median: 0.0
  - Stddev: 1766.8282470703125
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
  - Mean: 150.93934837497827
  - Median: 0.0
  - Stddev: 2143.9443359375
  - Non-zero count: 3636930.0


- taxable_employment_income:
  - Type: float
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 11989.279190090512
  - Median: 0.0
  - Stddev: 21680.869140625
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
  - Mean: 1633.9766744699848
  - Median: 0.0
  - Stddev: 6817.41455078125
  - Non-zero count: 9582497.0


- taxable_property_income:
  - Type: float
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 154.46146788367562
  - Median: 0.0
  - Stddev: 1609.9310302734375
  - Non-zero count: 1401037.0


- taxable_savings_interest_income:
  - Type: float
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 99.13499076680054
  - Median: 0.0
  - Stddev: 855.8574829101562
  - Non-zero count: 13221462.0


- taxable_social_security_income:
  - Type: float
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1421.106906374954
  - Median: 0.0
  - Stddev: 3293.616455078125
  - Non-zero count: 12962546.0


- taxable_trading_income:
  - Type: float
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1209.8894926927082
  - Median: 0.0
  - Stddev: 8957.953125
  - Non-zero count: 3683806.0


- total_income:
  - Type: float
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 17277.255338817984
  - Median: 10881.935346554488
  - Stddev: 23732.1953125
  - Non-zero count: 46213584.0


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
  - Mean: 11742.10039913171
  - Median: 11850.0
  - Stddev: 1014.4673461914062
  - Non-zero count: 65018695.0


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
  - Mean: 39970.131252834886
  - Median: 40000.0
  - Stddev: 825.0675048828125
  - Non-zero count: 65478555.0


- personal_allowance:
  - Type: float
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 11742.10039913171
  - Median: 11850.0
  - Stddev: 1014.4673461914062
  - Non-zero count: 65018695.0


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
  - Mean: 24.85529494629617
  - Median: 0.0
  - Stddev: 146.9286651611328
  - Non-zero count: 1874106.0


- savings_allowance:
  - Type: float
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 960.5914256965506
  - Median: 1000.0
  - Stddev: 137.57688903808594
  - Non-zero count: 65178135.0


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
  - Mean: 56.67008873709999
  - Median: 0.0
  - Stddev: 219.7454071044922
  - Non-zero count: 3738272.0


- CB_HITC:
  - Type: float
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 30.002068491550613
  - Median: 0.0
  - Stddev: 226.18800354003906
  - Non-zero count: 1435289.0


- add_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 305.28661604600694
  - Median: 0.0
  - Stddev: 6329.86376953125
  - Non-zero count: 282559.0


- add_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 137.37897353010356
  - Median: 0.0
  - Stddev: 2848.438720703125
  - Non-zero count: 282559.0


- add_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 2.8528091320840536
  - Median: 0.0
  - Stddev: 464.1643981933594
  - Non-zero count: 5475.0


- basic_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7313.130674358058
  - Median: 0.0
  - Stddev: 10849.0556640625
  - Non-zero count: 29980369.0


- basic_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1462.6260935883968
  - Median: 0.0
  - Stddev: 2169.81103515625
  - Non-zero count: 29979227.0


- basic_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 24.83412238802611
  - Median: 0.0
  - Stddev: 477.2981872558594
  - Non-zero count: 288807.0


- basic_rate_savings_income_pre_starter:
  - Type: float
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 36.076272787560335
  - Median: 0.0
  - Stddev: 503.7690734863281
  - Non-zero count: 1007004.0


- dividend_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 23.18591978776259
  - Median: 0.0
  - Stddev: 564.5613403320312
  - Non-zero count: 688775.0


- earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2410.205776172658
  - Median: 0.0
  - Stddev: 7185.20751953125
  - Non-zero count: 29979227.0


- earned_taxable_income:
  - Type: float
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 9641.083860190773
  - Median: 0.0
  - Stddev: 21196.44140625
  - Non-zero count: 29980369.0


- higher_rate_earned_income:
  - Type: float
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 2022.666553936109
  - Median: 0.0
  - Stddev: 10672.171875
  - Non-zero count: 4683250.0


- higher_rate_earned_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 809.066640923782
  - Median: 0.0
  - Stddev: 4268.869140625
  - Non-zero count: 4683250.0


- higher_rate_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 4.772610437982899
  - Median: 0.0
  - Stddev: 238.07984924316406
  - Non-zero count: 61753.0


- income_tax:
  - Type: float
  - Entity: person
  - Description: Income Tax
  - Mean: 2471.5533939603583
  - Median: 0.0
  - Stddev: 7383.869140625
  - Non-zero count: 30259914.0


- income_tax_pre_charges:
  - Type: float
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2441.5513303003577
  - Median: 0.0
  - Stddev: 7274.04541015625
  - Non-zero count: 30259914.0


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
  - Mean: 0.04739589931390514
  - Median: 0.0
  - Stddev: 0.20050378143787384
  - Non-zero count: 3103415.0


- savings_income_tax:
  - Type: float
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 8.159633651199572
  - Median: 0.0
  - Stddev: 253.1320037841797
  - Non-zero count: 335914.0


- savings_starter_rate_income:
  - Type: float
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4972.995106826174
  - Median: 5000.0
  - Stddev: 313.5854187011719
  - Non-zero count: 65325460.0


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: float
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 115.13006462012619
  - Median: 0.0
  - Stddev: 2025.879150390625
  - Non-zero count: 688775.0


- taxed_income:
  - Type: float
  - Entity: person
  - Description: Income which is taxed
  - Mean: 9788.673473481931
  - Median: 0.0
  - Stddev: 21475.759765625
  - Non-zero count: 30261056.0


- taxed_savings_income:
  - Type: float
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 32.459541818448294
  - Median: 0.0
  - Stddev: 726.8478393554688
  - Non-zero count: 335914.0


- in_deep_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), after housing costs
  - Mean: 0.02838262407915947
  - Median: 0.0
  - Stddev: 0.17774158011720206
  - Non-zero count: 789854.0


- in_deep_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in deep absolute poverty (below half the poverty line), before housing costs
  - Mean: 0.035745826794391006
  - Median: 0.0
  - Stddev: 0.19140002191729483
  - Non-zero count: 994763.0


- in_poverty_ahc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.10246206563009735
  - Median: 0.0
  - Stddev: 0.3255012214124028
  - Non-zero count: 2851395.0


- in_poverty_bhc:
  - Type: bool
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.17350422064748997
  - Median: 0.0
  - Stddev: 0.3948005326200802
  - Non-zero count: 4828412.0


- poverty_gap_ahc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: 439.1944622678835
  - Median: 0.0
  - Stddev: 1961.7154541015625
  - Non-zero count: 2851395.0


- poverty_gap_bhc:
  - Type: float
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: 811.2435207272774
  - Median: 0.0
  - Stddev: 2542.25439453125
  - Non-zero count: 4828412.0


- poverty_line_ahc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 12920.335034742067
  - Median: 14040.0
  - Stddev: 4705.5146484375
  - Non-zero count: 27828787.0


- poverty_line_bhc:
  - Type: float
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 15681.601448791727
  - Median: 16432.0
  - Stddev: 4731.8740234375
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
  - Mean: 0.16580420872146615
  - Median: 0.0
  - Stddev: 0.38437236528738367
  - Non-zero count: 10856620.0


- is_WA_adult:
  - Type: float
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6106867660717314
  - Median: 1.0
  - Stddev: 0.4967019557952881
  - Non-zero count: 39986887.0


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
  - Mean: 0.6153615637974906
  - Median: 1.0
  - Stddev: 0.48089963431862587
  - Non-zero count: 40292986.0


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
  - Mean: 0.38463843620250937
  - Median: 0.0
  - Stddev: 0.48089963431862587
  - Non-zero count: 25185569.0


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
  - Mean: 0.3720753220662535
  - Median: 0.0
  - Stddev: 0.4805899012216294
  - Non-zero count: 13041070.0


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
  - Mean: -inf
  - Median: 48.0
  - Stddev: nan
  - Non-zero count: 34937614.0


- eldest_child_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: -inf
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7620235.0


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
  - Type: float
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 1.4766852737566365
  - Median: 1.0
  - Stddev: 0.5187704563140869
  - Non-zero count: 34937614.0


- num_children:
  - Type: float
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 0.3914861600335274
  - Median: 0.0
  - Stddev: 0.8757651448249817
  - Non-zero count: 7847569.0


- relation_type:
  - Type: Categorical
  - Entity: benunit
  - Description: Whether single or a couple


- youngest_adult_age:
  - Type: float
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: inf
  - Median: 46.0
  - Stddev: nan
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
  - Mean: 0.9202517696554138
  - Median: 1.0
  - Stddev: 0.3351506292819977
  - Non-zero count: 27828787.0


- household_equivalisation_bhc:
  - Type: float
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 0.9543330914063199
  - Median: 1.0
  - Stddev: 0.2879670262336731
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
  - Type: float
  - Entity: household
  - Description: The number of bedrooms in the house
  - Mean: 2.767869867989575
  - Median: 3.0
  - Stddev: 1.0072964429855347
  - Non-zero count: 27828787.0


- region:
  - Type: Categorical
  - Entity: household
  - Description: Region of the UK


- tenure_type:
  - Type: Categorical
  - Entity: household
  - Description: Tenure type of the household


- H_BEDROOM6:
  - Type: int
  - Entity: household
  - Description: None
  - Mean: 2.767869867989575
  - Median: 3.0
  - Stddev: 1.0072964082020706
  - Non-zero count: 27828787.0


- H_TYPEACC:
  - Type: int
  - Entity: household
  - Description: None
  - Mean: 2.546842124308185
  - Median: 2.0
  - Stddev: 1.1519087874103213
  - Non-zero count: 27800268.0


- H_GVTREGNO:
  - Type: int
  - Entity: household
  - Description: None
  - Mean: 7.166110078746875
  - Median: 8.0
  - Stddev: 3.6844993222010674
  - Non-zero count: 27828787.0


- P_person_id:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 967186.0298002901
  - Median: 971928.5385327698
  - Stddev: 552841.8125
  - Non-zero count: 65478555.0


- B_benunit_id:
  - Type: float
  - Entity: benunit
  - Description: None
  - Mean: 966680.8051235396
  - Median: 970413.9652394106
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


- H_CTANNUAL:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 1356.8126552190693
  - Median: 1322.6252799045665
  - Stddev: 564.69921875
  - Non-zero count: 27802676.0


- H_GBHSCOST:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 79.4701191970746
  - Median: 57.0
  - Stddev: 104.29946899414062
  - Non-zero count: 27024466.0


- H_NIHSCOST:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 1.1882329617888123
  - Median: 0.0
  - Stddev: 19.913911819458008
  - Non-zero count: 711980.0


- H_HHRENT:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 50.96431518916006
  - Median: 0.0
  - Stddev: 102.36070251464844
  - Non-zero count: 9990064.0


- H_PTENTYP2:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 4.335349866309301
  - Median: 5.0
  - Stddev: 1.6638318300247192
  - Non-zero count: 27828787.0


- P_GROSS4:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1851.1850878047019
  - Median: 1471.0
  - Stddev: 1175.42041015625
  - Non-zero count: 51553959.0


- B_GROSS4:
  - Type: float
  - Entity: benunit
  - Description: None
  - Mean: 2420.2049674370933
  - Median: 1700.0
  - Stddev: 1157.133056640625
  - Non-zero count: 35049543.0


- H_GROSS4:
  - Type: float
  - Entity: household
  - Description: None
  - Mean: 2295.636794194443
  - Median: 1561.0
  - Stddev: 1106.8741455078125
  - Non-zero count: 27828787.0


- P_UGRSPAY:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 230.59893067401327
  - Median: 0.0
  - Stddev: 417.0141296386719
  - Non-zero count: 26715128.0


- P_UDEDUC1:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.032795925215169046
  - Median: 0.0
  - Stddev: 2.4196436405181885
  - Non-zero count: 35875.0


- P_INPENINC:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 31.422628355192018
  - Median: 0.0
  - Stddev: 131.1041259765625
  - Non-zero count: 9582497.0


- P_PROFIT1:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 38.28401599975714
  - Median: 0.0
  - Stddev: 2083.122802734375
  - Non-zero count: 3124544.0


- P_PROFIT2:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.05099121384092853
  - Median: 0.0
  - Stddev: 0.2313183695077896
  - Non-zero count: 3125390.0


- P_ACCINT_ACCOUNT_CODE_1:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.2063356660072719
  - Median: 0.0
  - Stddev: 1.9136378765106201
  - Non-zero count: 9798460.0


- P_ACCINT_ACCOUNT_CODE_2:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.03769478836367002
  - Median: 0.0
  - Stddev: 0.943744421005249
  - Non-zero count: 593651.0


- P_ACCINT_ACCOUNT_CODE_3:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.061122441682239924
  - Median: 0.0
  - Stddev: 1.6703026294708252
  - Non-zero count: 532022.0


- P_ACCINT_ACCOUNT_CODE_4:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_5:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.6919241145708713
  - Median: 0.0
  - Stddev: 10.904876708984375
  - Non-zero count: 11267721.0


- P_ACCINT_ACCOUNT_CODE_6:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.05740206688455437
  - Median: 0.0
  - Stddev: 3.2839341163635254
  - Non-zero count: 70161.0


- P_ACCINT_ACCOUNT_CODE_7:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.5795039328848671
  - Median: 0.0
  - Stddev: 16.312679290771484
  - Non-zero count: 576737.0


- P_ACCINT_ACCOUNT_CODE_8:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 2.32166973225066
  - Median: 0.0
  - Stddev: 34.869903564453125
  - Non-zero count: 3302775.0


- P_ACCINT_ACCOUNT_CODE_9:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_10:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_11:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_12:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_13:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_14:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_15:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_16:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_17:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_18:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_19:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_21:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.9582330271665565
  - Median: 0.0
  - Stddev: 11.621086120605469
  - Non-zero count: 8990422.0


- P_ACCINT_ACCOUNT_CODE_22:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_23:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_24:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0015240155939398048
  - Median: 0.0
  - Stddev: 0.3700278401374817
  - Non-zero count: 8101.0


- P_ACCINT_ACCOUNT_CODE_25:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_26:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_27:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.019892870445331962
  - Median: 0.0
  - Stddev: 1.8494071960449219
  - Non-zero count: 392809.0


- P_ACCINT_ACCOUNT_CODE_28:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.001968432542920646
  - Median: 0.0
  - Stddev: 0.11600244045257568
  - Non-zero count: 225999.0


- P_ACCINT_ACCOUNT_CODE_29:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_30:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- H_SUBLET:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_INDINC:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 380.33410760209966
  - Median: 269.0
  - Stddev: 2129.709228515625
  - Non-zero count: 49349156.0


- P_NINDINC:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 307.5243296679348
  - Median: 250.0
  - Stddev: 2136.50732421875
  - Non-zero count: 49004666.0


- P_CHINCDV:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.42692340857738303
  - Median: 0.0
  - Stddev: 6.605282783508301
  - Non-zero count: 635049.0


- P_BENAMT_BENEFIT_CODE_1:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.2275568830377608
  - Median: 0.0
  - Stddev: 10.366942405700684
  - Non-zero count: 1317063.0


- P_BENAMT_BENEFIT_CODE_2:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.7911450278971391
  - Median: 0.0
  - Stddev: 7.425052165985107
  - Non-zero count: 1106456.0


- P_BENAMT_BENEFIT_CODE_3:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 3.0723509365212776
  - Median: 0.0
  - Stddev: 10.529207229614258
  - Non-zero count: 6424339.0


- P_BENAMT_BENEFIT_CODE_4:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.9049046118928616
  - Median: 0.0
  - Stddev: 10.527260780334473
  - Non-zero count: 1132019.0


- P_BENAMT_BENEFIT_CODE_5:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 25.370474520525384
  - Median: 0.0
  - Stddev: 62.55794143676758
  - Non-zero count: 11554244.0


- P_BENAMT_BENEFIT_CODE_6:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.06880282635713673
  - Median: 0.0
  - Stddev: 3.2038633823394775
  - Non-zero count: 57115.0


- P_BENAMT_BENEFIT_CODE_8:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.07286318615639763
  - Median: 0.0
  - Stddev: 3.5465967655181885
  - Non-zero count: 61193.0


- P_BENAMT_BENEFIT_CODE_9:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.13079780362903135
  - Median: 0.0
  - Stddev: 4.628000736236572
  - Non-zero count: 95401.0


- P_BENAMT_BENEFIT_CODE_10:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.009453675627092449
  - Median: 0.0
  - Stddev: 1.1468000411987305
  - Non-zero count: 11916.0


- P_BENAMT_BENEFIT_CODE_12:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.9139006247224473
  - Median: 0.0
  - Stddev: 9.066205024719238
  - Non-zero count: 810520.0


- P_BENAMT_BENEFIT_CODE_13:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.7337793547113397
  - Median: 0.0
  - Stddev: 7.411696910858154
  - Non-zero count: 734581.0


- P_BENAMT_BENEFIT_CODE_14:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.05838008032884049
  - Median: 0.0
  - Stddev: 1.890191674232483
  - Non-zero count: 56433.0


- P_BENAMT_BENEFIT_CODE_1014:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.3504847123509064
  - Median: 0.0
  - Stddev: 5.626164436340332
  - Non-zero count: 289811.0


- P_BENAMT_BENEFIT_CODE_15:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.1320404469136879
  - Median: 0.0
  - Stddev: 3.5142064094543457
  - Non-zero count: 151046.0


- P_BENAMT_BENEFIT_CODE_16:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.144926576174
  - Median: 0.0
  - Stddev: 12.481842041015625
  - Non-zero count: 669633.0


- P_BENAMT_BENEFIT_CODE_17:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.021419911629228756
  - Median: 0.0
  - Stddev: 1.744089961051941
  - Non-zero count: 14487.0


- P_BENAMT_BENEFIT_CODE_19:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.6090777865936211
  - Median: 0.0
  - Stddev: 8.392367362976074
  - Non-zero count: 517051.0


- P_BENAMT_BENEFIT_CODE_21:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.06012208493245765
  - Median: 0.0
  - Stddev: 2.42122745513916
  - Non-zero count: 30560.0


- P_BENAMT_BENEFIT_CODE_22:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.07108052399751338
  - Median: 0.0
  - Stddev: 7.067324638366699
  - Non-zero count: 10340.0


- P_BENAMT_BENEFIT_CODE_24:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.42854038619502804
  - Median: 0.0
  - Stddev: 30.246965408325195
  - Non-zero count: 18259.0


- P_BENAMT_BENEFIT_CODE_30:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.008631345017299778
  - Median: 0.0
  - Stddev: 0.608738124370575
  - Non-zero count: 7698.0


- P_BENAMT_BENEFIT_CODE_31:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.013204963646782756
  - Median: 0.0
  - Stddev: 1.410159945487976
  - Non-zero count: 11431.0


- P_BENAMT_BENEFIT_CODE_32:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0011184683053259944
  - Median: 0.0
  - Stddev: 0.2771540582180023
  - Non-zero count: 1273.0


- P_BENAMT_BENEFIT_CODE_33:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.1760431565171563
  - Median: 0.0
  - Stddev: 19.879169464111328
  - Non-zero count: 46066.0


- P_BENAMT_BENEFIT_CODE_34:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.03970279672532791
  - Median: 0.0
  - Stddev: 9.636493682861328
  - Non-zero count: 2857.0


- P_BENAMT_BENEFIT_CODE_35:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.004752815044266367
  - Median: 0.0
  - Stddev: 0.5301610231399536
  - Non-zero count: 8337.0


- P_BENAMT_BENEFIT_CODE_36:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0034614432716524204
  - Median: 0.0
  - Stddev: 0.41830483078956604
  - Non-zero count: 4316.0


- P_BENAMT_BENEFIT_CODE_37:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.008931200751937705
  - Median: 0.0
  - Stddev: 2.154486656188965
  - Non-zero count: 2834.0


- P_BENAMT_BENEFIT_CODE_61:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.004021637587212117
  - Median: 0.0
  - Stddev: 0.3991543650627136
  - Non-zero count: 9175.0


- P_BENAMT_BENEFIT_CODE_62:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 30.420323111895186
  - Median: 0.0
  - Stddev: 75.54754638671875
  - Non-zero count: 11743418.0


- P_BENAMT_BENEFIT_CODE_65:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.008854502740311921
  - Median: 0.0
  - Stddev: 0.5729060769081116
  - Non-zero count: 57795.0


- P_BENAMT_BENEFIT_CODE_66:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.019223014090261694
  - Median: 0.0
  - Stddev: 0.7371615171432495
  - Non-zero count: 108848.0


- P_BENAMT_BENEFIT_CODE_69:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0361674351824593
  - Median: 0.0
  - Stddev: 1.1040217876434326
  - Non-zero count: 144318.0


- P_BENAMT_BENEFIT_CODE_70:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.04444583712293472
  - Median: 0.0
  - Stddev: 1.0492849349975586
  - Non-zero count: 193427.0


- P_BENAMT_BENEFIT_CODE_78:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.004786361038611826
  - Median: 0.0
  - Stddev: 0.7367099523544312
  - Non-zero count: 2908.0


- P_BENAMT_BENEFIT_CODE_81:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.06146516551381192
  - Median: 0.0
  - Stddev: 6.849831581115723
  - Non-zero count: 11701.0


- P_BENAMT_BENEFIT_CODE_82:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.021561988753098758
  - Median: 0.0
  - Stddev: 2.294255018234253
  - Non-zero count: 11922.0


- P_BENAMT_BENEFIT_CODE_83:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.06771429484715615
  - Median: 0.0
  - Stddev: 28.940170288085938
  - Non-zero count: 4622.0


- P_BENAMT_BENEFIT_CODE_90:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.9370175482770489
  - Median: 0.0
  - Stddev: 9.667805671691895
  - Non-zero count: 1257876.0


- P_BENAMT_BENEFIT_CODE_91:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 3.8457712005358022
  - Median: 0.0
  - Stddev: 24.918882369995117
  - Non-zero count: 2455681.0


- P_BENAMT_BENEFIT_CODE_92:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 3.433185109231564e-05
  - Median: 0.0
  - Stddev: 0.00963511411100626
  - Non-zero count: 1124.0


- P_BENAMT_BENEFIT_CODE_94:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 4.783708143897081
  - Median: 0.0
  - Stddev: 22.909976959228516
  - Non-zero count: 3596990.0


- P_BENAMT_BENEFIT_CODE_95:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.5863081896515483
  - Median: 0.0
  - Stddev: 17.673233032226562
  - Non-zero count: 722795.0


- P_BENAMT_BENEFIT_CODE_96:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.6032764691732235
  - Median: 0.0
  - Stddev: 11.168543815612793
  - Non-zero count: 1521158.0


- P_BENAMT_BENEFIT_CODE_97:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.7575291969628094
  - Median: 0.0
  - Stddev: 6.727320194244385
  - Non-zero count: 1086010.0


- P_BENAMT_BENEFIT_CODE_98:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.96324226229041
  - Median: 0.0
  - Stddev: 39.89448928833008
  - Non-zero count: 252074.0


- P_BENAMT_BENEFIT_CODE_99:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.7329860440567144
  - Median: 0.0
  - Stddev: 110.02783203125
  - Non-zero count: 34693.0


- P_BENAMT_BENEFIT_CODE_102:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_103:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_104:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_105:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_106:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_107:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_108:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_109:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_110:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.011251213549942074
  - Median: 0.0
  - Stddev: 0.6607922315597534
  - Non-zero count: 37945.0


- P_BENAMT_BENEFIT_CODE_111:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.03936215419819155
  - Median: 0.0
  - Stddev: 1.1887630224227905
  - Non-zero count: 134537.0


- P_AGE80:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 38.05373212649546
  - Median: 39.3239598278348
  - Stddev: 26.59808349609375
  - Non-zero count: 51553959.0


- P_AGE:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.7672470169813612
  - Median: 0.0
  - Stddev: 4.316173553466797
  - Non-zero count: 13118653.0


- P_PERSON:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.273965376908516
  - Median: 1.0
  - Stddev: 0.8990830183029175
  - Non-zero count: 51553959.0


- P_UPERSON:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.0393994644506128
  - Median: 1.0
  - Stddev: 0.6924399137496948
  - Non-zero count: 51553959.0


- P_TYPEED2:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.2715005699194187
  - Median: 0.0
  - Stddev: 1.2658056020736694
  - Non-zero count: 1995959.0


- P_TOTHOURS:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 17.09531228561137
  - Median: 0.0
  - Stddev: 19.48204803466797
  - Non-zero count: 31045772.0


- P_SEINCAMT:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 24.35690455526532
  - Median: 0.0
  - Stddev: 174.48521423339844
  - Non-zero count: 3738272.0


- P_EMPSTATI:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 2.9084855492000394
  - Median: 1.0
  - Stddev: 3.1097352504730225
  - Non-zero count: 51553959.0


- P_FUELAMT:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.007607548743008394
  - Median: 0.0
  - Stddev: 0.4254932403564453
  - Non-zero count: 15244.0


- P_MILEAMT:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.22482526823829677
  - Median: 0.0
  - Stddev: 4.76098108291626
  - Non-zero count: 304590.0


- P_MOTAMT:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 0.07000217995379017
  - Median: 0.0
  - Stddev: 2.1174678802490234
  - Non-zero count: 122426.0


- P_SEINCAM2:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 46.74796088581979
  - Median: 0.0
  - Stddev: 2090.904052734375
  - Non-zero count: 4170388.0


- P_INRINC:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 12.730147420021716
  - Median: 0.0
  - Stddev: 59.267215728759766
  - Non-zero count: 10533332.0


- P_ROYYR1:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 3.448405132807214
  - Median: 0.0
  - Stddev: 32.73629379272461
  - Non-zero count: 1874106.0


- P_ININV:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 5.81728576630929
  - Median: 0.0
  - Stddev: 55.498817443847656
  - Non-zero count: 13870968.0


- P_INTXCRED:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 4.7828223804832435
  - Median: 0.0
  - Stddev: 30.08650779724121
  - Non-zero count: 2722406.0


- P_INDUC:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.5863838015362435
  - Median: 0.0
  - Stddev: 17.671884536743164
  - Non-zero count: 722795.0


- P_INOTHBEN:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 14.958692170283843
  - Median: 0.0
  - Stddev: 47.20756149291992
  - Non-zero count: 21282432.0


- P_INDISBEN:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 5.503380091390227
  - Median: 0.0
  - Stddev: 25.512805938720703
  - Non-zero count: 4051403.0


- P_INRPINC:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 26.186428060301576
  - Median: 0.0
  - Stddev: 64.72219848632812
  - Non-zero count: 11553083.0


- P_SEX:
  - Type: float
  - Entity: person
  - Description: None
  - Mean: 1.1900438089997558
  - Median: 1.0
  - Stddev: 0.7775659561157227
  - Non-zero count: 51553959.0


- base_net_income:
  - Type: float
  - Entity: person
  - Description: Existing net income for the person to use as a base in microsimulation
  - Mean: 16013.465239778216
  - Median: 13000.0
  - Stddev: 111095.6015625
  - Non-zero count: 49639715.0


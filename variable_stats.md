# OpenFisca-UK Variable Statistics

All statistics generated from the 2018-19 Family Resources Survey, with simulation turned on.


- in_poverty_ahc:
  - Type: <class 'bool'>
  - Entity: household
  - Description: Whether the household is in absolute poverty, after housing costs
  - Mean: 0.20197603294746552
  - Median: 0.0
  - Stddev: 0.3969739134226824
  - Non-zero count: 5620748.0


- in_poverty_bhc:
  - Type: <class 'bool'>
  - Entity: household
  - Description: Whether the household is in absolute poverty, before housing costs
  - Mean: 0.19215497966188752
  - Median: 0.0
  - Stddev: 0.3924302294550659
  - Non-zero count: 5347440.0


- poverty_gap_ahc:
  - Type: <class 'float'>
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line, after housing costs
  - Mean: nan
  - Median: 0.0
  - Stddev: 5706.9111328125
  - Non-zero count: 5620748.0


- poverty_gap_bhc:
  - Type: <class 'float'>
  - Entity: household
  - Description: Positive financial gap between net household income and the poverty line
  - Mean: nan
  - Median: 0.0
  - Stddev: 3524.922607421875
  - Non-zero count: 5347440.0


- poverty_line_ahc:
  - Type: <class 'float'>
  - Entity: household
  - Description: The poverty line for the household, after housing costs
  - Mean: 12920.336610894108
  - Median: 14040.0
  - Stddev: 4705.5146484375
  - Non-zero count: 27828787.0


- poverty_line_bhc:
  - Type: <class 'float'>
  - Entity: household
  - Description: The poverty line for the household, before housing costs
  - Mean: 15681.601868625577
  - Median: 16432.0
  - Stddev: 4731.875
  - Non-zero count: 27828787.0


- country:
  - Type: Categorical
  - Entity: household
  - Description: Country of the UK


- household_equivalisation_ahc:
  - Type: <class 'float'>
  - Entity: household
  - Description: Equivalisation factor to account for household composition, after housing costs
  - Mean: 0.9202517696554138
  - Median: 1.0
  - Stddev: 0.3351506292819977
  - Non-zero count: 27828787.0


- household_equivalisation_bhc:
  - Type: <class 'float'>
  - Entity: household
  - Description: Equivalisation factor to account for household composition, before housing costs
  - Mean: 0.9543330914063199
  - Median: 1.0
  - Stddev: 0.2879670262336731
  - Non-zero count: 27828787.0


- household_weight:
  - Type: <class 'float'>
  - Entity: household
  - Description: Weight factor for the household
  - Mean: 2295.636794194443
  - Median: 1561.0
  - Stddev: 1106.8741455078125
  - Non-zero count: 27828787.0


- households:
  - Type: <class 'float'>
  - Entity: household
  - Description: Variable holding households
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 27828787.0


- is_shared_accommodation:
  - Type: <class 'bool'>
  - Entity: household
  - Description: Whether the household is shared accommodation
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_bedrooms:
  - Type: <class 'float'>
  - Entity: household
  - Description: The number of bedrooms in the house
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- region:
  - Type: Categorical
  - Entity: household
  - Description: Region of the UK


- tenure_type:
  - Type: Categorical
  - Entity: household
  - Description: Tenure type of the household


- age:
  - Type: <class 'float'>
  - Entity: person
  - Description: The age of the person in years
  - Mean: 39.82097914347682
  - Median: 39.3239598278348
  - Stddev: 23.953073501586914
  - Non-zero count: 64672612.0


- age_18_64:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is age 18 to 64
  - Mean: 0.6106867660717314
  - Median: 1.0
  - Stddev: 0.49670193698795856
  - Non-zero count: 39986887.0


- age_over_64:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is over age 64
  - Mean: 0.1797574335597357
  - Median: 0.0
  - Stddev: 0.4128768716054247
  - Non-zero count: 11770257.0


- age_under_18:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is under age 18
  - Mean: 0.20955580036853289
  - Median: 0.0
  - Stddev: 0.41734889359818766
  - Non-zero count: 13721411.0


- birth_year:
  - Type: <class 'float'>
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
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is in Further Education
  - Mean: 0.0011779734601656984
  - Median: 0.0
  - Stddev: 0.03194010855649921
  - Non-zero count: 77132.0


- in_HE:
  - Type: <class 'bool'>
  - Entity: person
  - Description: label
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- in_social_housing:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person lives in social housing
  - Mean: 0.16580420872146615
  - Median: 0.0
  - Stddev: 0.38437236528738367
  - Non-zero count: 10856620.0


- is_WA_adult:
  - Type: <class 'float'>
  - Entity: person
  - Description: Whether is a working-age adult
  - Mean: 0.6106867660717314
  - Median: 1.0
  - Stddev: 0.4967019557952881
  - Non-zero count: 39986887.0


- is_adult:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is an adult
  - Mean: 0.7904441996314672
  - Median: 1.0
  - Stddev: 0.41734889359818766
  - Non-zero count: 51757144.0


- is_benunit_head:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is the head-of-family
  - Mean: 0.5352827807516523
  - Median: 1.0
  - Stddev: 0.49960493110885895
  - Non-zero count: 35049543.0


- is_child:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is a child
  - Mean: 0.20955580036853289
  - Median: 0.0
  - Stddev: 0.41734889359818766
  - Non-zero count: 13721411.0


- is_female:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is female
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- is_household_head:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is the head-of-household
  - Mean: 0.424983874491427
  - Median: 0.0
  - Stddev: 0.4969542878692517
  - Non-zero count: 27827330.0


- is_male:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is male
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- is_older_child:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is over 14 but under 18
  - Mean: 0.04104539264802041
  - Median: 0.0
  - Stddev: 0.20292526183413828
  - Non-zero count: 2687593.0


- is_young_child:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is under 14
  - Mean: 0.16851040772051246
  - Median: 0.0
  - Stddev: 0.3855266696976094
  - Non-zero count: 11033818.0


- over_16:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is over 16
  - Mean: 0.8106907826539544
  - Median: 1.0
  - Stddev: 0.4030461281464062
  - Non-zero count: 53082861.0


- people:
  - Type: <class 'float'>
  - Entity: person
  - Description: Variable holding people
  - Mean: 1.0
  - Median: 1.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- person_weight:
  - Type: <class 'float'>
  - Entity: person
  - Description: Weight factor for the person
  - Mean: 2260.5343767741974
  - Median: 1658.0
  - Stddev: 1061.07763671875
  - Non-zero count: 65478555.0


- benunit_is_renting:
  - Type: <class 'bool'>
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
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Weight factor for the benefit unit
  - Mean: 2420.2049674370933
  - Median: 1700.0
  - Stddev: 1157.133056640625
  - Non-zero count: 35049543.0


- eldest_adult_age:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: -inf
  - Median: 48.0
  - Stddev: nan
  - Non-zero count: 34937614.0


- eldest_child_age:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: -inf
  - Median: -inf
  - Stddev: nan
  - Non-zero count: 7620235.0


- families:
  - Type: <class 'float'>
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
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether the benefit unit adults are married
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_adults:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: The number of children in the family
  - Mean: 1.4766852737566365
  - Median: 1.0
  - Stddev: 0.5187704563140869
  - Non-zero count: 34937614.0


- num_children:
  - Type: <class 'float'>
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
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: inf
  - Median: 46.0
  - Stddev: nan
  - Non-zero count: 35049543.0


- youngest_child_age:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Eldest adult age
  - Mean: inf
  - Median: inf
  - Stddev: nan
  - Non-zero count: 34249935.0


- childcare_cost:
  - Type: <class 'float'>
  - Entity: person
  - Description: Cost of childcare
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- council_tax:
  - Type: <class 'float'>
  - Entity: household
  - Description: Council Tax
  - Mean: nan
  - Median: 1322.6231604476818
  - Stddev: 599.0809326171875
  - Non-zero count: 26726432.0


- family_rent:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Gross rent for the family
  - Mean: 2103.9165108657767
  - Median: 0.0
  - Stddev: 4989.38671875
  - Non-zero count: 9988990.0


- housing_costs:
  - Type: <class 'float'>
  - Entity: household
  - Description: Total housing costs per week
  - Mean: 4194.234312260897
  - Median: 3120.0
  - Stddev: 5371.0107421875
  - Non-zero count: 27736446.0


- mortgage:
  - Type: <class 'float'>
  - Entity: household
  - Description: Total mortgage payments
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- personal_rent:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal rent
  - Mean: 1126.1902804055464
  - Median: 0.0
  - Stddev: 3730.41650390625
  - Non-zero count: 9988990.0


- rent:
  - Type: <class 'float'>
  - Entity: household
  - Description: Gross rent for the household
  - Mean: 2650.144389836323
  - Median: 0.0
  - Stddev: 5322.75634765625
  - Non-zero count: 9990064.0


- weekly_childcare_cost:
  - Type: <class 'float'>
  - Entity: person
  - Description: Average cost of childcare per week
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- weekly_rent:
  - Type: <class 'float'>
  - Entity: household
  - Description: Weekly average rent
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- base_net_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Existing net income for the person to use as a base in microsimulation
  - Mean: 16013.465237612178
  - Median: 13000.0
  - Stddev: 111095.6015625
  - Non-zero count: 49639715.0


- employment_status:
  - Type: Categorical
  - Entity: person
  - Description: Employment status of the person


- equiv_household_net_income:
  - Type: <class 'float'>
  - Entity: household
  - Description: Equivalised household net income, before housing costs
  - Mean: nan
  - Median: 29711.287110237496
  - Stddev: 174129.828125
  - Non-zero count: 25956257.0


- equiv_household_net_income_ahc:
  - Type: <class 'float'>
  - Entity: household
  - Description: Equivalised household net income, after housing costs
  - Mean: nan
  - Median: 27294.064573126325
  - Stddev: 174628.5625
  - Non-zero count: 25468235.0


- hours_worked:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total amount of hours worked by this person
  - Mean: 888.9562388892862
  - Median: 0.0
  - Stddev: 1013.0665283203125
  - Non-zero count: 31045772.0


- household_net_income:
  - Type: <class 'float'>
  - Entity: household
  - Description: Household net income, before housing costs
  - Mean: nan
  - Median: 29247.776611328125
  - Stddev: 174872.984375
  - Non-zero count: 25956257.0


- household_net_income_ahc:
  - Type: <class 'float'>
  - Entity: household
  - Description: Household net income, after housing costs
  - Mean: nan
  - Median: 25221.12735726691
  - Stddev: 174848.578125
  - Non-zero count: 25468235.0


- net_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Net income for the person
  - Mean: 15541.267830999173
  - Median: 12480.9335678759
  - Stddev: 119855.3828125
  - Non-zero count: 48859183.0


- sublet_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income received from sublet agreements
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- weekly_hours:
  - Type: <class 'float'>
  - Entity: person
  - Description: Average weekly hours for the year
  - Mean: 17.09531228628221
  - Median: 0.0
  - Stddev: 19.48204803466797
  - Non-zero count: 31045772.0


- benefits:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total simulated
  - Mean: 2616.9494304437812
  - Median: 0.0
  - Stddev: 4807.9921875
  - Non-zero count: 23841167.0


- benefits_modelling:
  - Type: <class 'float'>
  - Entity: person
  - Description: Difference between reported and simulated benefits for this person
  - Mean: 9.664130342897913
  - Median: 0.0
  - Stddev: 2208.852294921875
  - Non-zero count: 9584717.0


- benefits_premiums:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Value of premiums for disability and carer status
  - Mean: 482.86022420566604
  - Median: 0.0
  - Stddev: 1802.2833251953125
  - Non-zero count: 3972667.0


- benefits_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total simulated
  - Mean: 2607.2853003573737
  - Median: 0.0
  - Stddev: 5104.62255859375
  - Non-zero count: 21970175.0


- benunit_weekly_hours:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Average weekly hours worked by adults in the benefit unit
  - Mean: 31.936974065260962
  - Median: 35.0
  - Stddev: 30.85429573059082
  - Non-zero count: 22047795.0


- claims_legacy_benefits:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim legacy benefits over Universal Credit
  - Mean: 0.7953585585980394
  - Median: 1.0
  - Stddev: 0.4019638001918793
  - Non-zero count: 27876954.0


- family_benefits:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total simulated family benefits for this person
  - Mean: 862.126986313022
  - Median: 0.0
  - Stddev: 2541.564208984375
  - Non-zero count: 13127855.0


- family_benefits_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total reported family benefits for this person
  - Mean: 896.1968124098463
  - Median: 0.0
  - Stddev: 3085.521728515625
  - Non-zero count: 10893314.0


- is_QYP:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is a qualifying young person for benefits purposes
  - Mean: 0.00023813903651355775
  - Median: 0.0
  - Stddev: 0.011799871994737398
  - Non-zero count: 15593.0


- is_child_or_QYP:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is a child or qualifying young person for most benefits
  - Mean: 0.20974355649723792
  - Median: 0.0
  - Stddev: 0.41741013183180975
  - Non-zero count: 13733705.0


- is_couple:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this benefit unit contains a joint couple claimant for benefits
  - Mean: 0.4740214729761241
  - Median: 0.0
  - Stddev: 0.4998159694855555
  - Non-zero count: 16614236.0


- is_lone_parent:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Whether the family is a lone parent family
  - Mean: 0.05618173109988909
  - Median: 0.0
  - Stddev: 0.25292670726776123
  - Non-zero count: 1969144.0


- is_single:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this benefit unit contains a single claimant for benefits
  - Mean: 0.5259785270238759
  - Median: 1.0
  - Stddev: 0.4998159694855555
  - Non-zero count: 18435307.0


- is_single_person:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Whether the family is a single person
  - Mean: 0.472990246976972
  - Median: 0.0
  - Stddev: 0.4972909092903137
  - Non-zero count: 16578092.0


- personal_benefits:
  - Type: <class 'float'>
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1754.8224454547762
  - Median: 0.0
  - Stddev: 3929.2294921875
  - Non-zero count: 14627495.0


- personal_benefits_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Value of personal, non-means-tested benefits
  - Mean: 1711.0884880323476
  - Median: 0.0
  - Stddev: 3769.971435546875
  - Non-zero count: 14653250.0


- carer_premium:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Carer premium
  - Mean: 40.273449499755245
  - Median: 0.0
  - Stddev: 302.28387451171875
  - Non-zero count: 723880.0


- is_carer_for_benefits:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is a carer for benefits purposes
  - Mean: 0.011218650136674519
  - Median: 0.0
  - Stddev: 0.11336199523779618
  - Non-zero count: 734581.0


- num_carers:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: The number of carers for benefits purposes in the family
  - Mean: 0.020958361711021452
  - Median: 0.0
  - Stddev: 0.15879395604133606
  - Non-zero count: 723880.0


- disability_premium:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Disability premium
  - Mean: 179.1059231172301
  - Median: 0.0
  - Stddev: 658.1970825195312
  - Non-zero count: 2916234.0


- enhanced_disability_premium:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Enhanced disability premium
  - Mean: 0.5436543532423095
  - Median: 0.0
  - Stddev: 27.48753547668457
  - Non-zero count: 16244.0


- is_disabled_for_benefits:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is disabled for benefits purposes
  - Mean: 0.047336994532026555
  - Median: 0.0
  - Stddev: 0.22948140031146275
  - Non-zero count: 3099558.0


- is_enhanced_disabled_for_benefits:
  - Type: <class 'float'>
  - Entity: person
  - Description: Whether meets the middle disability benefit entitlement
  - Mean: 0.012900223592289109
  - Median: 0.0
  - Stddev: 0.9031115770339966
  - Non-zero count: 16244.0


- is_severely_disabled_for_benefits:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is severely disabled for benefits purposes
  - Mean: 0.029661146309658177
  - Median: 0.0
  - Stddev: 0.18366175665180345
  - Non-zero count: 1942169.0


- num_disabled_adults:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Number of disabled adults
  - Mean: 0.08721611577075342
  - Median: 0.0
  - Stddev: 0.3237573504447937
  - Non-zero count: 2916234.0


- num_disabled_children:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Number of disabled children
  - Mean: 0.001217505175459777
  - Median: 0.0
  - Stddev: 0.03835635632276535
  - Non-zero count: 40069.0


- num_enhanced_disabled_adults:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Number of enhanced disabled adults
  - Mean: 0.0004634582539350085
  - Median: 0.0
  - Stddev: 0.024080926552414894
  - Non-zero count: 16244.0


- num_enhanced_disabled_children:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Number of enhanced disabled children
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- num_severely_disabled_adults:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Number of severely disabled adults
  - Mean: 0.05480151338920453
  - Median: 0.0
  - Stddev: 0.260103315114975
  - Non-zero count: 1852755.0


- num_severely_disabled_children:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Number of severely disabled children
  - Mean: 0.0006105928399694113
  - Median: 0.0
  - Stddev: 0.025865908712148666
  - Non-zero count: 21401.0


- severe_disability_premium:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Severe disability premium
  - Mean: 262.9371130633394
  - Median: 0.0
  - Stddev: 1294.7274169921875
  - Non-zero count: 1852755.0


- UC_eligible_rent:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Eligible rent in Universal Credit
  - Mean: 932.2268157372788
  - Median: 0.0
  - Stddev: 2147.146240234375
  - Non-zero count: 6285973.0


- UC_personal_allowance:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Personal allowance for Universal Credit
  - Mean: 4718.706590063101
  - Median: 3813.840576171875
  - Stddev: 1164.732421875
  - Non-zero count: 35049543.0


- UC_premiums:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Premiums for Universal Credit
  - Mean: 1343.1991460610082
  - Median: 0.0
  - Stddev: 2485.510009765625
  - Non-zero count: 10588121.0


- claims_UC:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim UC
  - Mean: 0.15200517735709135
  - Median: 0.0
  - Stddev: 0.35505976823158597
  - Non-zero count: 5327712.0


- universal_credit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Universal Credit amount per week
  - Mean: 181.7346624927147
  - Median: 0.0
  - Stddev: 1104.877685546875
  - Non-zero count: 1234066.0


- universal_credit_applicable_amount:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Relevant income for Universal Credit
  - Mean: 6994.131989366747
  - Median: 5986.68115234375
  - Stddev: 3730.263916015625
  - Non-zero count: 35049543.0


- universal_credit_eligible:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether eligible for Universal Credit
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- universal_credit_income_reduction:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Reduction from income for Universal Credit
  - Mean: 18973.466260644713
  - Median: 12828.5419921875
  - Stddev: 22107.298828125
  - Non-zero count: 29575439.0


- universal_credit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Reported amount of Universal Credit per month
  - Mean: 82.48829929650108
  - Median: 0.0
  - Stddev: 919.0091552734375
  - Non-zero count: 722795.0


- JSA:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Amount of Jobseeker's Allowance for this family
  - Mean: 18.31386287231705
  - Median: 0.0
  - Stddev: 267.9993591308594
  - Non-zero count: 185107.0


- JSA_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Job Seeker's Allowance (income-based)
  - Mean: 12.642531410887678
  - Median: 0.0
  - Stddev: 227.4209442138672
  - Non-zero count: 154888.0


- JSA_income_applicable_amount:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Maximum amount of JSA (income-based)
  - Mean: 18.394723606587874
  - Median: 0.0
  - Stddev: 289.83526611328125
  - Non-zero count: 172909.0


- JSA_income_applicable_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Relevant income for JSA (income-based) means test
  - Mean: 24884.339798953915
  - Median: 18891.632747630865
  - Stddev: 22787.107421875
  - Non-zero count: 31952716.0


- JSA_income_eligible:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether eligible for JSA (income-based)
  - Mean: 0.02279927016452112
  - Median: 0.0
  - Stddev: 0.13766831158248036
  - Non-zero count: 799104.0


- JSA_income_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: JSA (income-based) (reported amount per week)
  - Mean: 18.2252038787812
  - Median: 0.0
  - Stddev: 292.5605163574219
  - Non-zero count: 289811.0


- claims_JSA:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim JSA based on survey response and take-up rates
  - Mean: 0.009792709708083783
  - Median: 0.0
  - Stddev: 0.10187601112660134
  - Non-zero count: 343230.0


- yearly_JSA:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Yearly amount of JSA for the family
  - Mean: 18.31386287231705
  - Median: 0.0
  - Stddev: 267.9993591308594
  - Non-zero count: 185107.0


- claims_HB:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim Housing Benefit
  - Mean: 0.6746711647566989
  - Median: 1.0
  - Stddev: 0.46493570445632104
  - Non-zero count: 23646916.0


- housing_benefit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Housing Benefit
  - Mean: 387.51093479381115
  - Median: 0.0
  - Stddev: 1420.4066162109375
  - Non-zero count: 3235765.0


- housing_benefit_applicable_amount:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Applicable amount for Housing Benefit
  - Mean: 2232.0546020877687
  - Median: 0.0
  - Stddev: 3861.144287109375
  - Non-zero count: 13041070.0


- housing_benefit_applicable_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Relevant income for Housing Benefit means test
  - Mean: 24433.016536548545
  - Median: 18827.358646126682
  - Stddev: 22041.033203125
  - Non-zero count: 31911979.0


- housing_benefit_eligible:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether eligible for Housing Benefit
  - Mean: 0.3720753220662535
  - Median: 0.0
  - Stddev: 0.4805899012216294
  - Non-zero count: 13041070.0


- housing_benefit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Housing Benefit (reported amount per week)
  - Mean: 248.75284124337716
  - Median: 0.0
  - Stddev: 1191.31884765625
  - Non-zero count: 3596990.0


- claims_IS:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim Income Support
  - Mean: 0.0147520040418216
  - Median: 0.0
  - Stddev: 0.13562605112848378
  - Non-zero count: 517051.0


- income_support:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Income Support
  - Mean: 26.636055870458318
  - Median: 0.0
  - Stddev: 352.4853820800781
  - Non-zero count: 320990.0


- income_support_applicable_amount:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Applicable amount of Income Support
  - Mean: 74.50721424954551
  - Median: 0.0
  - Stddev: 940.0902099609375
  - Non-zero count: 372395.0


- income_support_applicable_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Relevant income for Income Support means test
  - Mean: 24884.339798953915
  - Median: 18891.632747630865
  - Stddev: 22787.107421875
  - Non-zero count: 31952716.0


- income_support_eligible:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether eligible for Income Support
  - Mean: 0.03459856808974656
  - Median: 0.0
  - Stddev: 0.201198662541204
  - Non-zero count: 1212664.0


- income_support_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income Support (reported amount per week)
  - Mean: 31.67203485538439
  - Median: 0.0
  - Stddev: 436.4030456542969
  - Non-zero count: 517051.0


- benefit_cap:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Benefit cap for the family
  - Mean: inf
  - Median: 13399.8876953125
  - Stddev: nan
  - Non-zero count: 35049543.0


- is_benefit_cap_exempt:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether exempt from the benefits cap
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- claims_PC:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim Pension Credit
  - Mean: 0.6089397228374703
  - Median: 1.0
  - Stddev: 0.48652895106365823
  - Non-zero count: 21343059.0


- pension_credit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Pension credit amount per week
  - Mean: 102.14085132989248
  - Median: 0.0
  - Stddev: 687.27685546875
  - Non-zero count: 1751243.0


- pension_credit_GC:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Pension Credit (Guarantee Credit) amount per week
  - Mean: 89.01199057499869
  - Median: 0.0
  - Stddev: 668.1214599609375
  - Non-zero count: 1267004.0


- pension_credit_MG:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Pension Credit (Minimum Guarantee) amount per week
  - Mean: 1679.4970046691747
  - Median: 0.0
  - Stddev: 4688.24072265625
  - Non-zero count: 5053667.0


- pension_credit_SC:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Pension Credit (Savings Credit) amount per week
  - Mean: 13.128858280929872
  - Median: 0.0
  - Stddev: 95.40303802490234
  - Non-zero count: 1057913.0


- pension_credit_applicable_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Applicable income for Pension Credit
  - Mean: 25762.94965118629
  - Median: 19674.888671875
  - Stddev: 23375.560546875
  - Non-zero count: 32556759.0


- pension_credit_eligible:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether eligible for Pension Credit
  - Mean: 0.21824983566832812
  - Median: 0.0
  - Stddev: 0.4447838745853726
  - Non-zero count: 7649557.0


- pension_credit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Reported amount of Pension Credit per week
  - Mean: 47.055048768434055
  - Median: 0.0
  - Stddev: 547.4176025390625
  - Non-zero count: 1132019.0


- CTC_child_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: CTC entitlement from child elements
  - Mean: 411.66078770270985
  - Median: 0.0
  - Stddev: 1722.11328125
  - Non-zero count: 2402900.0


- CTC_disabled_child_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: CTC entitlement from disabled child elements
  - Mean: 2.660680197741808
  - Median: 0.0
  - Stddev: 104.89398193359375
  - Non-zero count: 25871.0


- CTC_family_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: CTC entitlement in the Family Element
  - Mean: 37.36369686760253
  - Median: 0.0
  - Stddev: 148.44090270996094
  - Non-zero count: 2402900.0


- CTC_maximum_rate:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: The maximum rate of CTC
  - Mean: 452.3119867782584
  - Median: 0.0
  - Stddev: 1880.54833984375
  - Non-zero count: 2402900.0


- CTC_severely_disabled_child_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: CTC entitlement from severely disabled child elements
  - Mean: 0.6268220102042414
  - Median: 0.0
  - Stddev: 27.986364364624023
  - Non-zero count: 16581.0


- WTC_basic_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the basic element
  - Mean: 69.82268556254785
  - Median: 0.0
  - Stddev: 396.87481689453125
  - Non-zero count: 1187987.0


- WTC_childcare_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the childcare element
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- WTC_couple_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the couple element
  - Mean: 32.20079731139433
  - Median: 0.0
  - Stddev: 254.30429077148438
  - Non-zero count: 551894.0


- WTC_disabled_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the disabled element
  - Mean: 3.7013486880556474
  - Median: 0.0
  - Stddev: 127.16803741455078
  - Non-zero count: 40289.0


- WTC_lone_parent_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the lone parent element
  - Mean: 31.79587619730163
  - Median: 0.0
  - Stddev: 289.07073974609375
  - Non-zero count: 544954.0


- WTC_maximum_rate:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: The maximum rate of WTC
  - Mean: 153.0644533653406
  - Median: 0.0
  - Stddev: 892.9992065429688
  - Non-zero count: 1187987.0


- WTC_severely_disabled_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the severely disabled element
  - Mean: 0.9038885328690306
  - Median: 0.0
  - Stddev: 39.382568359375
  - Non-zero count: 22792.0


- WTC_worker_element:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: WTC entitlement from the worker element
  - Mean: 14.63985707317211
  - Median: 0.0
  - Stddev: 111.89149475097656
  - Non-zero count: 621964.0


- child_tax_credit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Amount of Child Tax Credit entitled to
  - Mean: 362.7458905858484
  - Median: 0.0
  - Stddev: 1671.558349609375
  - Non-zero count: 2156411.0


- child_tax_credit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Working Tax Credit (reported amount)
  - Mean: 199.9800488502639
  - Median: 0.0
  - Stddev: 1295.7816162109375
  - Non-zero count: 2455681.0


- claims_CTC:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates
  - Mean: 0.07006313891168281
  - Median: 0.0
  - Stddev: 0.2750975827810318
  - Non-zero count: 2455681.0


- claims_WTC:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates
  - Mean: 0.035888513582045846
  - Median: 0.0
  - Stddev: 0.19771028774279886
  - Non-zero count: 1257876.0


- is_CTC_child_limit_exempt:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person was born before 2017 and therefore exempt from the two-child limit for Child Tax Credit
  - Mean: 0.9498417306246297
  - Median: 1.0
  - Stddev: 0.21926754530601014
  - Non-zero count: 62194264.0


- is_CTC_eligible:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether the family is eligible for CTC
  - Mean: 0.2242120817381271
  - Median: 0.0
  - Stddev: 0.42816255763543365
  - Non-zero count: 7858531.0


- is_WTC_eligible:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Whether the family is eligible for WTC
  - Mean: 0.5106053165942849
  - Median: 1.0
  - Stddev: 0.4999896287918091
  - Non-zero count: 17896483.0


- is_child_for_CTC:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is a child conferring CTC eligibility
  - Mean: 0.20974355649723792
  - Median: 0.0
  - Stddev: 0.41741013183180975
  - Non-zero count: 13733705.0


- tax_credits:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Value of the Tax Credits (benefits) for this family
  - Mean: 430.9897339368128
  - Median: 0.0
  - Stddev: 1991.6551513671875
  - Non-zero count: 2269004.0


- tax_credits_applicable_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Applicable income for Tax Credits
  - Mean: 30436.945228826375
  - Median: 20800.0
  - Stddev: 34751.3515625
  - Non-zero count: 29777056.0


- tax_credits_reduction:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Reduction in Tax Credits from means-tested income
  - Mean: 10225.66030455361
  - Median: 5708.884765625
  - Stddev: 13929.5068359375
  - Non-zero count: 27700427.0


- working_tax_credit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Amount of Working Tax Credit entitled to
  - Mean: 68.24384222862038
  - Median: 0.0
  - Stddev: 539.1953735351562
  - Non-zero count: 878028.0


- working_tax_credit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Working Tax Credit (reported amount)
  - Mean: 48.72485204502181
  - Median: 0.0
  - Stddev: 502.72576904296875
  - Non-zero count: 1257876.0


- child_benefit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Child Benefit entitlement for the family
  - Mean: 357.72243459406195
  - Median: 0.0
  - Stddev: 762.013916015625
  - Non-zero count: 7786103.0


- child_benefit_less_tax_charge:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Child Benefit entitlement, less the High Income Tax Charge
  - Mean: 302.91097412085134
  - Median: 0.0
  - Stddev: 713.8612060546875
  - Non-zero count: 6855006.0


- child_benefit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Child Benefit (reported amount)
  - Mean: 159.76229662389002
  - Median: 0.0
  - Stddev: 547.5189208984375
  - Non-zero count: 6424339.0


- claims_child_benefit:
  - Type: <class 'bool'>
  - Entity: benunit
  - Description: Whether this family is imputed to claim Child Benefit, based on survey response and take-up rates
  - Mean: 0.9594976174154396
  - Median: 1.0
  - Stddev: 0.19393539792687098
  - Non-zero count: 33629953.0


- yearly_child_benefit:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Child Benefit entitlement for the year
  - Mean: 357.72243459406195
  - Median: 0.0
  - Stddev: 762.013916015625
  - Non-zero count: 7786103.0


- ESA_income:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: ESA (income-based)
  - Mean: 111.2238018320569
  - Median: 0.0
  - Stddev: 902.1917114257812
  - Non-zero count: 660734.0


- ESA_income_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: ESA (income-based) (reported amount per week)
  - Mean: 59.53618590582191
  - Median: 0.0
  - Stddev: 649.055908203125
  - Non-zero count: 669633.0


- LHA_allowed_bedrooms:
  - Type: <class 'float'>
  - Entity: household
  - Description: The number of bedrooms covered by LHA for the household
  - Mean: 1.256940879241341
  - Median: 1.0
  - Stddev: 0.4386759400367737
  - Non-zero count: 27828787.0


- LHA_cap:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Applicable amount for LHA
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- LHA_eligible:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: Whether eligible for Local Housing Allowance
  - Mean: 0.1963764263631055
  - Median: 0.0
  - Stddev: 0.3740248382091522
  - Non-zero count: 6882904.0


- incapacity_benefit:
  - Type: <class 'float'>
  - Entity: person
  - Description: Incapacity Benefit
  - Mean: 1.1138353706436668
  - Median: 0.0
  - Stddev: 90.69267272949219
  - Non-zero count: 14487.0


- incapacity_benefit_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Incapacity Benefit (reported)
  - Mean: 1.1138353706436668
  - Median: 0.0
  - Stddev: 90.69267272949219
  - Non-zero count: 14487.0


- is_SP_age:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether the person is State Pension Age
  - Mean: 0.1797574335597357
  - Median: 0.0
  - Stddev: 0.4128768716054247
  - Non-zero count: 11770257.0


- state_pension:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from the State Pension
  - Mean: 1319.2646145398041
  - Median: 0.0
  - Stddev: 3253.012939453125
  - Non-zero count: 11554244.0


- state_pension_age:
  - Type: <class 'float'>
  - Entity: person
  - Description: State Pension age for this person
  - Mean: 65.0
  - Median: 65.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- state_pension_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Reported income from the State Pension
  - Mean: 1319.2646145398041
  - Median: 0.0
  - Stddev: 3253.012939453125
  - Non-zero count: 11554244.0


- DLA:
  - Type: <class 'float'>
  - Entity: person
  - Description: Disability Living Allowance
  - Mean: 104.97250466644462
  - Median: 0.0
  - Stddev: 850.8763427734375
  - Non-zero count: 1490840.0


- DLA_M:
  - Type: <class 'float'>
  - Entity: person
  - Description: Disability Living Allowance (mobility component)
  - Mean: 41.13953996671884
  - Median: 0.0
  - Stddev: 386.1026611328125
  - Non-zero count: 1106456.0


- DLA_M_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Disability Living Allowance (mobility component) (reported)
  - Mean: 41.13953996671884
  - Median: 0.0
  - Stddev: 386.1026611328125
  - Non-zero count: 1106456.0


- DLA_SC:
  - Type: <class 'float'>
  - Entity: person
  - Description: Disability Living Allowance (self-care)
  - Mean: 63.83298978577333
  - Median: 0.0
  - Stddev: 539.081298828125
  - Non-zero count: 1317063.0


- DLA_SC_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Disability Living Allowance (self-care) (reported)
  - Mean: 63.83298978577333
  - Median: 0.0
  - Stddev: 539.081298828125
  - Non-zero count: 1317063.0


- PIP:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal Independence Payment
  - Mean: 122.76191773494
  - Median: 0.0
  - Stddev: 869.1986083984375
  - Non-zero count: 1619945.0


- PIP_DL:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal Independence Payment (Daily Living)
  - Mean: 83.37042280098512
  - Median: 0.0
  - Stddev: 580.7645874023438
  - Non-zero count: 1521158.0


- PIP_DL_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal Independence Payment (Daily Living) (reported)
  - Mean: 83.37042280098512
  - Median: 0.0
  - Stddev: 580.7645874023438
  - Non-zero count: 1521158.0


- PIP_M:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal Independence Payment (Mobility)
  - Mean: 39.39152545160617
  - Median: 0.0
  - Stddev: 349.8207092285156
  - Non-zero count: 1086010.0


- PIP_M_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal Independence Payment (Mobility) (reported)
  - Mean: 39.39152545160617
  - Median: 0.0
  - Stddev: 349.8207092285156
  - Non-zero count: 1086010.0


- BSP:
  - Type: <class 'float'>
  - Entity: person
  - Description: Bereavement Support Payment
  - Mean: 3.577772528840778
  - Median: 0.0
  - Stddev: 166.6005096435547
  - Non-zero count: 57115.0


- BSP_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Bereavement Support Payment (reported)
  - Mean: 3.577772528840778
  - Median: 0.0
  - Stddev: 166.6005096435547
  - Non-zero count: 57115.0


- ESA_contrib:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based)
  - Mean: 59.53618590582191
  - Median: 0.0
  - Stddev: 649.055908203125
  - Non-zero count: 669633.0


- ESA_contrib_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employment and Support Allowance (contribution-based) (reported)
  - Mean: 59.53618590582191
  - Median: 0.0
  - Stddev: 649.055908203125
  - Non-zero count: 669633.0


- AFCS:
  - Type: <class 'float'>
  - Entity: person
  - Description: Armed Forces Compensation Scheme
  - Mean: 47.52285684127386
  - Median: 0.0
  - Stddev: 471.44287109375
  - Non-zero count: 810520.0


- AFCS_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Armed Forces Compensation Scheme (reported)
  - Mean: 3.788894075822291
  - Median: 0.0
  - Stddev: 184.4232940673828
  - Non-zero count: 61193.0


- carers_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Carer's Allowance
  - Mean: 38.15654342969305
  - Median: 0.0
  - Stddev: 385.408447265625
  - Non-zero count: 734581.0


- carers_allowance_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Carer's Allowance (reported)
  - Mean: 38.15654342969305
  - Median: 0.0
  - Stddev: 385.408447265625
  - Non-zero count: 734581.0


- JSA_contrib:
  - Type: <class 'float'>
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based)
  - Mean: 3.035765899700506
  - Median: 0.0
  - Stddev: 98.2900161743164
  - Non-zero count: 56433.0


- JSA_contrib_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Job Seeker's Allowance (contribution-based) (reported)
  - Mean: 3.035765899700506
  - Median: 0.0
  - Stddev: 98.2900161743164
  - Non-zero count: 56433.0


- AA:
  - Type: <class 'float'>
  - Entity: person
  - Description: Attendance Allowance
  - Mean: 47.52285684127386
  - Median: 0.0
  - Stddev: 471.44287109375
  - Non-zero count: 810520.0


- AA_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Attendance Allowance (reported)
  - Mean: 47.52285684127386
  - Median: 0.0
  - Stddev: 471.44287109375
  - Non-zero count: 810520.0


- SDA:
  - Type: <class 'float'>
  - Entity: person
  - Description: Severe Disablement Allowance
  - Mean: 0.4915901229170208
  - Median: 0.0
  - Stddev: 59.63357925415039
  - Non-zero count: 11916.0


- SDA_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Severe Disablement Allowance (reported)
  - Mean: 0.4915901229170208
  - Median: 0.0
  - Stddev: 59.63357925415039
  - Non-zero count: 11916.0


- IIDB:
  - Type: <class 'float'>
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit
  - Mean: 6.866091049184696
  - Median: 0.0
  - Stddev: 182.73863220214844
  - Non-zero count: 151046.0


- IIDB_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Industrial Injuries Disablement Benefit (reported)
  - Mean: 6.866091049184696
  - Median: 0.0
  - Stddev: 182.73863220214844
  - Non-zero count: 151046.0


- tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total tax liability
  - Mean: 3304.246913454149
  - Median: 0.0
  - Stddev: 8129.06201171875
  - Non-zero count: 32412537.0


- tax_modelling:
  - Type: <class 'float'>
  - Entity: person
  - Description: Difference between reported and imputed tax liabilities
  - Mean: -481.8615498351821
  - Median: 0.0
  - Stddev: 26922.630859375
  - Non-zero count: 17519968.0


- tax_reported:
  - Type: <class 'float'>
  - Entity: person
  - Description: Reported tax paid
  - Mean: 3786.1084525765727
  - Median: 52.0
  - Stddev: 28564.7890625
  - Non-zero count: 33916703.0


- NI_class_4:
  - Type: <class 'float'>
  - Entity: person
  - Description: Class 4 Contributions for National Insurance for the year
  - Mean: 60.438251267018984
  - Median: 0.0
  - Stddev: 385.0707702636719
  - Non-zero count: 2660037.0


- national_insurance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total amount of National Insurance liability for this person
  - Mean: 905.8048072170216
  - Median: 0.0
  - Stddev: 1424.17626953125
  - Non-zero count: 26580479.0


- NI_class_2:
  - Type: <class 'float'>
  - Entity: person
  - Description: Class 2 Contributions for National Insurance for the year
  - Mean: 7.028439784375397
  - Median: 0.0
  - Stddev: 30.571063995361328
  - Non-zero count: 2984789.0


- weekly_NI_class_2:
  - Type: <class 'float'>
  - Entity: person
  - Description: Class 2 Contributions for National Insurance
  - Mean: 7.028439784375397
  - Median: 0.0
  - Stddev: 30.571063995361328
  - Non-zero count: 2984789.0


- NI_exempt:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether is exempt from National Insurance
  - Mean: 0.3690666509057813
  - Median: 0.0
  - Stddev: 0.4938962976514026
  - Non-zero count: 24165951.0


- employee_NI_class_1:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 838.3381167806988
  - Median: 0.0
  - Stddev: 1394.8895263671875
  - Non-zero count: 23728103.0


- employer_NI:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employer contributions to National Insurance
  - Mean: 964.0888518075658
  - Median: 0.0
  - Stddev: 1604.1229248046875
  - Non-zero count: 23728103.0


- employer_NI_class_1:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 964.0888518075658
  - Median: 0.0
  - Stddev: 1604.1229248046875
  - Non-zero count: 23728103.0


- total_NI:
  - Type: <class 'float'>
  - Entity: person
  - Description: Total National Insurance contributions by employers and employees
  - Mean: 1869.893681123495
  - Median: 0.0
  - Stddev: 2996.97802734375
  - Non-zero count: 26580479.0


- weekly_employee_NI_class_1:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employee Class 1 Contributions for National Insurance
  - Mean: 838.3381167806988
  - Median: 0.0
  - Stddev: 1394.8895263671875
  - Non-zero count: 23728103.0


- weekly_employer_NI_class_1:
  - Type: <class 'float'>
  - Entity: person
  - Description: Employer Class 1 Contributions for National Insurance
  - Mean: 964.0888518075658
  - Median: 0.0
  - Stddev: 1604.1229248046875
  - Non-zero count: 23728103.0


- dividend_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from dividends
  - Mean: 150.93934860466814
  - Median: 0.0
  - Stddev: 2143.9443359375
  - Non-zero count: 3636930.0


- employment_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from employment
  - Mean: 11991.145646864125
  - Median: 0.0
  - Stddev: 21684.73828125
  - Non-zero count: 26715128.0


- miscellaneous_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from other sources
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- pension_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from pensions
  - Mean: 1633.9766744699848
  - Median: 0.0
  - Stddev: 6817.41455078125
  - Non-zero count: 9582497.0


- property_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from rental of property
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- savings_interest_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from interest on savings
  - Mean: 105.7838712164575
  - Median: 0.0
  - Stddev: 910.0344848632812
  - Non-zero count: 21166306.0


- social_security_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from social security
  - Mean: 1421.106945071725
  - Median: 0.0
  - Stddev: 3293.616455078125
  - Non-zero count: 12962546.0


- trading_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from trading profits
  - Mean: 1266.5595938058634
  - Median: 0.0
  - Stddev: 9073.2333984375
  - Non-zero count: 3738272.0


- ISA_interest_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount received in interest from Individual Savings Accounts
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- adjusted_net_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 16458.166191697463
  - Median: 9724.0
  - Stddev: 23339.107421875
  - Non-zero count: 44966830.0


- capital_allowances:
  - Type: <class 'float'>
  - Entity: person
  - Description: Full relief from capital expenditure allowances
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- deficiency_relief:
  - Type: <class 'float'>
  - Entity: person
  - Description: Deficiency relief
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- employment_deductions:
  - Type: <class 'float'>
  - Entity: person
  - Description: Deductions from employment income
  - Mean: 2.0078695343108297
  - Median: 0.0
  - Stddev: 125.98777770996094
  - Non-zero count: 449034.0


- employment_expenses:
  - Type: <class 'float'>
  - Entity: person
  - Description: Cost of expenses necessarily incurred and reimbursed by employment
  - Mean: 0.3024362313747988
  - Median: 0.0
  - Stddev: 5.3050055503845215
  - Non-zero count: 423893.0


- loss_relief:
  - Type: <class 'float'>
  - Entity: person
  - Description: Tax relief from trading losses
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- pension_contributions:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount contributed to registered pension schemes paid by the individual (not the employer)
  - Mean: 1.7054332999288027
  - Median: 0.0
  - Stddev: 125.82318115234375
  - Non-zero count: 35875.0


- pension_contributions_relief:
  - Type: <class 'float'>
  - Entity: person
  - Description: Reduction in taxable income from pension contributions
  - Mean: 1631.7102189221778
  - Median: 0.0
  - Stddev: 1766.8282470703125
  - Non-zero count: 29952273.0


- tax_free_savings_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income from savings in tax-free accounts
  - Mean: 52.80935880117734
  - Median: 0.0
  - Stddev: 628.3755493164062
  - Non-zero count: 9087589.0


- taxable_dividend_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of dividend income that is taxable
  - Mean: 150.93934860466814
  - Median: 0.0
  - Stddev: 2143.9443359375
  - Non-zero count: 3636930.0


- taxable_employment_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Net taxable earnings
  - Mean: 11989.2792082381
  - Median: 0.0
  - Stddev: 21680.869140625
  - Non-zero count: 26713361.0


- taxable_miscellaneous_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of miscellaneous income that is taxable
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- taxable_pension_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of pension income that is taxable
  - Mean: 1633.9766744699848
  - Median: 0.0
  - Stddev: 6817.41455078125
  - Non-zero count: 9582497.0


- taxable_property_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of property income that is taxable
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- taxable_savings_interest_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of savings interest which is taxable
  - Mean: 52.97451243096187
  - Median: 0.0
  - Stddev: 609.1726684570312
  - Non-zero count: 18075929.0


- taxable_social_security_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of social security income that is taxable
  - Mean: 1421.106945071725
  - Median: 0.0
  - Stddev: 3293.616455078125
  - Non-zero count: 12962546.0


- taxable_trading_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Amount of trading income that is taxable
  - Mean: 1209.8895050527624
  - Median: 0.0
  - Stddev: 8957.953125
  - Non-zero count: 3683806.0


- total_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Taxable income after tax reliefs and before allowances
  - Mean: 16569.512076617466
  - Median: 9877.300978557392
  - Stddev: 23409.869140625
  - Non-zero count: 45149424.0


- trading_loss:
  - Type: <class 'float'>
  - Entity: person
  - Description: Loss from trading in the current year.
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- allowances:
  - Type: <class 'float'>
  - Entity: person
  - Description: Allowances applicable to adjusted net income
  - Mean: 11746.152227916215
  - Median: 11850.0
  - Stddev: 995.1085815429688
  - Non-zero count: 65037177.0


- blind_persons_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Blind Person's Allowance for the year (not simulated)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- charitable_investment_gifts:
  - Type: <class 'float'>
  - Entity: person
  - Description: Gifts of qualifying investment or property to charities
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- covenanted_payments:
  - Type: <class 'float'>
  - Entity: person
  - Description: Covenanted payments to charities
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- dividend_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Dividend allowance for the person
  - Mean: 2000.0
  - Median: 2000.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- gift_aid:
  - Type: <class 'float'>
  - Entity: person
  - Description: Expenditure under Gift Aid
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- marriage_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- married_couples_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Married Couples' allowance for the year
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- married_couples_allowance_deduction:
  - Type: <class 'float'>
  - Entity: person
  - Description: Deduction from Married Couples' allowance for the year
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- other_deductions:
  - Type: <class 'float'>
  - Entity: person
  - Description: All other tax deductions
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- pension_annual_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Annual Allowance for pension contributions
  - Mean: 39970.22928250767
  - Median: 40000.0
  - Stddev: 820.6321411132812
  - Non-zero count: 65478555.0


- personal_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Personal Allowance for the year
  - Mean: 11746.152227916215
  - Median: 11850.0
  - Stddev: 995.1085815429688
  - Non-zero count: 65037177.0


- property_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Property Allowance for the year
  - Mean: 1000.0
  - Median: 1000.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- property_allowance_deduction:
  - Type: <class 'float'>
  - Entity: person
  - Description: Deduction applied by the property allowance
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- savings_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings Allowance for the year
  - Mean: 961.7226128462976
  - Median: 1000.0
  - Stddev: 135.6366729736328
  - Non-zero count: 65185864.0


- trading_allowance:
  - Type: <class 'float'>
  - Entity: person
  - Description: Trading Allowance for the year
  - Mean: 1000.0
  - Median: 1000.0
  - Stddev: 0.0
  - Non-zero count: 65478555.0


- trading_allowance_deduction:
  - Type: <class 'float'>
  - Entity: person
  - Description: Deduction applied by the trading allowance
  - Mean: 56.67008875310123
  - Median: 0.0
  - Stddev: 219.7454071044922
  - Non-zero count: 3738272.0


- CB_HITC:
  - Type: <class 'float'>
  - Entity: person
  - Description: Child Benefit High-Income Tax Charge
  - Mean: 29.3396309730242
  - Median: 0.0
  - Stddev: 224.3818817138672
  - Non-zero count: 1409294.0


- add_rate_earned_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the additional rate
  - Mean: 302.00758188406115
  - Median: 0.0
  - Stddev: 6273.89501953125
  - Non-zero count: 282559.0


- add_rate_earned_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income tax on earned income at the additional rate
  - Mean: 135.90340790521344
  - Median: 0.0
  - Stddev: 2823.252685546875
  - Non-zero count: 282559.0


- add_rate_savings_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 2.6704767089392853
  - Median: 0.0
  - Stddev: 463.2538757324219
  - Non-zero count: 3334.0


- basic_rate_earned_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the basic rate
  - Mean: 7235.271235172092
  - Median: 0.0
  - Stddev: 10804.4560546875
  - Non-zero count: 29746178.0


- basic_rate_earned_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income tax on earned income at the basic rate
  - Mean: 1447.0542618473598
  - Median: 0.0
  - Stddev: 2160.891357421875
  - Non-zero count: 29746178.0


- basic_rate_savings_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings income at the basic rate
  - Mean: 6.937106168380004
  - Median: 0.0
  - Stddev: 226.10757446289062
  - Non-zero count: 103453.0


- basic_rate_savings_income_pre_starter:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings income which would otherwise be taxed at the basic rate, without the starter rate
  - Mean: 12.87274401596512
  - Median: 0.0
  - Stddev: 253.93240356445312
  - Non-zero count: 515553.0


- dividend_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income tax on dividend income
  - Mean: 19.52248199795098
  - Median: 0.0
  - Stddev: 468.4195861816406
  - Non-zero count: 688775.0


- earned_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income tax on earned income
  - Mean: 2375.97443102537
  - Median: 0.0
  - Stddev: 7127.99072265625
  - Non-zero count: 29746178.0


- earned_taxable_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Non-savings, non-dividend income for Income Tax
  - Mean: 9519.820740930361
  - Median: 0.0
  - Stddev: 21047.828125
  - Non-zero count: 29746178.0


- higher_rate_earned_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Earned income (non-savings, non-dividend) at the higher rate
  - Mean: 1982.5419238742077
  - Median: 0.0
  - Stddev: 10577.8525390625
  - Non-zero count: 4606557.0


- higher_rate_earned_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income tax on earned income at the higher rate
  - Mean: 793.0167805098414
  - Median: 0.0
  - Stddev: 4231.14111328125
  - Non-zero count: 4606557.0


- higher_rate_savings_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings income at the higher rate
  - Mean: 0.8901677674636185
  - Median: 0.0
  - Stddev: 68.01142883300781
  - Non-zero count: 15247.0


- income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income Tax
  - Mean: 2398.442115404808
  - Median: 0.0
  - Stddev: 7189.61962890625
  - Non-zero count: 30034622.0


- income_tax_pre_charges:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income Tax before any tax charges
  - Mean: 2398.442115404808
  - Median: 0.0
  - Stddev: 7189.61962890625
  - Non-zero count: 30034622.0


- is_higher_earner:
  - Type: <class 'bool'>
  - Entity: person
  - Description: Whether this person is the highest earner in a family
  - Mean: 0.5352827807516523
  - Median: 1.0
  - Stddev: 0.49960493110885895
  - Non-zero count: 35049543.0


- pays_scottish_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Whether the individual pays Scottish Income Tax rates
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- savings_income_tax:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income tax on savings income
  - Mean: 2.9452028096524843
  - Median: 0.0
  - Stddev: 215.34140014648438
  - Non-zero count: 117062.0


- savings_starter_rate_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings income which is tax-free under the starter rate
  - Mean: 4988.707896784484
  - Median: 5000.0
  - Stddev: 194.809326171875
  - Non-zero count: 65441665.0


- tax_band:
  - Type: Categorical
  - Entity: person
  - Description: Tax band of the individual


- taxed_dividend_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Dividend income which is taxed
  - Mean: 115.13007408605016
  - Median: 0.0
  - Stddev: 2025.879150390625
  - Non-zero count: 688775.0


- taxed_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Income which is taxed
  - Mean: 9645.448564698187
  - Median: 0.0
  - Stddev: 21252.37890625
  - Non-zero count: 30034622.0


- taxed_savings_income:
  - Type: <class 'float'>
  - Entity: person
  - Description: Savings income which advances the person's income tax schedule
  - Mean: 10.497750644782908
  - Median: 0.0
  - Stddev: 521.518310546875
  - Non-zero count: 117062.0


- H_CTANNUAL:
  - Type: <class 'float'>
  - Entity: household
  - Description: None
  - Mean: nan
  - Median: 1322.6231604476818
  - Stddev: 599.0809326171875
  - Non-zero count: 26726432.0


- H_GBHSCOST:
  - Type: <class 'float'>
  - Entity: household
  - Description: None
  - Mean: 4132.446198247879
  - Median: 2964.0
  - Stddev: 5423.572265625
  - Non-zero count: 27024466.0


- H_NIHSCOST:
  - Type: <class 'float'>
  - Entity: household
  - Description: None
  - Mean: 61.788114013018244
  - Median: 0.0
  - Stddev: 1035.5233154296875
  - Non-zero count: 711980.0


- H_HHRENT:
  - Type: <class 'float'>
  - Entity: household
  - Description: None
  - Mean: 2650.144389836323
  - Median: 0.0
  - Stddev: 5322.75634765625
  - Non-zero count: 9990064.0


- H_PTENTYP2:
  - Type: <class 'float'>
  - Entity: household
  - Description: None
  - Mean: 4.335349866309301
  - Median: 5.0
  - Stddev: 1.6638318300247192
  - Non-zero count: 27828787.0


- P_GROSS4:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1851.1850878047019
  - Median: 1471.0
  - Stddev: 1175.42041015625
  - Non-zero count: 51553959.0


- B_GROSS4:
  - Type: <class 'float'>
  - Entity: benunit
  - Description: None
  - Mean: 2420.2049674370933
  - Median: 1700.0
  - Stddev: 1157.133056640625
  - Non-zero count: 35049543.0


- H_GROSS4:
  - Type: <class 'float'>
  - Entity: household
  - Description: None
  - Mean: 2295.636794194443
  - Median: 1561.0
  - Stddev: 1106.8741455078125
  - Non-zero count: 27828787.0


- P_UGRSPAY:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 230.59895450702305
  - Median: 0.0
  - Stddev: 417.0141906738281
  - Non-zero count: 26715128.0


- P_UDEDUC1:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0327967938576035
  - Median: 0.0
  - Stddev: 2.4196765422821045
  - Non-zero count: 35875.0


- P_INPENINC:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 31.422628355192018
  - Median: 0.0
  - Stddev: 131.1041259765625
  - Non-zero count: 9582497.0


- P_PROFIT1:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 38.2840125508106
  - Median: 0.0
  - Stddev: 2083.122802734375
  - Non-zero count: 3124544.0


- P_PROFIT2:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.05099121384092853
  - Median: 0.0
  - Stddev: 0.2313183695077896
  - Non-zero count: 3125390.0


- P_ACCINT_ACCOUNT_CODE_1:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.20625582411928248
  - Median: 0.0
  - Stddev: 1.9136323928833008
  - Non-zero count: 10162745.0


- P_ACCINT_ACCOUNT_CODE_2:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.03768717901002078
  - Median: 0.0
  - Stddev: 0.9437406659126282
  - Non-zero count: 600400.0


- P_ACCINT_ACCOUNT_CODE_3:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.06111944136305936
  - Median: 0.0
  - Stddev: 1.670320749282837
  - Non-zero count: 538069.0


- P_ACCINT_ACCOUNT_CODE_4:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_5:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.6918207547284189
  - Median: 0.0
  - Stddev: 10.904861450195312
  - Non-zero count: 11417661.0


- P_ACCINT_ACCOUNT_CODE_6:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.05740274831243507
  - Median: 0.0
  - Stddev: 3.2839646339416504
  - Non-zero count: 70161.0


- P_ACCINT_ACCOUNT_CODE_7:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.5795020950843138
  - Median: 0.0
  - Stddev: 16.31266212463379
  - Non-zero count: 576737.0


- P_ACCINT_ACCOUNT_CODE_8:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 2.3216538392227166
  - Median: 0.0
  - Stddev: 34.869937896728516
  - Non-zero count: 3309939.0


- P_ACCINT_ACCOUNT_CODE_9:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_10:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_11:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_12:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_13:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_14:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_15:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_16:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_17:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_18:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_19:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_21:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.9581618412273013
  - Median: 0.0
  - Stddev: 11.621087074279785
  - Non-zero count: 9052293.0


- P_ACCINT_ACCOUNT_CODE_22:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_23:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_24:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.001523824172914339
  - Median: 0.0
  - Stddev: 0.3700384497642517
  - Non-zero count: 8101.0


- P_ACCINT_ACCOUNT_CODE_25:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_26:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_27:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.019891751396932285
  - Median: 0.0
  - Stddev: 1.8494123220443726
  - Non-zero count: 419439.0


- P_ACCINT_ACCOUNT_CODE_28:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0019656690391845278
  - Median: 0.0
  - Stddev: 0.11600235849618912
  - Non-zero count: 227372.0


- P_ACCINT_ACCOUNT_CODE_29:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_ACCINT_ACCOUNT_CODE_30:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- H_SUBLET:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_INDINC:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 380.33410760209966
  - Median: 269.0
  - Stddev: 2129.709228515625
  - Non-zero count: 49349156.0


- P_NINDINC:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 307.5243296679348
  - Median: 250.0
  - Stddev: 2136.50732421875
  - Non-zero count: 49004666.0


- P_CHINCDV:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.42692490239923836
  - Median: 0.0
  - Stddev: 6.605302810668945
  - Non-zero count: 635049.0


- P_BENAMT_BENEFIT_CODE_1:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.2275568830377608
  - Median: 0.0
  - Stddev: 10.366942405700684
  - Non-zero count: 1317063.0


- P_BENAMT_BENEFIT_CODE_2:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.7911449348698367
  - Median: 0.0
  - Stddev: 7.425051212310791
  - Non-zero count: 1106456.0


- P_BENAMT_BENEFIT_CODE_3:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 3.072351002604676
  - Median: 0.0
  - Stddev: 10.529207229614258
  - Non-zero count: 6424339.0


- P_BENAMT_BENEFIT_CODE_4:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.9049047511253091
  - Median: 0.0
  - Stddev: 10.527261734008789
  - Non-zero count: 1132019.0


- P_BENAMT_BENEFIT_CODE_5:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 25.370472995890815
  - Median: 0.0
  - Stddev: 62.55794143676758
  - Non-zero count: 11554244.0


- P_BENAMT_BENEFIT_CODE_6:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.06880332614072532
  - Median: 0.0
  - Stddev: 3.2038559913635254
  - Non-zero count: 57115.0


- P_BENAMT_BENEFIT_CODE_8:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.07286334552092445
  - Median: 0.0
  - Stddev: 3.5466010570526123
  - Non-zero count: 61193.0


- P_BENAMT_BENEFIT_CODE_9:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.13079863812041118
  - Median: 0.0
  - Stddev: 4.628013610839844
  - Non-zero count: 95401.0


- P_BENAMT_BENEFIT_CODE_10:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.00945365647092388
  - Median: 0.0
  - Stddev: 1.1467994451522827
  - Non-zero count: 11916.0


- P_BENAMT_BENEFIT_CODE_12:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.9139006247224473
  - Median: 0.0
  - Stddev: 9.066205024719238
  - Non-zero count: 810520.0


- P_BENAMT_BENEFIT_CODE_13:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.7337793547113397
  - Median: 0.0
  - Stddev: 7.411696910858154
  - Non-zero count: 734581.0


- P_BENAMT_BENEFIT_CODE_14:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.05838009657883072
  - Median: 0.0
  - Stddev: 1.890191912651062
  - Non-zero count: 56433.0


- P_BENAMT_BENEFIT_CODE_1014:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.35048463697133764
  - Median: 0.0
  - Stddev: 5.626163005828857
  - Non-zero count: 289811.0


- P_BENAMT_BENEFIT_CODE_15:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.13204025207145328
  - Median: 0.0
  - Stddev: 3.51420521736145
  - Non-zero count: 151046.0


- P_BENAMT_BENEFIT_CODE_16:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.1449266670285432
  - Median: 0.0
  - Stddev: 12.481844902038574
  - Non-zero count: 669633.0


- P_BENAMT_BENEFIT_CODE_17:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.021419911629228756
  - Median: 0.0
  - Stddev: 1.744089961051941
  - Non-zero count: 14487.0


- P_BENAMT_BENEFIT_CODE_19:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.609077572791142
  - Median: 0.0
  - Stddev: 8.392365455627441
  - Non-zero count: 517051.0


- P_BENAMT_BENEFIT_CODE_21:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.060122158956462356
  - Median: 0.0
  - Stddev: 2.421231985092163
  - Non-zero count: 30560.0


- P_BENAMT_BENEFIT_CODE_22:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.07108052399751338
  - Median: 0.0
  - Stddev: 7.067324638366699
  - Non-zero count: 10340.0


- P_BENAMT_BENEFIT_CODE_24:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.42854038619502804
  - Median: 0.0
  - Stddev: 30.246965408325195
  - Non-zero count: 18259.0


- P_BENAMT_BENEFIT_CODE_30:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.008631345017299778
  - Median: 0.0
  - Stddev: 0.608738124370575
  - Non-zero count: 7698.0


- P_BENAMT_BENEFIT_CODE_31:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.013205179390377094
  - Median: 0.0
  - Stddev: 1.410167932510376
  - Non-zero count: 11431.0


- P_BENAMT_BENEFIT_CODE_32:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0011185509233085649
  - Median: 0.0
  - Stddev: 0.27717453241348267
  - Non-zero count: 1273.0


- P_BENAMT_BENEFIT_CODE_33:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.17604293869200677
  - Median: 0.0
  - Stddev: 19.879169464111328
  - Non-zero count: 46066.0


- P_BENAMT_BENEFIT_CODE_34:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.039702907463516346
  - Median: 0.0
  - Stddev: 9.636493682861328
  - Non-zero count: 2857.0


- P_BENAMT_BENEFIT_CODE_35:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0047529847762613825
  - Median: 0.0
  - Stddev: 0.5301652550697327
  - Non-zero count: 8337.0


- P_BENAMT_BENEFIT_CODE_36:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0034614432716524204
  - Median: 0.0
  - Stddev: 0.41830483078956604
  - Non-zero count: 4316.0


- P_BENAMT_BENEFIT_CODE_37:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.008931200751937705
  - Median: 0.0
  - Stddev: 2.154486656188965
  - Non-zero count: 2834.0


- P_BENAMT_BENEFIT_CODE_61:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.004021655817474738
  - Median: 0.0
  - Stddev: 0.3991522789001465
  - Non-zero count: 9175.0


- P_BENAMT_BENEFIT_CODE_62:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 30.420323111895186
  - Median: 0.0
  - Stddev: 75.54754638671875
  - Non-zero count: 11743418.0


- P_BENAMT_BENEFIT_CODE_65:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.00885438409263832
  - Median: 0.0
  - Stddev: 0.5729027986526489
  - Non-zero count: 57795.0


- P_BENAMT_BENEFIT_CODE_66:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.019222960086278683
  - Median: 0.0
  - Stddev: 0.7371646165847778
  - Non-zero count: 108848.0


- P_BENAMT_BENEFIT_CODE_69:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.03616742075129925
  - Median: 0.0
  - Stddev: 1.1040213108062744
  - Non-zero count: 144318.0


- P_BENAMT_BENEFIT_CODE_70:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.044445782752744634
  - Median: 0.0
  - Stddev: 1.04928457736969
  - Non-zero count: 193427.0


- P_BENAMT_BENEFIT_CODE_78:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.004786361038611826
  - Median: 0.0
  - Stddev: 0.7367099523544312
  - Non-zero count: 2908.0


- P_BENAMT_BENEFIT_CODE_81:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0614657906399449
  - Median: 0.0
  - Stddev: 6.849862098693848
  - Non-zero count: 11701.0


- P_BENAMT_BENEFIT_CODE_82:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.02156213283580073
  - Median: 0.0
  - Stddev: 2.294243574142456
  - Non-zero count: 11922.0


- P_BENAMT_BENEFIT_CODE_83:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.06771427098193467
  - Median: 0.0
  - Stddev: 28.940170288085938
  - Non-zero count: 4622.0


- P_BENAMT_BENEFIT_CODE_90:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.9370164115173638
  - Median: 0.0
  - Stddev: 9.667802810668945
  - Non-zero count: 1257876.0


- P_BENAMT_BENEFIT_CODE_91:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 3.845770221697506
  - Median: 0.0
  - Stddev: 24.91887855529785
  - Non-zero count: 2455681.0


- P_BENAMT_BENEFIT_CODE_92:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 3.433185109231564e-05
  - Median: 0.0
  - Stddev: 0.00963511411100626
  - Non-zero count: 1124.0


- P_BENAMT_BENEFIT_CODE_94:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 4.783708675953754
  - Median: 0.0
  - Stddev: 22.909976959228516
  - Non-zero count: 3596990.0


- P_BENAMT_BENEFIT_CODE_95:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.5863135713199308
  - Median: 0.0
  - Stddev: 17.673254013061523
  - Non-zero count: 722795.0


- P_BENAMT_BENEFIT_CODE_96:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.603276539547319
  - Median: 0.0
  - Stddev: 11.16854476928711
  - Non-zero count: 1521158.0


- P_BENAMT_BENEFIT_CODE_97:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.757529266764105
  - Median: 0.0
  - Stddev: 6.727321147918701
  - Non-zero count: 1086010.0


- P_BENAMT_BENEFIT_CODE_98:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.96324226229041
  - Median: 0.0
  - Stddev: 39.89448928833008
  - Non-zero count: 252074.0


- P_BENAMT_BENEFIT_CODE_99:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.7329860440567144
  - Median: 0.0
  - Stddev: 110.02783203125
  - Non-zero count: 34693.0


- P_BENAMT_BENEFIT_CODE_102:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_103:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_104:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_105:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_106:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_107:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_108:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_109:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.0
  - Median: 0.0
  - Stddev: 0.0
  - Non-zero count: 0.0


- P_BENAMT_BENEFIT_CODE_110:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.011251144273243507
  - Median: 0.0
  - Stddev: 0.6607882976531982
  - Non-zero count: 37945.0


- P_BENAMT_BENEFIT_CODE_111:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.03936244375842594
  - Median: 0.0
  - Stddev: 1.188767910003662
  - Non-zero count: 134537.0


- P_AGE80:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 38.05373212649546
  - Median: 39.3239598278348
  - Stddev: 26.59808349609375
  - Non-zero count: 51553959.0


- P_AGE:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.7672470169813612
  - Median: 0.0
  - Stddev: 4.316173553466797
  - Non-zero count: 13118653.0


- P_PERSON:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.273965376908516
  - Median: 1.0
  - Stddev: 0.8990830183029175
  - Non-zero count: 51553959.0


- P_UPERSON:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 1.0393994644506128
  - Median: 1.0
  - Stddev: 0.6924399137496948
  - Non-zero count: 51553959.0


- P_TYPEED2:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.2715005699194187
  - Median: 0.0
  - Stddev: 1.2658056020736694
  - Non-zero count: 1995959.0


- P_TOTHOURS:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 888.9562388892862
  - Median: 0.0
  - Stddev: 1013.0665283203125
  - Non-zero count: 31045772.0


- P_SEINCAMT:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 24.35691504473924
  - Median: 0.0
  - Stddev: 174.48526000976562
  - Non-zero count: 3738272.0


- P_EMPSTATI:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 2.9084855492000394
  - Median: 1.0
  - Stddev: 3.1097352504730225
  - Non-zero count: 51553959.0


- P_FUELAMT:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.007607548743008394
  - Median: 0.0
  - Stddev: 0.4254932403564453
  - Non-zero count: 15244.0


- P_MILEAMT:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.2248258506456203
  - Median: 0.0
  - Stddev: 4.760979652404785
  - Non-zero count: 304590.0


- P_MOTAMT:
  - Type: <class 'float'>
  - Entity: person
  - Description: None
  - Mean: 0.07000283183072852
  - Median: 0.0
  - Stddev: 2.1174943447113037
  - Non-zero count: 122426.0


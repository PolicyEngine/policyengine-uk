## [2.109.7] - 2026-10-03

### Changed

- - Tighten the Housing Benefit passport tests: hold Guarantee Credit at nil in the contributory-benefit property control, and base the applicable-income arithmetic fixtures on earnings and working tax credit rather than Child Benefit.

### Fixed

- - Disregard the whole income and capital of a Housing Benefit claimant in receipt of Income Support, income-based Jobseeker's Allowance or income-related Employment and Support Allowance, as SI 2006/213 Schedule 5 paragraph 4 and Schedule 6 paragraph 5 (Northern Ireland: SR 2006/405 Schedule 6 paragraph 4 and Schedule 7 paragraph 5) require, so they get maximum Housing Benefit. These benefits were counted as income and tapered. The passport has no age condition, so it covers mixed-age couples whose younger member is on one of these benefits (SI 2006/213 regulation 5(1)(b)). Adds `in_receipt_of_income_support_jsa_ib_or_esa_ir`.


## [2.109.6] - 2026-10-03

### Fixed

- - Encode petrol and diesel fuel duty as its dated statutory schedule (52.95p to 31 December 2026, 55.95p from 1 January 2027, 57.95p from 1 March 2027 under SI 2026/164 as amended by SI 2026/555), day-weighted across each model year, with April RPI uprating from 2027 forecast from the OBR March 2026 RPI series. Model year 2027 is now 59.77p a litre rather than a calendar-year average of 59.25p. Move LPG and natural gas rate steps to 1 January and 1 March 2027, and drop the 2012 petrol and diesel rate that was never charged.


## [2.109.5] - 2026-10-03

### Changed

- Run the CI Test job on Linux arm64 with four pytest-xdist workers (pytest-xdist is now a dev dependency), cancel superseded pull request runs, and time the job out after 60 minutes.


## [2.109.4] - 2026-10-03

### Fixed

- - Date the Pension Credit exclusion of mixed-age couples (State Pension Credit Act 2002 s.4(1A)) from 15 May 2019, and model the SI 2019/37 article 4 saving. Before the change, mixed-age couples could claim Pension Credit and pension-age Housing Benefit, and now take that route rather than Universal Credit. Afterwards, a couple entitled to Pension Credit or pension-age Housing Benefit on 14 May 2019 keeps them while it stays entitled. The saving is a new input, `has_mixed_age_couple_pension_credit_saving`, which by default is inferred from reported Pension Credit or pension-age Housing Benefit without reported Universal Credit, where the older member was born by 1954. A family on the Pension Credit route is no longer eligible for Universal Credit.


## [2.109.3] - 2026-10-03

### Fixed

- - Pension Credit assessable capital now reads `is_claimant_or_partner` rather than the Universal Credit claimant flag to decide whose person-level capital counts, and the legacy and Pension Credit person-level capital parameter descriptions name that flag. The Lifetime ISA tests now set it on families the age presumption would otherwise treat as couples, and pin that Pension Credit ignores the Universal Credit flag.


## [2.109.2] - 2026-10-03

### Changed

- Since 2.106.0, `carer_support_payment` means the Carer Support Payment component only, as "carer support payment" does in the reserved-benefit regulations since SI 2026/246. The Scottish Carer Supplement is the separate `scottish_carer_supplement`; code that summed `carer_support_payment` for the total paid to a Scottish carer must add both.


## [2.109.1] - 2026-10-03

### Fixed

- Stop exempting mixed-age couples on Universal Credit from the benefit cap (UC Regs 2013 regs 79, 82 and 83 have no age exception), and stop treating them as pensioners for Council Tax Reduction (SI 2012/2885 reg 3, WSI 2013/3029 reg 3, SSI 2021/249 reg 3). The cap's age exemption now follows which Housing Benefit regulations apply (HB Regs 2006 reg 5), through the new `housing_benefit_pension_age_regulations_apply`; the CTR pensioner test is the new `council_tax_reduction_pensioner`. Both read the claimant and partner (`is_claimant_or_partner`), and a Universal Credit award counts only where one of them is under State Pension age, so a pensioner whose only younger member is an 18- or 19-year-old dependant keeps pensioner treatment, with or without `is_parent`. CTR amounts change only in England, where such couples move to the local working-age scheme; in Wales and Scotland CTR changes only through the capped Universal Credit counted as income. Outside the five English councils the model simulates (Newham, Merton, Kingston upon Thames, Westminster and Oxford), the working-age scheme uses reported CTR, so a household calculation for a mixed-age couple on Universal Credit in the rest of England now shows CTR of £0 unless a reported amount is entered.


## [2.109.0] - 2026-10-03

### Added

- Add an optional State Pension earnings-path guarantee (`gov.dwp.state_pension.triple_lock.earnings_path_guarantee`), so reforms that keep the pension in line with earnings over time, such as one reading of the plan announced in September 2026, can be modelled as parameter changes. Off under current law.

### Changed

- Computed the State Pension triple lock from September CPI and May-July AWE total pay growth used in each uprating review, followed by OBR September CPI and Q2 earnings forecasts and then calendar-year growth, with macro scenarios moving those forecasts and `active: false` leaving non-negative earnings growth; April 2027's 3.9% rise and projected £250.71 new State Pension weekly rate use the 15 September 2026 first earnings estimate and stay provisional until the October labour market release, the vintage the review uses.
- Changed `yoy_growth.triple_lock` to use the previous year's September CPI and May-July AWE inputs rounded to 0.1 percentage points before taking the maximum of the included elements and configured floor, including CPI forecast gaps for observation years 2026–2030 and earnings forecast gaps for 2027–2030, with April 2027 determined by the provisional 3.9% earnings input; `triple_lock.outturn` is null from 2012, the generated uprating series runs through April 2074 and follows rounded lagged calendar-year earnings from April 2035 under the stored baseline, and basic and new State Pension levels are about 0.48% higher in 2027–2034 than under the previous baseline, with a growing gap thereafter and the 2027-onward changes provisional until the October 2026 labour market release.


## [2.108.0] - 2026-10-02

### Fixed

- Universal Credit no longer counts actual savings interest, dividends or rent as unearned income: regulation 66(1) of the Universal Credit Regulations 2013 lists no description that covers them, so capital counts only through its assumed yield (tariff income).
- - Stopped the trading allowance being deducted on top of expenses already netted out of self-employment profit (ITTOIA 2005 Part 6A). It now gives full relief only where profit is within the allowance, and partial relief when the new optional `self_employment_gross_receipts` input shows that expenses and capital allowances fall short of it. The allowance now starts in 2017-18.

### Removed

- Removed the `gov.dwp.universal_credit.means_test.income_definitions.capital_derived` parameter, which gated the removal of interest, dividends and rent from Universal Credit unearned income.


## [2.107.0] - 2026-10-02

### Added

- - Added HBAI population variables (`is_hbai_dependent_child`, `is_hbai_adult`, `is_hbai_working_age_adult`, `is_hbai_pensioner`, `hbai_person_type`, and the equivalence-scale child bands) following the HBAI FYE 2025 glossary, `is_claimant_or_partner` for the single adult or couple a benefit unit is formed around, and programme-named child, young person and responsibility variables for Universal Credit, tax credits, the legacy means-tested benefits, the WTC childcare element and student support.

### Changed

- - Deprecated the generic age-18 variables (`is_child`, `is_adult`, `num_children`, `num_adults`, `family_type`, `child_index`, the eldest and youngest child and adult ages, `benunit_count_children`, `benunit_count_adults`, the disabled child and adult counts, `is_WA_adult`, `is_young_child`, `is_older_child`). They keep their formulas for downstream users, but no model rule reads them any more: each programme uses its own legal definition of a child or young person and of the claimant and partner.

### Fixed

- - Fixed benefit-unit structure: a lone parent living with an 18- or 19-year-old still at school is no longer treated as a (married) couple, a couple with such a dependant is no longer treated as single or a lone parent, and a 16- or 17-year-old heading their own benefit unit is a single claimant rather than a couple with themselves as the child. Lone parent, single claimant and couple are now mutually exclusive.
  - A benefit unit now has at most two claimants or partners: the head (the eldest adult head if more than one is given, or the eldest adult if the head is not an adult) and one partner (a member flagged as a parent if there is one, otherwise the eldest other adult). When the head is not flagged as a parent but two other members are, those two are the couple. Without relationship inputs, a member under 20 and at least 16 years younger than the head is presumed to be the head's child rather than their partner, so a lone parent with an 18-year-old at university stays single and a couple with one stays a couple of two. Datasets and users can supply `is_claimant_or_partner` directly.
  - Fixed Marriage Allowance and the CPS marriage reforms to transfer allowance and split income only between spouses or civil partners, never from a child in the benefit unit; the Tax-Free Childcare work condition to test the applicant and partner only; the WTC lone parent, couple, disability and childcare elements and eligibility routes to use the tax credit claimant and child definitions; and the DfE schemes (Care to Learn, Childcare Grant, Parents' Learning Allowance, extended childcare income test) to use each scheme's own definition of a child or of the parent and partner.
  - The HBAI equivalence scale now weights HBAI adults and dependent children, which changes factors only in households with no one aged 18 or over.
- - Updated legacy benefits to use claimant and partner roles and programme-specific child definitions for legacy benefit allowances, income disregards, capital allocation, disability premiums, Housing Benefit childcare charges, and Council Tax Reduction exemptions.
  - A child or young person placed with the family by a local authority is no longer counted as a member of the family for the legacy benefits (Income Support Regulations 1987 reg 16(4); Housing Benefit Regulations 2006 reg 21(3)).
  - Housing Benefit's pension-age route now tests the claimant and any partner (SI 2014/1230 reg 6A(4)), so a pensioner living with an 18- or 19-year-old dependant can make a new Housing Benefit claim.
- - Replaced age-18 child/adult flags in the LHA shared accommodation rate and the benefit-cap rates with claimant/partner status and responsibility for a child or young person. Because one LHA category and one benefit cap serve both Universal Credit and Housing Benefit, the family rates apply if either scheme's test is met (UC regs 4-5, including the reg 5(1)(a) route for 16-year-olds; HB reg 19), via the new `is_responsible_for_child_or_young_person_for_uc_or_housing_benefit`.
  - Renters under 35 receiving attendance allowance, the DLA care component at the middle or highest rate, or the PIP daily living component are now excepted from the shared accommodation rate (UC Regulations 2013 Sch 4 para 29(5)). The exception is UC's; the Housing Benefit "young individual" definition (HB Regulations 2006 reg 2(1)) has no disability exception, but the model uses one LHA category for both schemes. The other paragraph 29 exceptions and the conservative LHA non-dependant proxy remain as documented limits.
- - Universal Credit, Housing Benefit, Income Support, tax credit and Council Tax Reduction means tests now count only the income of the claimant, any partner and the programme's own children or young persons, the members the model already counted. The income of any other member of the benefit unit no longer counts: for example an 18- or 19-year-old who is presumed to be the claimant's child but is neither a partner nor a qualifying young person. The same applies to the hours behind the Housing Benefit worker disregard. The shared helper is `add_for_members`. The regulations count only the claimant's and partner's income (UC Regulations 2013 reg 22; HB Regulations 2006 reg 25; IS Regulations 1987 reg 23; Tax Credits Act 2002 s.7; Council Tax Reduction Schemes (Prescribed Requirements) (England) Regulations 2012 Sch 1 para 11). Dropping dependants' own income as well is left to a follow-up, because some survey records give children adult-level incomes.
- - Applied Pension Credit age conditions, income assessment and carer and severe disability additions to claimants and partners rather than dependent children and young people, and removed the severe disability addition's child veto.
  - The Pension Credit severe disability addition now follows SPC Regulations 2002 Sch I para 1(1) and reg 6(5): a claimant with a partner qualifies if both receive a qualifying disability benefit and a carer benefit is paid for at most one of them (double amount when none is paid, single amount when one is), or if one receives it, the other is blind and no carer benefit is paid for the first (single amount). The person cared for is not observed, so each carer benefit paid in the benefit unit is taken to be for a different claimant or partner, and never for its recipient (a qualifying claimant's own Carer's Allowance does not bar them). The household non-dependant residence test and the mixed-age transitional protection remain unmodelled.
  - Guarantee Credit is now paid only to benefit units eligible for Pension Credit, so it can no longer act as a passport (for example to targeted childcare) for families that do not qualify.
- - Apply Universal Credit age conditions, childcare work conditions, and household capital allocation to claimants and partners, with documented proxies for the observable minimum-age exceptions from age 16. Rename the capital allocation helper to `household_uc_unreported_claimants`.


## [2.106.1] - 2026-10-02

### Fixed

- - Hold the NICs primary threshold, upper earnings limit, secondary threshold and Class 4 lower and upper profits limits at their 2026-27 levels through 2030-31, as announced at Budget 2025, with a reference for each year. CPI uprating resumes in 2031-32; before this change the Class 4 limits were uprated from 2027-28 and the primary threshold and upper earnings limit from 2028-29. Also correct the 2025-26 lower earnings limit to £125 a week (SI 2025/288).


## [2.106.0] - 2026-10-02

### Added

- Add `scottish_carer_supplement`, the Scottish Carer Supplement paid with Carer Support Payment from 15 March 2026. `carer_support_payment` is now the Carer Support Payment component only, so totals summed by variable name need both variables.

### Fixed

- Count Carer's Allowance and Carer Support Payment as Pension Credit income (SPC Regs 2002 reg 15(1)), and split the Scottish Carer Supplement out of Carer Support Payment into its own variable so that Pension Credit and Housing Benefit leave it out (SI 2026/246).


## [2.105.1] - 2026-10-02

### Fixed

- Apply the Local Housing Allowance cap to the eligible rent before the Housing Benefit taper and non-dependant deductions, as SI 2006/213 regs 12D(2)(a), 70 and 71 (SI 2006/214 regs 12D, 50 and 51 at pension age) require, rather than capping the tapered rent.


## [2.105.0] - 2026-10-02

### Added

- Add `pension_credit_reported_capital`, a benefit-unit input that replaces the household proxy in Pension Credit assessable capital when a dataset records the claimant's and partner's own capital (default -1: no change).


## [2.104.8] - 2026-10-02

### Fixed

- Hold Northern Ireland households' council tax flat when a dataset is projected forward, instead of growing it by England's council tax forecast: the uprating code looked for the label `NORTHERN IRELAND` (with a space), so Northern Ireland fell through to England. Region labels outside the `Region` enum now raise rather than taking England's growth.


## [2.104.7] - 2026-10-02

### Fixed

- Count State Pension as Universal Credit unearned income (retirement pension income, UC Regs 2013 regs 66(1)(a) and 67). Mixed-age couples on UC were having their State Pension ignored.


## [2.104.6] - 2026-10-02

### Fixed

- Copy arrays read from the simulation before writing into them in the Universal Credit rebalancing and PIP phase-in scenario modifiers, so the cache changes only through `set_input`. Results are unchanged; a new code-health test fails on in-place writes into cached arrays.


## [2.104.5] - 2026-10-02

### Fixed

- Give households with an unknown region the UK-wide private rent index when uprating rent, so datasets containing `Region.UNKNOWN` (such as Survey of Personal Incomes records with an address abroad) can be simulated instead of raising `ParameterNotFoundError`.


## [2.104.4] - 2026-10-02

### Fixed

- - `Simulation(reform=...)` and `Microsimulation(reform=...)` accept structural `Reform` classes again, including classes built by `Reform.from_dict` and `set_parameter`, and tuples of reforms applied in order. Every one of these raised `TypeError` since the `Scenario` refactor, because `Scenario.from_reform` instantiated the class without the baseline system that policyengine-core's `Reform.__init__` requires. A reform class is now applied to the simulation's own tax-benefit system the way `Simulation.apply_reform` applies it. A `Reform` instance is rejected with a clear error, since its own state would be lost. Dict reforms are unchanged.


## [2.104.3] - 2026-10-02

### Fixed

- - Count contributory JSA once in `household_benefits`. `HOUSEHOLD_BENEFIT_VARIABLES` listed `jsa_contrib` twice, which overstated household benefits, net income and gross income by each household's contributory JSA. Also remove a duplicate `pension_credit` from the means-tested cost-of-living qualifying benefits (no output change), and test that no list of variable names repeats an entry.


## [2.104.2] - 2026-10-01

### Fixed

- Disregard the whole income and capital of Pension Credit guarantee credit recipients in the England pensioner, Wales and Scotland council tax reduction schemes, so they get the maximum reduction less non-dependant deductions whatever their income or savings (SI 2012/2885 Sch 1 para 13; WSI 2013/3029 Sch 1 para 7; SSI 2012/319 reg 24). For savings-credit-only recipients, use the Pension Credit assessment of income plus the savings credit paid, and of capital (para 14; para 8; reg 25). Their reduction can fall, because the savings credit counts as income and the capital limit applies to all the capital Pension Credit counts, not only savings.


## [2.104.1] - 2026-10-01

### Fixed

- Count contributory Employment and Support Allowance, Maternity Allowance, industrial injuries benefit and (from 19 November 2023) Scottish Carer Support Payment as Universal Credit unearned income, as UC Regs 2013 reg. 66(1)(b)(ii), (viii), (ix) and (iiia) require. Carer Support Payment counts only its carer support payment component (not the Scottish Carer Supplement) and only up to a year of Carer's Allowance.


## [2.104.0] - 2026-10-01

### Added

- - Added a capital gains realisation elasticity for gains qualifying for Business Asset Disposal Relief: while `gov.simulation.capital_gains_responses.separate_badr_elasticity` is on, those gains respond with `badr_elasticity` (1.4, the OBR's assumption for BADR gains) and the person's other gains with the main elasticity, both to the same share-weighted rate change. The switch is off by default, so existing results don't move.

### Fixed

- - Fixed marginal tax rates losing precision at large values: `marginal_tax_rate_on_capital_gains`, `marginal_tax_rate`, `marginal_tax_rate_wrt_employer_cost` and the labour supply derivative now add £1,000 or 0.1% of the value, whichever is larger, and divide by the step as stored in float32. A fixed £1,000 step had read the 24% main rate of capital gains tax as 24.8% at £185m of gains and 23.2% at £561m, and anywhere from -2.4% to 48.8% above £1bn, which fed straight into the capital gains realisation response. Below £1m the step is still £1,000, so readings there move only where float32 rounds the £1,000 step, and then by less than 0.01 percentage points.


## [2.103.0] - 2026-10-01

### Added

- - Added the Lifetime ISA holdings that microcosm datasets carry (`lifetime_isa_balance`, `has_lifetime_isa`, `household_lifetime_isa_balance`) and the Lifetime ISA withdrawal-charge parameters. Universal Credit, Housing Benefit, Income Support, income-based JSA, income-related ESA and Pension Credit now count a Lifetime ISA at its surrender value (75% of the balance under 60, the whole balance from 60) as capital of the holder's own benefit unit when the holder is its claimant or partner, and not before the Lifetime ISA existed (6 April 2017). Datasets without the columns are unaffected.


## [2.102.6] - 2026-09-30

### Fixed

- Charge secondary (employer) Class 1 National Insurance on employees over state pension age. SSCBA 1992 s.6(3) ends only primary (employee) contributions at pensionable age.


## [2.102.5] - 2026-09-30

### Fixed

- Let families in which every adult is over State Pension age make new Housing Benefit claims, as SI 2014/1230 reg 6A(4) allows. They no longer need a reported claim, and `would_claim_uc` no longer blocks them because Universal Credit is not available to them. Household calculations previously paid pension-age renters no Housing Benefit, and pension-age families in the Enhanced FRS who report Housing Benefit lost it whenever they drew `would_claim_uc`. Working-age and mixed-age families keep the existing continuing-award rule.


## [2.102.4] - 2026-09-30

### Changed

- - Require policyengine-core 3.32.9 or later, which sends `HUGGING_FACE_TOKEN` to public but gated Hugging Face repos such as policyengine-uk-data-private, and stop exporting `HF_TOKEN` in CI, the workaround that release makes unnecessary.


## [2.102.3] - 2026-09-28

### Changed

- - Rebase the absolute poverty line to HBAI's FYE 2025 reference year from FYE 2022 onward, as DWP has reported it since March 2026: 431.69 BHC / 373.89 AHC a week at FYE 2025. On the enhanced FRS in 2026-27, absolute poverty rises by about 4 points overall and about 7 points for children after housing costs.


## [2.102.2] - 2026-09-27

### Fixed

- - Fixed Class 4 National Insurance deducting employee Class 1 contributions from trading profits; Class 4 is now charged on the full profits, as SSCBA 1992 Schedule 2 requires, with the regulation 100 annual maximum still limiting combined liability.


## [2.102.1] - 2026-09-27

### Fixed

- - Fixed Class 4 National Insurance dropping the additional-rate band above the Upper Profits Limit when uprated thresholds are not round numbers. The regulation 100 annual maximum no longer leaves its Case 1 choice to float32 rounding. It applies only when primary Class 1 contributions (or, before 6 April 2024, Class 2 contributions) are also payable, and it ignores Class 2 from 6 April 2024 as SI 2024/377 requires. It also no longer returns NaN when a reform sets the main Class 4 rate to zero.


## [2.102.0] - 2026-09-25

### Added

- - Added household alcohol duty with strength bands, draught relief, and fiscal-year weighting.
- - Added household tobacco duty with cigarette minimum duty and fiscal-year weighting.
- - Added car vehicle excise duty using registration dates, emissions, fuel type, engine size and list price.
- - Added LPG and natural road fuel gas to fuel duty, including the 2026-27 staged increases.
  - Documented the gas-rate projection limits and different year bases in aggregate tax results.


## [2.101.0] - 2026-09-25

### Added

- Added `net_wealth` (total wealth net of mortgage, consumer, and student loan debt) and the `mortgage_debt` and `consumer_debt` household inputs. Unlike gross `total_wealth`, net wealth can be negative when a household's debts exceed its assets.


## [2.100.1] - 2026-09-23

### Fixed

- Stop projecting `domestic_energy_consumption`, `electricity_consumption` and `gas_consumption`. The data build calibrates them to NEED mean kWh at Ofgem Q2 2026 unit rates, so the stored values already carry FY26/27 price levels and projecting from the data year re-applied price changes that were already included. This reverses the direction of the fix in #1860, which resolved the #1859 inconsistency by uprating electricity and gas to match the aggregate rather than by removing all three. Modelled energy spending in projected years falls by about 8%.


## [2.100.0] - 2026-09-22

### Added

- - Add the six April 2023 unitary authorities (Cumberland, North Northamptonshire, North Yorkshire, Somerset, West Northamptonshire, Westmorland and Furness) to the `LocalAuthority` enum, so a dataset on the April 2023 local authority roster can supply `local_authority` for every household.


## [2.99.2] - 2026-09-21

### Fixed

- - Fixed `in_relative_poverty_bhc` and `in_relative_poverty_ahc` to take the 60% line from the median over individuals (household weight times household size), as DWP's HBAI series does, instead of the median over households. This is a definition change, not a data change, and it moves measured relative poverty: on the enhanced FRS 2024/25 (version 1.57.3) the BHC flag goes from 18.3% to 19.7% of individuals at 2024 and from 17.4% to 19.3% at 2026, the AHC flag from 22.3% to 23.7% and from 21.0% to 23.3%. Also corrected the BHC flag's label, added `poverty_threshold_ahc` as the AHC twin of `poverty_threshold_bhc` and documented the absolute-versus-relative pair on each flag; the absolute flags are unchanged.


## [2.99.1] - 2026-09-18

No significant changes.


## [2.99.0] - 2026-09-18

### Added

- - Add three person-level inputs, `capital_gains_badr`, `capital_gains_residential_property` and `capital_gains_carried_interest`, as components of `capital_gains`, and charge each at its own schedule in `capital_gains_tax`: new parameters `gov.hmrc.cgt.badr.rate` and `.lifetime_limit`, `gov.hmrc.cgt.residential_property.{basic,higher,additional}_rate` and `gov.hmrc.cgt.carried_interest.{basic,higher,additional}_rate`. The annual exempt amount goes to the highest-rate schedule first, relief gains take the unused basic rate band before other gains (TCGA 1992 s. 1I(4)-(6)), and the remaining band goes where it saves most. With the inputs absent or zero the liability is unchanged. A reform that changes only `gov.hmrc.cgt.{basic,higher,additional}_rate` no longer reaches residential property, carried interest or relief gains; to tax every gain at income tax rates, set the `residential_property` and `carried_interest` rates too and set `gov.hmrc.cgt.badr.lifetime_limit` to zero.

### Fixed

- - Open dataset H5 files read-only when loading. huggingface_hub 1.32.0 stores cached downloads as read-only blobs, and the default append mode refused them, so every dataset-backed simulation failed with a PermissionError.


## [2.98.0] - 2026-09-16

### Added

- - Add `would_claim_carers_allowance` (person) and `would_claim_uc_childcare` (benefit unit) take-up inputs, both defaulting to true, and recognise 35 or more weekly care hours in `is_carer_for_benefits` so a dataset can qualify carers for the Universal Credit carer element and the legacy carer premiums from reported hours without paying Carer's Allowance to every carer.


## [2.97.2] - 2026-09-10

### Fixed

- - Removed the Scottish Child Payment baby bonus from the baseline. The £40/week rate for under-1s was announced in the Scottish Budget 2026-27 but is not in legislation (SSI 2026/170 reg 8 sets a single flat rate with no under-1 tier), so from 2027 an eligible under-1 in Scotland was scored £2,080.00 against the statutory £1,500.20, overstating household net income by £579.80. It is now off in the baseline and only applies when a reform sets `gov.contrib.scotland.scottish_child_payment.in_effect`.


## [2.97.1] - 2026-09-10

### Fixed

- - Fixed the lagged CPI and lagged average earnings series ending at a hardcoded 2029, which froze lagged average earnings at its 2028 growth rate and left the index around 14% low by 2039.


## [2.97.0] - 2026-09-08

### Added

- - Added the is_uc_claimant input to identify Universal Credit claimants and partners from recorded benefit-unit relationships.

### Fixed

- - Fixed Universal Credit claimant classification and work allowances for families with qualifying young people, and excluded claimants from their own ordinary and disability child elements and two-child-limit counts.


## [2.96.1] - 2026-09-07

### Changed

- - Updated the private rent index to the ONS Price Index of Private Rents, which runs to July 2026 and raises Local Housing Allowance rates from 2024.


## [2.96.0] - 2026-09-06

### Added

- - Added the national maximum Local Housing Allowance, which caps the Broad Rental Market Area percentile and binds in central London.

### Fixed

- - Fixed frozen LHA rates being re-based to the first year of the freeze rather than held at the level last determined, and read the percentile and national maximum at that determination year so a later change cannot move a frozen rate.
- - Fixed the Universal Credit housing costs element using the weekly Housing Benefit maximum LHA annualised by 52, rather than the statutory monthly maximum.


## [2.95.0] - 2026-09-01

### Removed

- - Removed the obsolete UK release action that silently attempted to run deleted downstream dependency-update scripts.


## [2.94.0] - 2026-08-30

### Changed

- - Added shared AI contributor instructions that route tool-specific guidance into common engineering documentation.

### Removed

- - Removed Python 3.9 and 3.10 support; supported versions are now Python 3.11–3.14.


## [2.93.1] - 2026-08-28

### Fixed

- Place earnings quintiles against thresholds taken from the observed earnings distribution of working adults, rather than ranking the whole population on actual earnings. Ranking everyone, children included, left the bottom two quintiles entirely without earners, placed every potential labour-market entrant at the steep end of the OBR Table A1 elasticities, and left those quintiles with no employed donors — so `impute_wages_for_nonworkers` returned a wage of zero for them, which silently bars entry into employment. Wage donors are now grouped by sex and age band, which also breaks the circular dependency between the two functions.

  Non-workers are placed on the quintile table at full-time-equivalent income. This is an assumption beyond the cited sources, and it is material: unscaled 18.8-hour placement moves entrants to quintile 1 and roughly doubles the elasticity they draw. Documented in the module with the bound and how to reproduce it.


## [2.93.0] - 2026-08-28

### Added

- - Add `tax_free_childcare_spend_routed_share`, a per-child input for the share of childcare spending paid through a Tax-Free Childcare account. Only routed spending attracts the top-up, and `childcare_expenses` is annual. The share is measured across the eligible period, not the whole year, because `tax_free_childcare` already prorates annual spending by the eligible fraction and a whole-year share would discount the same months twice. Defaults to 1 — a neutral all-spend-routed assumption rather than a statutory requirement — and is clipped to 0-1, so no household calculation changes. The dataset build may supply an HMRC-derived account-activity duration proxy rather than an observed routed-expenditure share; see policyengine-uk-data.


## [2.92.2] - 2026-08-28

### Fixed

- - Apply the Tax-Free Childcare rate to the total paid to the provider rather than grossing it up as if it were the parent's deposit. The parameter is 20% of household and government contributions combined, and its reference is the section of the Childcare Payments Act that defines the gross-side rate, so dividing by `(1 - rate)` applied deposit-side arithmetic to a gross-side rate. Modelled spending on the Enhanced FRS falls 14.5%, less than the 20% the rate change implies, because the per-child cap binds for many recipients. Also pro-rate the top-up by the share of the year a family is eligible rather than only its cap, which changes nothing on a built dataset today because `tax_free_childcare_eligible_declaration_periods` is binary by construction.


## [2.92.1] - 2026-08-28

No significant changes.


## [2.92.0] - 2026-08-26

### Added

- Added `private_pension_wealth` (Household, imputed from the Wealth and Assets Survey) as an explicit capital disregard: it is not a capital source in any means test, `corporate_wealth` no longer describes private pensions, `total_wealth` includes it, and a new `corporate_sector_wealth` (corporate plus private pension wealth) is the allocation key for shareholding, corporate land value and the employer NI capital response so those keys do not move when the data splits pension wealth out of corporate wealth (policyengine-uk-data#452).


## [2.91.0] - 2026-08-17

### Added

- - Added an auxiliary capital gains realisation elasticity with respect to the marginal tax rate, alongside the existing retention-rate elasticity.


## [2.90.3] - 2026-08-14

### Changed

- UC deductions documentation: promote the aggregate caveat - reform aggregates (poverty counts, floor-reform costs) run roughly 40% low because the model's UC caseload falls short of administrative counts (policyengine-uk-data#452 tracks the calibration fix; #450 tracks moving deduction imputation to the dataset build); per-household statistics are the validated, quotable layer. Also note the rate distribution is national (regional factors scale incidence only, so regional composition differences are not modeled) and that annual per-household amounts are upper bounds for spell-limited deduction types.


## [2.90.2] - 2026-08-13

No significant changes.


## [2.90.1] - 2026-08-12

No significant changes.


## [2.90.0] - 2026-08-12

### Added

- Universal Credit deductions: latent deduction demand assigned from DWP deductions statistics (incidence by region, rate distribution, type combinations), the deductions cap including the 2025 Fair Repayment Rate, last resort deductions exempt from the cap, reform switches to abolish advance, third party or government debt deductions, and a protected minimum floor lever limiting combined deductions and benefit cap reductions (JRF-style floor reforms). Per-household statistics are validated against the DWP deductions statistics; weighted aggregates (deducting households, total deducted, the cost of floor reforms) run low in proportion to the model's UC caseload shortfall (policyengine-uk-data#452) and should not be quoted without that caveat - see the deductions validation page in the documentation for the limitations that bound reform estimates.


## [2.89.4] - 2026-07-27

### Fixed

- Lower Northern Ireland's regional land intensity from 0.673 to 0.44, interpolating from price-similar regions consistently with Scotland and Wales.


## [2.89.3] - 2026-07-23

No significant changes.


## [2.89.2] - 2026-06-18

No significant changes.


## [2.89.1] - 2026-06-17

No significant changes.


## [2.89.0] - 2026-06-11

### Added

- - Added direct `gs://` dataset loading for UK simulations, including support for GCS generations and PolicyEngine data-version metadata.


## [2.88.65] - 2026-06-07

No significant changes.


## [2.88.64] - 2026-06-07

No significant changes.


## [2.88.63] - 2026-06-07

No significant changes.


## [2.88.62] - 2026-06-07

No significant changes.


## [2.88.61] - 2026-06-07

No significant changes.


## [2.88.60] - 2026-06-07

No significant changes.


## [2.88.59] - 2026-06-06

No significant changes.


## [2.88.58] - 2026-06-06

No significant changes.


## [2.88.57] - 2026-06-06

No significant changes.


## [2.88.56] - 2026-06-06

No significant changes.


## [2.88.55] - 2026-06-06

No significant changes.


## [2.88.54] - 2026-06-06

No significant changes.


## [2.88.53] - 2026-06-05

### Fixed

- - Fixed Carer Support Payment and Scottish Carer Supplement 2026 parameter dates.


## [2.88.52] - 2026-06-05

No significant changes.


## [2.88.51] - 2026-06-05

No significant changes.


## [2.88.50] - 2026-06-05

No significant changes.


## [2.88.49] - 2026-06-05

No significant changes.


## [2.88.48] - 2026-06-05

No significant changes.


## [2.88.47] - 2026-06-05

No significant changes.


## [2.88.46] - 2026-06-05

No significant changes.


## [2.88.45] - 2026-06-05

No significant changes.


## [2.88.44] - 2026-06-05

No significant changes.


## [2.88.43] - 2026-06-04

No significant changes.


## [2.88.42] - 2026-06-04

No significant changes.


## [2.88.41] - 2026-06-04

### Fixed

- Fix property_purchased default from True to False so households are not charged stamp duty on their entire property wealth unless they explicitly purchased this year. The True default charged every household in population datasets full SDLT/LBTT/LTT on its home value, inflating the first income decile's effective tax rate to 251% and breaking the data pipeline.


## [2.88.40] - 2026-06-02

No significant changes.


## [2.88.39] - 2026-06-01

No significant changes.


## [2.88.38] - 2026-06-01

No significant changes.


## [2.88.37] - 2026-06-01

No significant changes.


## [2.88.36] - 2026-06-01

No significant changes.


## [2.88.35] - 2026-06-01

No significant changes.


## [2.88.34] - 2026-06-01

No significant changes.


## [2.88.33] - 2026-06-01

No significant changes.


## [2.88.32] - 2026-06-01

No significant changes.


## [2.88.31] - 2026-06-01

No significant changes.


## [2.88.30] - 2026-06-01

No significant changes.


## [2.88.29] - 2026-06-01

No significant changes.


## [2.88.28] - 2026-06-01

No significant changes.


## [2.88.27] - 2026-06-01

No significant changes.


## [2.88.26] - 2026-06-01

No significant changes.


## [2.88.25] - 2026-06-01

No significant changes.


## [2.88.24] - 2026-06-01

No significant changes.


## [2.88.23] - 2026-05-23

No significant changes.


## [2.88.22] - 2026-05-23

No significant changes.


## [2.88.21] - 2026-05-23

No significant changes.


## [2.88.20] - 2026-05-20

No significant changes.


## [2.88.19] - 2026-05-20

No significant changes.


## [2.88.18] - 2026-05-17

### Changed

- Remove redundant uprating metadata and class-level aggregation metadata from variables that already define their computation explicitly.


## [2.88.17] - 2026-05-17

### Changed

- Make the CPS expanded Marriage Allowance reform use the explicit `would_claim_marriage_allowance` input instead of formula-time randomness.


## [2.88.16] - 2026-05-15

No significant changes.


## [2.88.15] - 2026-05-11

### Fixed

- - Include `council_tax_benefit` in `household_benefits`, `gov_spending`, `hbai_household_net_income`, and `pre_budget_change_household_benefits`. Previously CTR was absent from these aggregates, so abolishing council tax via `gov.contrib.abolish_council_tax` refunded the gross billed amount to households (and removed gross revenue from the government balance) rather than the net out-of-pocket amount, overstating household savings by about £4 billion in aggregate.


## [2.88.14] - 2026-05-09

No significant changes.


## [2.88.13] - 2026-05-05

### Changed

- Added runtime metadata with installed policyengine-core identity for bundle validation.


## [2.88.12] - 2026-05-02

No significant changes.


## [2.88.11] - 2026-05-01

No significant changes.


## [2.88.10] - 2026-04-29

No significant changes.


## [2.88.9] - 2026-04-20

No significant changes.


## [2.88.8] - 2026-04-20

### Fixed

- - Fix `gov.dwp.tax_credits.min_benefit` parameter unit from `currency-USD` to `currency-GBP` — the parameter is a UK statutory threshold in pounds.
  - Correct `benunit_weekly_hours` label from "Average weekly hours worked by adults in the benefit unit" to "Total weekly hours worked by adults in the benefit unit" — the formula is `adds = ["weekly_hours"]`, which sums rather than averages.


## [2.88.7] - 2026-04-20

No significant changes.


## [2.88.6] - 2026-04-19

### Fixed

- Replace `new_state_pension`'s flat-max payout with a `min(reported, max) / max * period_max` formula mirroring `basic_state_pension`, and extend `additional_state_pension` to NEW-type retirees so any pre-2016 SERPS/S2P Protected Payment flows through as an add-on instead of being silently dropped. Partial-NI-record retirees now receive their actual pro-rated rate rather than the full flat max. Closes part of the ~£12 bn residual state-pension gap vs the OBR target tracked in #1632.


## [2.88.5] - 2026-04-18

### Fixed

- Zero out Income Support and income-based Jobseeker's Allowance after DWP managed migration completed on 31 March 2026. New parameters `gov.dwp.income_support.active` and `gov.dwp.JSA.income.active` flip to `false` from 2026-04-01, matching the Tax Credits treatment. Contribution-based JSA remains active.


## [2.88.4] - 2026-04-18

### Fixed

- Bump `policyengine-core` minimum to `>=3.25.0` to pick up the cache-invalidation and `set_input` preservation fixes (PolicyEngine/policyengine-core#475). The 3.24.0–3.24.3 cascade left UK model tests returning zero for income_tax, UC, and other formula-driven variables when a reform is applied during simulation construction; 3.25.0 includes the regression fix.


## [2.88.3] - 2026-04-17

### Fixed

- Migrate versioning workflow to GitHub App token (POLICYENGINE_GITHUB PAT expired).


## [2.88.2] - 2026-04-17

No significant changes.


## [2.88.1] - 2026-04-17

### Changed

- - Update `.github/CONTRIBUTING.md` to document the towncrier `changelog.d/` workflow. The old `changelog_entry.yaml` + `make changelog` flow was deprecated some time ago; the CONTRIBUTING guide still instructed new contributors to use it, causing CI round-trips on PRs that created a `changelog_entry.yaml` no fragment step was looking for.


## [2.88.0] - 2026-04-17

### Added

- Support Python 3.9 and 3.10 (in addition to 3.11–3.14). On Python 3.9/3.10, pip resolves `policyengine-core` to a version that has been relaxed to support older Python (3.24.0+); on 3.11+ behavior is unchanged.


## [2.87.1] - 2026-04-17

### Fixed

- - Fix `state_pension_type` incorrectly classifying every pensioner as receiving the pre-2016 basic State Pension. The formula used `values_list[0]` to find when the New State Pension activated, but policyengine-core auto-extrapolates the parameter into the far future, so `[0]` was returning a 2040s entry instead of the 2016 activation date. Walks the list oldest-first to find the real activation instant, so post-2016 retirees are now correctly classified as `NEW`. Raises the modelled 2025 state pension aggregate from about £116bn to about £127bn.
- - Fix Working Tax Credit and Child Tax Credit continuing to pay out from the 2025-26 tax year onward. Working Tax Credit and Child Tax Credit ended on 5 April 2025 (HMRC/DWP). Adds a `gov.dwp.tax_credits.active` parameter that flips to `false` on 2025-04-06 and gates `tax_credits` on it. Removes about £1.9bn of phantom Tax Credit spending per year from 2025-26 onward while preserving the legitimate 2024-25 baseline.


## [2.87.0] - 2026-04-17

### Added

- - Add a microsimulation smoke test suite that runs against the unpinned latest enhanced FRS dataset and asserts plausibility bounds for UK population, UC aggregate, `is_parent` population, core benefit totals, and extended childcare eligibility. Catches silent model/data skew at the point the dataset is republished, not after a release.


## [2.86.13] - 2026-04-17

No significant changes.


## [2.86.12] - 2026-04-15

No significant changes.


## [2.86.11] - 2026-04-15

No significant changes.


## [2.86.10] - 2026-04-15

No significant changes.


## [2.86.9] - 2026-04-15

No significant changes.


## [2.86.8] - 2026-04-15

No significant changes.


## [2.86.7] - 2026-04-15

No significant changes.


## [2.86.6] - 2026-04-15

No significant changes.


## [2.86.5] - 2026-04-15

No significant changes.


## [2.86.4] - 2026-04-15

No significant changes.


## [2.86.3] - 2026-04-15

No significant changes.


## [2.86.2] - 2026-04-15

No significant changes.


## [2.86.1] - 2026-04-15

No significant changes.


## [2.86.0] - 2026-04-15

### Added

- Add a first-pass Disabled Students' Allowance model for England higher-education students.


## [2.85.0] - 2026-04-15

### Added

- Add a first-pass Travel Grant model.


## [2.84.0] - 2026-04-15

### Added

- Add a first-pass Adult Dependants' Grant model.
- Add a first-pass Parents' Learning Allowance model.


## [2.83.0] - 2026-04-14

### Added

- Add a first-pass 16 to 19 Bursary Fund model for vulnerable groups.


## [2.82.0] - 2026-04-14

### Added

- - Add a first-pass Childcare Grant model for England full-time undergraduates.


## [2.81.0] - 2026-04-14

### Added

- - Add an approximate England full-time maintenance loan model, with explicit override inputs for living arrangement and assessed household income.

### Fixed

- Fix maintenance loan proxy logic to require explicit higher-education evidence and improve sponsor-income assessment.


## [2.80.0] - 2026-04-13

### Added

- - Add an approximate England full-time maintenance loan model, with explicit override inputs for living arrangement and assessed household income.


## [2.79.3] - 2026-04-13

### Fixed

- Use modelled student loan repayments in aggregates and cap them by outstanding balance when available.


## [2.79.2] - 2026-04-12

### Fixed

- Fixed `corporate_land_value` to allocate aggregate corporate land using the current weighted distribution of `corporate_wealth`, and refreshed the aggregate land parameters to the 2024 ONS land totals used by `policyengine-uk-data`.


## [2.79.1] - 2026-04-12

### Changed

- Expose build metadata helpers for UK data artifacts, including a stable data-build fingerprint and build provenance metadata.


## [2.79.0] - 2026-04-12

### Added

- Add named economic-assumption parameters for the local-authority ONS income target uprating factors used by `policyengine-uk-data`.

### Fixed

- Corrected Universal Credit rebalancing so existing health-element claimants keep their combined standard allowance and health element award CPI-protected.


## [2.78.0] - 2026-04-07

### Added

- Added the England-only High Value Council Tax Surcharge from April 2028, including its 2026-price valuation bands and CPI uprating from 2029-30 onward.


## [2.77.5] - 2026-04-07

### Fixed

- Prevent labor supply response formulas and progression dynamics from
  flipping sign when baseline employment income is negative.


## [2.77.4] - 2026-04-07

### Fixed

- Add regression coverage to keep income decile outputs in `-1` or `1..10`.


## [2.77.3] - 2026-04-07

### Fixed

- Fixed `gov.contrib.cec.state_pension_increase` so state pension reforms affect microsimulation outputs and budget impacts.


## [2.77.2] - 2026-04-07

### Fixed

- Documented how to request access to restricted UK datasets before setting `HUGGING_FACE_TOKEN`.


## [2.77.1] - 2026-04-07

### Fixed

- Tax-Free Childcare now requires childcare expenses to be paid to a qualifying provider when that input is supplied.


## [2.77.0] - 2026-04-07

### Added

- Added an `abolish_benefit_cap` scenario for benefit-cap removal analysis.


## [2.76.0] - 2026-04-07

### Added

- Added an OBR detailed forecast table importer script for updating economic forecast values in `yoy_growth.yaml`.


## [2.75.4] - 2026-04-05

### Fixed

- - Ensure `uprate_rent` passes a NumPy array into vectorial parameter lookup for regional private rent growth.


## [2.75.3] - 2026-03-26

### Changed

- Replace flat national land intensity ratio (0.673) with region-specific ratios from MHCLG 2023 land value estimates, so household_land_value reflects the much higher land share in London (0.85) vs the North East (0.42).


## [2.75.2] - 2026-03-17

### Changed

- Replaced personal PAT with `GITHUB_TOKEN` in versioning workflow. Publish now runs as a sequential job instead of requiring a re-triggered workflow, removing the dependency on a personal access token for same-repo operations.

### Fixed

- Fixed `hbai_household_net_income` to respect `abolish_council_tax` parameter and include LVT in subtracts, so that poverty statistics correctly respond to council tax abolition and land value tax reforms.
- Fixed invalid `secrets` reference in versioning workflow step condition that prevented the workflow from running.


## [2.75.1] - 2026-03-10

### Changed

- Added `copy` parameter to `apply_uprating` (default `True`); `extend_single_year_dataset` now passes `copy=False` to skip the redundant deep copy of the multi-year dataset since each year is already copied individually.


## [2.75.0] - 2026-03-08

### Added

- Add separate `electricity_consumption` and `gas_consumption` input variables, surfacing the NEED 2023-calibrated imputations from policyengine-uk-data 1.41.0.
- Added ruff check linting configuration with E and F rules to catch common Python errors.

### Changed

- Replace modelled_policies.yaml with structured programs.yaml containing rich metadata for all 37 modelled programs.
- Migrated from changelog_entry.yaml to towncrier fragments to eliminate merge conflicts.
- Switch from black to ruff format.
- Update OBR economic forecasts to March 2026 EFO.
- Update remaining OBR economic forecasts to March 2026 EFO detailed tables (CPIH, rent, mortgage interest, council tax, non-labour income, mixed income, household interest income, CPI AHC).
- Add Python 3.14 classifier and remove upper bound on requires-python.

### Fixed

- Fix verified_years in programs.yaml based on parameter and test audit.


# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.74.0] - 2026-02-23 13:44:25

### Fixed

- Include employer pension contributions and salary sacrifice in the Annual Allowance tax charge calculation, per Finance Act 2004 s.233.

## [2.73.2] - 2026-02-23 13:07:05

### Fixed

- Enum columns now decode to string labels when accessing .person/.benunit/.household on datasets loaded via non-URL paths (e.g. UKSingleYearDataset or UKMultiYearDataset passed directly)

## [2.73.1] - 2026-02-19 17:57:15

### Fixed

- Skip student loan uprating if column doesn't exist yet during dataset creation.

## [2.73.0] - 2026-02-19 17:30:26

### Added

- {'Student loan plan uprating in economic assumptions': 're-labels Plan 1/2/5 each year based on cohort start year, writes off loans after 29 years, and samples new Plan 5 entrants for England using empirical age/income take-up probabilities.'}

## [2.72.4] - 2026-02-18 10:18:43

### Changed

- Vectorised BRMA LHA rate lookup for ~3s speedup on calculate calls.

## [2.72.3] - 2026-01-25 14:13:02

### Changed

- Bumped policyengine-core minimum version to 3.23.5 for pandas 3.0 compatibility

## [2.72.2] - 2026-01-21 11:55:12

### Fixed

- Scottish top rate (48%) threshold corrected from 125,140 to 112,570 (above personal allowance). The threshold was incorrectly stored as the total income value instead of the amount above PA, causing the top rate to effectively start at 137,710 instead of 125,140.

## [2.72.1] - 2026-01-20 12:44:50

### Fixed

- Add 2026-27 Scottish income tax threshold freeze to baseline (higher, advanced, and top rates) per Scottish Budget 2025-26.

## [2.72.0] - 2026-01-20 12:32:14

### Added

- Scottish Child Payment rates from 2026-27 to 2030-31 per Scottish Fiscal Commission forecasts.
- Scottish Child Payment baby boost under-1 total from 2027-28 to 2030-31 per SFC forecasts.
- CPI uprating for SCP parameters for projections beyond 2030-31.

## [2.71.1] - 2026-01-17 18:54:27

### Fixed

- Reverted premature SCP 2026-27 rate increase (not yet law).
- Refactored SCP baby bonus reform to use £40/week total as the policy parameter instead of a fixed bonus amount.

## [2.71.0] - 2026-01-17 18:39:20

### Added

- Scottish Child Payment increased to 28.20/week for 2026-27, per Scottish Budget 2026-27.

## [2.70.7] - 2026-01-17 18:37:47

### Fixed

- Skip behavioral response tests when HUGGING_FACE_TOKEN is not available (enables Dependabot PRs to pass CI).

## [2.70.6] - 2026-01-17 18:33:41

### Fixed

- Fixed Scottish Child Payment baby bonus reform to use Person-level variable structure, matching the refactored base variable. The reform now correctly uses parameterized baby bonus rates instead of hardcoded values.
- Fixed SCP baby bonus effective date to 2027-04-01 (fiscal year 2027-28) per Scottish Budget 2026-27.

## [2.70.5] - 2026-01-17 18:05:46

### Fixed

- CI workflows now handle missing HUGGING_FACE_TOKEN gracefully, allowing Dependabot PRs to run tests without failing on empty Bearer token errors.

## [2.70.4] - 2026-01-17 17:45:51

### Changed

- Standardized all parameter labels to use sentence case, while preserving proper names (e.g., "Bank of England", "Child Benefit") and acronyms (e.g., "HMRC", "VAT", "NHS")

## [2.70.3] - 2026-01-17 17:42:23

### Fixed

- Extended childcare entitlement hours expansion date corrected from 2026-01-01 to 2025-09-01 for children aged 9 months to 2 years, implementing the September 2025 policy change that doubled free childcare from 15 to 30 hours per week for working parents.

## [2.70.2] - 2026-01-17 17:37:48

### Added

- Per-value legislative references for income tax allowances and minimum wage rates

## [2.70.1] - 2026-01-17 17:17:54

### Fixed

- CI now runs on dependency updates (pyproject.toml, uv.lock changes)
- Fixed Scottish Child Payment test format to use array notation for person-level output

## [2.70.0] - 2026-01-17 04:45:58

### Changed

- Remove randomness from country package by moving stochastic variable generation to data package. Variables now read pre-computed values from datasets for deterministic, reproducible calculations.

## [2.69.0] - 2026-01-15 15:17:19

### Added

- Scottish Child Payment baby bonus reform.

## [2.68.1] - 2026-01-13 17:13:11

### Fixed

- Dataset uprating bug where region values weren't converted to strings for rent indexing
- Salary sacrifice default behavior to be static (0) instead of fully optimized (1.0)

## [2.68.0] - 2026-01-13 15:46:23

### Added

- 2025-26 Scottish income tax rates.

## [2.67.0] - 2026-01-13 14:23:42

### Added

- Scottish Child Payment - a benefit provided by Social Security Scotland for eligible children under 16 in low-income families receiving qualifying benefits (UC, tax credits, etc.).

## [2.66.0] - 2026-01-12 16:12:34

### Fixed

- LHA freeze parameter.

## [2.65.9] - 2025-12-09 16:16:37

### Fixed

- Refactor variables with redundant adds/subtracts and formula definitions to prevent sync issues

## [2.65.8] - 2025-12-09 10:09:16

### Added

- Legislative references for marriage allowance take-up rate (Income Tax Act 2007 s. 55B)
- Legislative references for married couple's allowance deduction rate (Income Tax Act 2007 s. 46)
- Legislative references for income tax additions and subtractions (Income Tax Act 2007 s. 23)
- Labels for 11 HMRC income tax parameters including annual allowance, personal savings allowance, and savings starter rate parameters

### Changed

- All HMRC income tax parameters now have proper labels and legislative references

## [2.65.7] - 2025-12-09 09:47:39

### Added

- Add savings, net_financial_wealth, gross_financial_wealth, and shareholding to total_wealth calculation

## [2.65.6] - 2025-12-09 08:44:22

### Fixed

- Fixed employer_ni_fixed_employer_cost_change variable returning impacts in baseline scenarios by correcting baseline parameter access.

## [2.65.5] - 2025-12-08 22:13:29

### Fixed

- Correct 2025-26 benefit cap rates (were incorrectly showing uprated values; benefit cap has been frozen since 2023)
- Update UC parameter legislation references to point to exact regulation sections on legislation.gov.uk
- Add missing 2025-26 Universal Credit non-dependent deduction amount (GBP 93.02)

## [2.65.4] - 2025-12-08 21:37:03

### Fixed

- Basic state pension calculation.

## [2.65.3] - 2025-12-08 10:54:42

### Added

- Salary sacrifice pension cap reform (GBP 2,000 cap from April 2029) with broad-base employer response modeling.

## [2.65.2] - 2025-12-05 16:29:26

### Fixed

- Fix fuel duty rates to use OBR November 2025 RPI forecasts.

## [2.65.1] - 2025-12-04 14:45:58

### Changed

- Bump policyengine-core to 3.23.0 (adds strict enum validation).

## [2.65.0] - 2025-12-03 16:17:09

### Fixed

- Extend fiscal year parameter conversion to cover 2015-2040, fixing issues where policies changing on April 6 (UK fiscal year start) were not reflected in simulations for years 2026+.

## [2.64.1] - 2025-12-03 12:45:46

### Fixed

- Print statement.

## [2.64.0] - 2025-12-03 11:59:49

### Added

- Two child limit repeal from April 2026 (Autumn Budget 2025) - sets UC and Tax Credits child element limit to infinity
- Salary sacrifice pension cap of �2,000 from April 2029 (Autumn Budget 2025)
- Move inflation adjustment AHC back to BHC inflation.

## [2.63.0] - 2025-12-02 16:24:40

### Added

- Added gift_aid_grossed_up variable that computes Gift Aid grossed up by basic rate per ITA 2007 s.58.
- Added comprehensive Gift Aid tests covering basic rate relief, higher rate relief, and PA taper interaction.

### Changed

- Added legislation references (legislation.gov.uk) to gift_aid and personal_allowance variables.

### Fixed

- Fixed Personal Allowance taper calculation to deduct grossed-up Gift Aid from ANI per ITA 2007 s.58. Previously, Gift Aid donations did not reduce ANI for PA taper purposes, causing high earners (GBP 100k-125k) to receive less tax relief than legally entitled.

## [2.62.1] - 2025-12-02 14:16:53

### Added

- Add upper interest threshold freeze for Plan 2 student loans (Budget 2025)

## [2.62.0] - 2025-12-02 09:19:36

### Added

- Add owns vehicle variable

## [2.61.4] - 2025-12-01 11:11:26

### Changed

- Vectorised BRMA LHA rate lookup for ~3s speedup on calculate calls.

## [2.61.3] - 2025-12-01 03:34:34

### Added

- Add 2026 Plan 2 student loan interest rate thresholds (lower £29,385, upper £52,885) and freeze lower threshold 2027-2029 per Budget 2025

## [2.61.2] - 2025-11-28 14:58:06

### Fixed

- Fix fuel duty rates to use calendar year averages instead of incorrectly selecting first rate of each year in reform calculations. Updates 2026-2029 rates to weighted averages (53.45p, 59.02p, 61.11p, 62.90p) with detailed documentation of actual source values and calculation methodology.

## [2.61.1] - 2025-11-28 13:48:04

### Fixed

- Update HH net income calculation.

## [2.61.0] - 2025-11-28 11:59:37

### Added

- Add student loan repayment modelling with parameters for Plan 1, 2, 4, 5 and postgraduate loans, including thresholds and repayment rates.

## [2.60.0] - 2025-11-27 16:24:25

### Added

- November 2025 Autumn Budget parameter updates. Extends income tax threshold freeze (personal allowance GBP 12,570, higher rate GBP 50,270, additional rate GBP 125,140) and NICs secondary threshold freeze (GBP 96/week) to April 2031. Updates fuel duty schedule with freeze until September 2026, staggered 5p cut reversal, and RPI uprating from April 2027.

## [2.59.0] - 2025-11-27 09:29:34

### Added

- Implement November 2025 Autumn Budget income source tax rate increases. Dividends +2pp basic/higher from April 2026, savings +2pp from April 2027, property +2pp from April 2027.

## [2.58.0] - 2025-11-26 19:23:28

### Changed

- Update economic projections to OBR November 2025 Economic and Fiscal Outlook forecasts (CPI, RPI, CPIH, average earnings, house prices, rents, mortgage interest)

## [2.57.1] - 2025-11-26 18:40:43

### Fixed

- Correct OBR March 2025 economic projections to match detailed forecast tables

## [2.57.0] - 2025-11-21 14:59:20

### Changed

- Salary sacrifice pension contributions above the cap are now redirected to employee pension contributions (which receive income tax relief but pay NI) instead of returning only to regular employment income. This better reflects the behavioral assumption that individuals prioritize retirement savings.

## [2.56.1] - 2025-11-20 14:51:58

### Changed

- Updated microsimulation test expected values to reflect salary sacrifice calculation improvements.

### Fixed

- Salary sacrifice returned to income now cannot be negative.
- Adjusted salary sacrifice pension contributions now cannot go below zero.

## [2.56.0] - 2025-11-20 12:24:29

### Added

- Salary sacrifice pension cap policy modeling (2,000 GBP cap on NI-exempt contributions)

## [2.55.3] - 2025-10-22 10:03:42

### Added

- Scenario now supports `applied_before_data_load` flag to control when parameter changes and simulation modifiers are applied relative to data loading.

## [2.55.2] - 2025-10-21 12:08:26

### Fixed

- Bug fix for decomp analysis.

## [2.55.1] - 2025-10-20 12:51:40

### Fixed

- Bug fix in state pension scripts.

## [2.55.0] - 2025-10-20 12:43:40

### Fixed

- Bug in state pension formulae causing issues when using datasets with year != 2023.

## [2.54.2] - 2025-10-17 15:01:31

### Fixed

- Fix bug where changes to economic assumption parameters would not change uprating behaviour.

## [2.54.1] - 2025-10-15 12:18:22

### Fixed

- Fixed randomness between runs caused by UC reform.

## [2.54.0] - 2025-09-30 14:40:31

### Added

- Dataset filter function to extract single households for analysis.

### Changed

- Default target variable for labour supply calculations to HBAI household net income.
- Default adult count for labour supply calculations to 2.

### Fixed

- Labour supply response calculation issues by removing inappropriate clipping of marginal rates.
- Potential bug in labour supply response variable initialization order.

## [2.53.1] - 2025-09-29 12:26:51

### Fixed

- Temporarily disabled OBR participation responses.

## [2.53.0] - 2025-09-25 09:22:41

### Fixed

- Bugs in the benefit cap exemption list.

## [2.52.1] - 2025-09-24 15:33:18

### Fixed

- Updated carbon emissions data to latest available figures

## [2.52.0] - 2025-09-24 12:24:39

### Fixed

- Bugs in the benefit cap exemption list.

## [2.51.0] - 2025-09-10 09:28:56

### Fixed

- Update reduced vat expenditure share from OBR

## [2.50.0] - 2025-09-03 09:15:47

### Fixed

- Add real_hbai_household_net_income_ahc variable for convenience.

## [2.49.5] - 2025-09-02 13:00:40

### Fixed

- Removed bug-causing high income tax change variable.

## [2.49.4] - 2025-09-01 13:02:52

### Fixed

- Fix behavioral response calculations returning zero FTE impacts due to simulation state corruption
- Fix NaN values in wage relative change calculations during labor supply responses
- Fix income effect calculations by properly handling household_net_income timing

## [2.49.3] - 2025-09-01 09:09:46

### Fixed

- Bug causing some households to claim both CTC and UC.

## [2.49.2] - 2025-08-29 13:54:13

### Fixed

- Fix bug in capital/consumer incidence.

## [2.49.1] - 2025-08-29 10:32:06

### Fixed

- Re-enabled employer NI dynamics.

## [2.49.0] - 2025-08-28 13:08:00

### Fixed

- Baseline simulation created before simulation modifier is applied.

## [2.48.0] - 2025-08-27 20:32:42

### Fixed

- Fuel duty is 52.95p per litre until 2026 where the temporary 5p cut is reversed, and then risen with RPI

## [2.47.4] - 2025-08-14 16:30:16

### Fixed

- Issue causing capital gains elasticities to not take effect.

## [2.47.3] - 2025-08-13 08:14:33

### Fixed

- Scenario class now supports all Reform object types and maintains backwards compatibility.

## [2.47.2] - 2025-08-12 14:17:09

### Fixed

- Moved `Scenario` in top-level import.

## [2.47.1] - 2025-08-12 09:48:46

### Fixed

- Bug in multi year datasets.

## [2.47.0] - 2025-08-12 09:29:55

### Fixed

- Dropped support for <3.13.

## [2.46.3] - 2025-08-09 09:01:58

### Fixed

- Minor bug in comparison function.

## [2.46.2] - 2025-08-08 15:09:27

### Changed

- Updated script to open automated API update PRs

## [2.46.1] - 2025-08-08 11:42:38

### Fixed

- Forecast window extended to 2030-31.

## [2.46.0] - 2025-08-08 11:34:55

### Changed

- Long-term OBR economic growfactors for 2030-10 and onwards.

## [2.45.5] - 2025-08-08 10:46:25

### Added

- Utility function for comparing simulations added to `policyengine_uk.utils.compare`.

## [2.45.4] - 2025-08-04 14:23:45

### Changed

- Dropped direct jupyter book dependency.

## [2.45.3] - 2025-08-04 12:54:43

### Fixed

- Moved rent uprating to warning from error if before 2022.

## [2.45.2] - 2025-08-01 09:00:11

### Fixed

- Bug in NI rates.

## [2.45.1] - 2025-07-31 13:39:16

### Fixed

- Bug caused by not resetting parameter caches.

## [2.45.0] - 2025-07-30 14:17:20

### Added

- Docs upgraded to jupyter book 2.
- Model baseline page added.
- Capital gains tax baseline updated.

## [2.44.1] - 2025-07-29 15:40:04

### Changed

- HBAI benefits included at top level.

## [2.44.0] - 2025-07-29 14:15:32

### Added

- UC rebalancing reforms.

## [2.43.5] - 2025-07-28 22:20:17

### Fixed

- Minor missing variable attributes.

## [2.43.4] - 2025-07-28 12:35:29

### Fixed

- WFP reforms active.
- Growthfactors extended to 2040.

## [2.43.3] - 2025-07-28 10:01:47

### Changed

- Separated out system.py to avoid bloat.

## [2.43.2] - 2025-07-26 20:54:03

### Added

- Add pydantic dependency to fix missing import in scenario utilities

## [2.43.1] - 2025-07-26 14:10:57

### Changed

- Add Python 3.13 support and update CI workflows
- Updated policyengine-core dependency to >=3.19.0 for Python 3.13 support
- Updated GitHub Actions to latest versions (checkout@v4, setup-python@v5) for Python 3.13 compatibility
- Set all workflows to use Python 3.13

## [2.43.0] - 2025-07-26 11:31:02

### Added

- Scenario class for reforms.
- Documentation of Scenario and Simulation.
- Standardisation of uprating behaviour.

## [2.42.0] - 2025-07-25 08:57:23

### Changed

- Add after housing costs deflator

## [2.41.4] - 2025-07-24 14:41:02

### Fixed

- Parameterize age 35 threshold in LHA shared accommodation rules

## [2.41.3] - 2025-07-24 13:53:51

### Fixed

- change LHA param name

## [2.41.2] - 2025-07-24 10:30:43

### Fixed

- debug LHA lowercase

## [2.41.1] - 2025-07-22 20:55:35

### Changed

- Update microdf_python dependency to >=1.0.0.

## [2.41.0] - 2025-07-22 19:49:35

### Changed

- Standardize decimals in parameters.

## [2.40.2] - 2025-07-22 09:37:07

### Fixed

- Bug in uprating.

## [2.40.1] - 2025-07-21 15:37:49

### Fixed

- Bug in handling downloads of UKMultiYearDataset from HuggingFace.

## [2.40.0] - 2025-07-21 13:23:31

### Added

- UKMultiYearDataset class to handle multiple fiscal years.
- Uprating of datasets using the `uprate` method.

## [2.39.3] - 2025-07-17 12:45:26

### Fixed

- NI domestic rates taken as reported.

## [2.39.2] - 2025-07-17 10:41:08

### Fixed

- Use outturn data for council tax growth in England, Scotland, and Wales for 2023-2025.

## [2.39.1] - 2025-07-16 11:08:29

### Fixed

- Improved water bills projections.

## [2.39.0] - 2025-07-15 11:58:59

### Added

- Codecov coverage.
- Expanded .gitignore.

## [2.38.2] - 2025-07-15 08:50:48

### Fixed

- Temporarily suspended employer_ni_fixed_cost_change as it returns impacts in the baseline.

## [2.38.1] - 2025-07-14 15:03:33

### Fixed

- Lag CPI correctly for benefit uprating.

## [2.38.0] - 2025-07-14 14:10:31

### Fixed

- Uprating for rent split by private and social rented sectors.

## [2.37.0] - 2025-07-14 10:36:08

### Added

- Water bills projections.

## [2.36.1] - 2025-07-13 19:47:46

### Fixed

- Bug in loading entity tables.

## [2.36.0] - 2025-07-13 13:11:45

### Added

- Documentation on growth factors.
- Cleaned up non-standard uprating factors for wealth variables.
- Added triple lock uprating detail and reform switches.
- Added ability to download entity datasets from HuggingFace.

## [2.35.1] - 2025-07-11 14:15:07

### Fixed

- Private pension income index set to RPI<=5%

## [2.35.0] - 2025-07-11 13:43:26

### Changed

- Earnings uprated with OBR average earnings rather than per-capita employment income.

## [2.34.5] - 2025-07-10 16:14:53

### Fixed

- HBAI documentation updated to include Healthy Start vouchers and external child payments.

## [2.34.4] - 2025-07-10 16:12:40

### Added

- Missing HBAI variables.

## [2.34.3] - 2025-07-10 15:42:46

### Fixed

- Bug in private pension income uprating.

## [2.34.2] - 2025-07-10 14:28:02

### Fixed

- Documentation improved for HBAI income concept.
- Restructured HBAI income variables to better match the official definition.

## [2.34.1] - 2025-07-10 12:10:52

### Fixed

- Triple lock uses the average earnings index from the OBR.

## [2.34.0] - 2025-07-10 10:02:17

### Fixed

- Statutory maternity, paternity, and sick pay variables now use the `gov.obr.consumer_price_index` for uprating.
- SSMG no longer is uprated by inflation.

## [2.33.0] - 2025-07-09 12:34:06

### Added

- Growth factor documentation.

## [2.32.4] - 2025-06-30 11:28:06

### Fixed

- Abolish Council Tax has no budgetary impact.

## [2.32.3] - 2025-06-17 12:37:38

### Fixed

- Update UK parameters.

## [2.32.2] - 2025-06-12 12:42:27

### Fixed

- Bug with BRMA variable name.

## [2.32.1] - 2025-06-11 13:52:32

### Added

- Add test suite for abolition parameters functionality.

## [2.32.0] - 2025-06-11 08:59:43

### Added

- Winter Fuel Allowance means-testing reform.

## [2.31.0] - 2025-06-09 15:26:19

### Added

- ONS household population data from 2001-2043.
- Council tax per household projections from OBR data.

### Changed

- Updated employer National Insurance contribution rate to 15% from April 6, 2025.

## [2.30.0] - 2025-06-09 11:32:22

### Changed

- Updated employer National Insurance contribution rate to 15% from April 6, 2025.

## [2.29.0] - 2025-06-09 09:54:52

### Added

- Council tax projection parameters from OBR data.

## [2.28.3] - 2025-06-06 16:15:25

### Changed

- Refactored all Variable files to follow single-responsibility principle with one Variable class per file.
- Split approximately 70 multi-Variable Python files into individual files, improving code organization and maintainability.

## [2.28.2] - 2025-05-28 09:03:21

### Fixed

- Bug in employer NI incidence parameters.

## [2.28.1] - 2025-05-27 10:44:15

### Fixed

- Removed duplicate parameters in Pension Credit.

## [2.28.0] - 2025-05-22 13:19:28

### Fixed

- Pension Credit income sources.

## [2.27.0] - 2025-05-22 11:22:00

### Fixed

- Pension Credit income sources.

## [2.26.1] - 2025-05-22 11:07:31

### Fixed

- Backdated parameters to 2015 for safety.

## [2.26.0] - 2025-05-22 11:02:05

### Fixed

- Implemented 2016 Savings Credit eligibility restriction in Pension Credit.

## [2.25.0] - 2025-05-21 09:46:26

### Added

- Public service spending variables.

## [2.24.2] - 2025-05-08 12:42:28

### Added

- Added variable to represent partial usage of extended childcare entitlement hours
- Updated extended childcare entitlement calculation to account for partial hours usage

## [2.24.1] - 2025-05-06 15:36:49

### Fixed

- Delete redundant weeks_per_year file from extended childcare.

## [2.24.0] - 2025-04-16 13:04:31

### Added

- Child eligible variables for childcare programs.

## [2.23.2] - 2025-04-15 14:14:21

### Fixed

- Corrected the is_parent variable to properly identify parents.
- Fixed logic in childcare programs to ensure accurate calculations.

## [2.23.1] - 2025-04-15 08:32:54

### Fixed

- Removed uk-data as a dependency from the package.

## [2.23.0] - 2025-04-07 09:00:36

### Added

- Rename 'study childcare entitlement' to 'care to learn'

## [2.22.8] - 2025-04-03 11:26:35

### Fixed

- Bug in UC child limit calculation.

## [2.22.7] - 2025-04-03 11:12:35

### Fixed

- Uprating that fails on ubuntu.

## [2.22.6] - 2025-03-26 17:50:04

### Changed

- Updated with OBR forecast

## [2.22.5] - 2025-03-26 14:42:25

### Fixed

- Bug causing UK API impacts to fail.

## [2.22.4] - 2025-03-25 11:47:32

### Fixed

- Baseline microsimulations break with no reform.

## [2.22.3] - 2025-03-25 11:03:07

### Fixed

- OBR forecast parameters now affect other parameters.

## [2.22.2] - 2025-03-23 23:09:48

### Fixed

- PRs now run tests fully.

## [2.22.1] - 2025-03-19 20:33:18

### Fixed

- Bug in higher rate threshold timing.

## [2.22.0] - 2025-03-03 12:11:29

### Added

- Separate reforms to exempt parents of under [x] from the UC child limit and from CTC child limit.

## [2.21.0] - 2025-02-28 16:39:12

### Added

- Two-child limit age exemption reform for Child Tax Credit.

## [2.20.0] - 2025-02-28 15:38:29

### Added

- Two-child limit reform proposal.

## [2.19.4] - 2025-02-27 14:23:28

### Fixed

- Bug in universal childcare entitlement.

## [2.19.3] - 2025-02-25 16:13:06

### Fixed

- Capital gains LSRs bug.

## [2.19.2] - 2025-02-25 14:33:57

### Fixed

- Bug in LSRs.

## [2.19.1] - 2025-02-18 16:22:32

### Fixed

- Bug causing non-default datasets to not execute.

## [2.19.0] - 2025-02-11 11:14:35

## [2.18.0] - 2024-12-05 12:43:06

### Added

- Scottish Winter Fuel Payment equivalent.

## [2.17.0] - 2024-12-04 16:48:42

### Fixed

- Scottish baseline matched with Scottish Fiscal Commission.

## [2.16.0] - 2024-11-28 16:54:41

### Changed

- Pinned UK data to 1.9.0.

## [2.15.1] - 2024-11-05 14:05:53

### Fixed

- Bug in budget change reforms.

## [2.15.0] - 2024-10-30 17:24:57

### Added

- OBR Autumn 2024 EFO economic factors.

## [2.14.1] - 2024-10-30 14:02:58

### Fixed

- NI threshold in 2027.

## [2.14.0] - 2024-10-28 12:09:01

### Fixed

- Bugs affecting household app calculations.

## [2.13.2] - 2024-10-28 10:46:29

### Fixed

- Threshold freeze for ST extended to 2027.

## [2.13.1] - 2024-10-24 13:24:27

### Fixed

- Bug causing capital gains responses to be calculated for every reform simulation.

## [2.13.0] - 2024-10-24 11:42:25

### Fixed

- Bug causing household app crashes.
- Metadat for OBR parameters.

## [2.12.0] - 2024-10-23 14:47:21

### Added

- Capital Gains Tax elasticities.

## [2.11.0] - 2024-10-23 10:15:26

### Added

- Benefit uprating for 2025/26.

## [2.10.0] - 2024-10-22 11:24:42

### Changed

- Data bumped to 1.9.0.

## [2.9.0] - 2024-10-22 08:36:24

### Changed

- UK data updated to 1.8.0.

## [2.8.0] - 2024-10-21 13:04:20

### Fixed

- Adjusted private school attendance factor to 0.85.

## [2.7.0] - 2024-10-21 10:09:01

### Added

- Automatic allocation of post-employee-incidence employee to households (consumers/capital).

## [2.6.0] - 2024-10-19 19:58:09

### Fixed

- Bug in budget change reforms.

## [2.5.0] - 2024-10-19 09:27:21

### Changed

- UK data package bumped to 1.6.

## [2.4.0] - 2024-10-17 21:43:42

### Added

- Employee incidence percentage for employer NICs.

## [2.3.0] - 2024-10-17 10:47:06

### Changed

- UK-data bumped to 1.5.

## [2.2.0] - 2024-10-16 11:52:07

### Fixed

- Add employer NI incidence.

## [2.1.1] - 2024-09-18 11:12:23

## [2.1.0] - 2024-09-18 11:04:12

### Fixed

- Add back recursive-include.

## [2.0.0] - 2024-09-18 10:53:42

### Changed

- Dataset handling outsourced to policyengine-uk-data.

## [1.8.0] - 2024-09-16 11:41:10

### Fixed

- Missing metadata in variables.
- Inflation uprating for some parameters.
- Inconsistent variable capitalisation.

## [1.7.4] - 2024-09-16 09:32:28

### Fixed

- Ensure rent index is tracking CPI.

## [1.7.3] - 2024-09-03 22:35:35

### Changed

- Update policyengine-core.
- Apply new approach to determine if in a microsimulation.

## [1.7.2] - 2024-08-28 23:37:22

### Added

- Test suite for private_school_vat
- Test suite for attends_private_school

## [1.7.1] - 2024-08-22 20:35:09

### Added

- Mask applied to private_school_vat to prevent calculation error when household weights aren't provided

## [1.7.0] - 2024-08-15 11:36:14

### Added

- CPI category forecasts.

## [1.6.0] - 2024-08-15 11:09:56

### Fixed

- Updated inflation uprating for COICOP categories.

## [1.5.1] - 2024-08-12 22:11:31

### Changed

- Corrected spelling on SPI validation documentation entry
- Corrected argparse version

## [1.5.0] - 2024-08-08 15:33:05

### Added

- Docs page about SPI 2020/21 validation

### Fixed

- Correct Scottish income tax rates for 2020/21

## [1.4.0] - 2024-07-30 13:05:05

### Added

- Winter Fuel Payment to household benefits.

## [1.3.0] - 2024-07-29 16:47:34

### Added

- Winter Fuel Allowance.

## [1.2.0] - 2024-07-27 10:02:38

### Added

- Tax on excess pension contributions

### Fixed

- Include Scottish income tax calculation within overall UK income tax calculation
- Apply allowances to all types of income
- Prevent negative income tax output
- Update Dividend Allowance values
- Correct Starter Rate for Savings taper structure
- Prevent calculation errors due to empty extra dividend bracket with conflicting rates

## [1.1.0] - 2024-07-26 08:35:13

### Changed

- Simplified uprating indices by moving OBR parameters to gov folder.

## [1.0.0] - 2024-07-19 09:43:03

### Changed

- Fiscal years are years by default.

## [0.86.6] - 2024-07-17 16:23:18

### Fixed

- Ensure household API version script bumps UK version

## [0.86.5] - 2024-07-17 15:26:43

### Added

- References to many income tax provisions.

### Fixed

- Folder distribution and formatting for income tax-related variables.
- pays_scottish_income_tax now returns a Boolean value.

## [0.86.4] - 2024-07-15 12:12:25

### Changed

- Refactor the Housing Benefit parameter, variable and test files.

## [0.86.3] - 2024-07-11 14:58:53

### Changed

- Refactor the Universal Credit parameter, variable and test files.

## [0.86.2] - 2024-07-10 20:08:36

### Added

- Auto-updating of the household API when this package is updated

## [0.86.1] - 2024-07-10 18:58:10

### Added

- Tests to income-related variables

## [0.86.0] - 2024-07-10 18:29:49

### Added

- 2022-23 FRS.

## [0.85.0] - 2024-06-28 19:59:31

### Added

- High-income budget switch.

## [0.84.0] - 2024-06-28 16:35:47

### Added

- Non-dom status switch.

## [0.83.2] - 2024-06-28 00:49:27

### Added

- Private school VAT calculation

## [0.83.1] - 2024-06-17 16:09:43

### Changed

- Uprated PIP, DLA, and Accessibility Account
- Re-enabled PIP and DLA within webapp
- Corrected mistakes in PIP

## [0.83.0] - 2024-06-11 15:49:29

### Fixed

- Property sale rates at 4.5%.

## [0.82.0] - 2024-06-11 07:51:23

### Added

- Budgetary change distributional impact parameters.

## [0.81.0] - 2024-06-10 12:42:45

### Added

- Conservative manifesto policy to move CB HITC to household based.

## [0.80.0] - 2024-06-07 08:22:24

### Added

- Recent reforms to Income Tax and NI.

## [0.79.0] - 2024-05-28 11:46:47

### Added

- Improvements to State Pension handling.
- Basic/additional State Pension splitting.

## [0.78.0] - 2024-05-27 22:27:48

### Added

- Pensioner personal allowance

## [0.77.0] - 2024-05-23 17:20:21

### Added

- Abolition switch for State Pension payments.
- Freeze switch for Pension Credit payments.

### Fixed

- New benefit claimants are now accounted for in reforms.

## [0.76.0] - 2024-05-02 11:47:45

### Added

- U.S. progress on labour supply responses.

## [0.75.0] - 2024-05-01 16:32:07

### Added

- State Pension Age reforms.

## [0.74.1] - 2024-04-30 18:10:23

### Fixed

- Update BRMAs.

## [0.74.0] - 2024-04-30 17:53:26

### Fixed

- Capital gains tax improvements.

## [0.73.1] - 2024-04-16 13:18:46

### Fixed

- Bug causing frs_2021 simulations to error.
- Unnecessary system initialisation code.

## [0.73.0] - 2024-04-12 17:36:36

### Changed

- OBR forecast update.

## [0.72.0] - 2024-03-07 16:04:57

### Added

- add Income Tax Integration Test

## [0.71.0] - 2024-03-05 17:37:39

### Added

- Fuel duty revenue projections

## [0.70.0] - 2024-03-05 11:48:27

### Fixed

- Carbon tax intensities for 2024.
- UK NI rate for 2024.

## [0.69.1] - 2024-03-04 18:45:44

### Changed

- Lowered rates for Class 1 and Class 4 NICs, pursuant to the Autumn Statement 2023
- Set Class 2 NIC rate to 0%, pursuant to the Autumn Statement 2023

## [0.69.0] - 2024-02-19 22:26:55

### Added

- Docker image deployment for streamlit documentation.

## [0.68.0] - 2024-02-19 22:00:58

### Added

- Initial version of capital gains imputations and logic.

## [0.67.0] - 2024-02-17 21:35:30

### Added

- Household wealth decile.

### Changed

- Assign decile of -1 to households with negative income.

## [0.66.0] - 2024-02-01 16:02:50

### Added

- Add Income Tax test.

## [0.65.0] - 2024-01-28 17:39:54

### Changed

- Calibration routine to include benefit cap statistics.

### Fixed

- Benefit cap UC bug.

## [0.64.0] - 2024-01-04 16:18:59

### Added

- Update PIP documentation

## [0.63.2] - 2024-01-04 16:08:24

### Added

- Added tests for fuel duty.

## [0.63.1] - 2023-12-17 10:18:46

### Fixed

- Bump policyengine-core to capture simulation randomness bug fixes.

## [0.63.0] - 2023-12-15 14:54:47

### Changed

- Validated and standardised National Insurance variables.

## [0.62.2] - 2023-12-15 14:32:51

### Added

- Missing uprating parameters for 2018.

## [0.62.1] - 2023-12-14 16:07:36

### Added

- Test cases for TV Licence.

## [0.62.0] - 2023-12-05 12:45:18

### Added

- Enhanced FRS version for December 2023.

## [0.61.3] - 2023-11-26 14:29:46

### Fixed

- Added missing label for benefit uprating.

## [0.61.2] - 2023-11-24 10:49:06

### Fixed

- Added missing label for benefit uprating.

## [0.61.1] - 2023-11-23 18:03:37

## [0.61.0] - 2023-11-23 16:22:19

### Added

- Update National Insurance documentation
- Update Income Tax documentation

## [0.60.0] - 2023-11-22 15:17:21

### Added

- HM Treasury baseline for CPI uprating benefits.

## [0.59.0] - 2023-11-22 12:04:13

### Added

- Switch for benefit uprating.

## [0.58.2] - 2023-11-16 16:32:22

### Added

- Documentation for Land and Buildings Transaction Tax.
- Documentation for Land Transaction Tax.

### Fixed

- Updated LBTT rate increase for non-primary residences.
- Fixed SDLT description.

## [0.58.1] - 2023-10-27 20:42:43

### Fixed

- Bug causing child minimum basic income ages to function incorrectly when the adult UBI is nonzero.

## [0.58.0] - 2023-10-19 15:46:33

### Added

- Pension Credit documentation page.

## [0.57.0] - 2023-10-17 14:55:07

### Added

- Child minimum age for basic income.

## [0.56.4] - 2023-10-12 15:11:13

### Added

- Documentation for Stamp Duty Land Tax.

## [0.56.3] - 2023-10-09 19:01:07

## [0.56.2] - 2023-09-14 16:06:31

### Fixed

- Small issues on the NI page.

## [0.56.1] - 2023-09-14 15:35:12

### Added

- Documentation for TV licence.

## [0.56.0] - 2023-09-14 15:31:01

### Added

- Update Universal Credit documentation

## [0.55.4] - 2023-09-14 15:25:24

### Fixed

- TOC entry for NI documentation.

## [0.55.3] - 2023-09-14 13:53:16

### Added

- Documentation example.

## [0.55.2] - 2023-08-24 14:59:45

### Added

- Documentation for fuel duty.

## [0.55.1] - 2023-08-12 17:36:09

### Fixed

- Temporarily remove PIP, DLA and minimum wage parameters from the app.

## [0.55.0] - 2023-08-07 16:52:20

### Added

- Updates values for universal credit from 2016 to 2023

## [0.54.0] - 2023-07-21 12:20:43

### Changed

- Calibration updated with new DWP statistics.

## [0.53.0] - 2023-07-17 17:10:23

### Fixed

- Bug affecting the two-child limit (1% of households)

## [0.52.0] - 2023-07-09 19:21:46

### Added

- Updates to calibration statistics from 2023 benefits and tax sources.

## [0.51.1] - 2023-06-20 19:19:13

### Fixed

- A bug in the income-splitting logic that caused taxable incomes to be too low.

## [0.51.0] - 2023-06-18 09:17:08

### Added

- Marriage tax-related reforms.

## [0.50.1] - 2023-05-28 02:23:58

### Fixed

- Household basic income phase-out rate unit.

## [0.50.0] - 2023-05-27 15:52:33

### Added

- Python 3.10 support.

## [0.49.1] - 2023-05-23 12:04:57

### Added

- Missing labels for parameters.

## [0.49.0] - 2023-05-09 17:02:36

### Added

- Savings variable from the WAS.

### Fixed

- Added logging for targets in imputations for completeness.

## [0.48.0] - 2023-04-24 14:04:39

### Added

- 2023 tax rates for UK and Scotland

## [0.47.0] - 2023-04-24 14:03:45

### Added

- Spring Budget 2023 policy changes.

## [0.46.0] - 2023-04-24 12:16:00

### Added

- Extra tax bands for the UK and Scotland.

## [0.45.1] - 2023-04-10 13:36:29

### Added

- Speed improvements
- Parameter metadata fixes

## [0.45.0] - 2023-04-01 09:38:48

### Added

- Improvements to calibration routines.

## [0.44.3] - 2023-03-30 14:03:15

### Fixed

- Marriage Allowance previously didn't have an economic impact.

## [0.44.2] - 2023-03-26 00:21:18

### Fixed

- Import errors due to survey-enhance.

## [0.44.1] - 2023-03-25 23:53:14

### Fixed

- Made Survey-Enhance a dev dependency.

## [0.44.0] - 2023-03-23 08:45:05

### Changed

- PolicyEngine Core data updates accounted for.

## [0.43.0] - 2023-03-15 11:40:17

### Changed

- Fuel duty incidence assumed to be 100% on consumers.

## [0.42.1] - 2023-03-14 18:22:37

### Fixed

- Bugs relating to private pension contributions.

## [0.42.0] - 2023-03-03 16:23:13

### Added

- State Pension uprating parameter.

### Fixed

- Corporate wealth for pensioners capped to ensure consistency with pension income in some cases.
- EBC end date is before 2023.

## [0.41.11] - 2023-03-02 11:57:32

### Fixed

- Parameter updates for the CoL payments.
- Metadata for the CEC wealth tax.

## [0.41.10] - 2023-02-27 17:19:33

### Fixed

- EPG test used the wrong variable name.

## [0.41.9] - 2023-02-27 16:53:13

### Fixed

- EPG properly included in net income.

## [0.41.8] - 2023-02-27 16:01:50

### Fixed

- Properly exclude primary residence values from the CEC wealth tax.

## [0.41.7] - 2023-02-27 15:37:16

### Added

- Seasonality to EPG modelling (simple).
- EPG documentation updates.

## [0.41.6] - 2023-02-27 15:06:37

### Fixed

- Energy Price Guarantee implementation.

## [0.41.5] - 2023-02-27 13:23:51

### Fixed

- Bug causing pension contributions to not be correctly deducted from taxable income.

## [0.41.4] - 2023-02-01 03:38:40

### Changed

- Increased default age from 30 to 40.

## [0.41.3] - 2023-02-01 00:43:08

### Changed

- Raised default age from 18 to 30.

## [0.41.2] - 2023-01-27 13:02:28

### Changed

- VAT adjusted to hit administrative targets.

## [0.41.1] - 2023-01-27 09:21:35

### Changed

- MTR calculation limited to one person for speed improvement.
- Benefit cap implementation refactored to share code between UC and HB.

### Fixed

- Property income reduces UC as unearned income.

## [0.41.0] - 2023-01-26 20:09:59

### Added

- Wealth tax brackets.
- Intermediate benefit uprating (multiplies by a percentage).

## [0.40.0] - 2023-01-25 21:14:21

### Added

- VAT imputation and implementation.

## [0.39.0] - 2023-01-19 22:59:56

### Added

- Monthly NI calculations.

## [0.38.6] - 2023-01-10 17:31:54

### Changed

- Use `adds` and `subtracts` everywhere.
- Replace `aggr` with `add`.
- Apply `defined_for`.
- Use `default` arg to `select` rather than dummy `True` condition.

## [0.38.5] - 2023-01-06 10:07:28

### Added

- Metadata on modelled policies.

## [0.38.4] - 2023-01-03 23:39:07

### Changed

- PolicyEngine Core version widened.

## [0.38.3] - 2023-01-03 20:32:56

### Added

- Missing label in inputs.

## [0.38.2] - 2022-12-30 17:05:40

### Changed

- Reorganised variables in the input tree.

## [0.38.1] - 2022-12-28 17:28:42

### Fixed

- Bug causing UC housing entitlements to be too low for single people with children.

## [0.38.0] - 2022-12-27 13:53:34

### Added

- Normalised poverty and deep poverty variables.

## [0.37.6] - 2022-12-20 14:11:35

### Added

- Token for GitHub PR filing (deployment of the API).

## [0.37.5] - 2022-12-20 11:41:05

### Added

- ENV token for the deployment action.

## [0.37.4] - 2022-12-20 10:59:01

### Added

- Variable metadata for disability variables.
- Auto-update for the API.

## [0.37.3] - 2022-12-15 16:10:43

### Changed

- Bumped PolicyEngine-Core.

## [0.37.2] - 2022-12-14 16:33:27

### Added

- Metadata for PolicyEngine.

## [0.37.1] - 2022-12-13 20:20:48

### Added

- Metadata for contrib parameters.

## [0.37.0] - 2022-12-11 18:29:22

### Added

- LVT
- Carbon tax
- NI BRMAs
- NI domestic rates by local authority

## [0.36.2] - 2022-12-07 13:50:34

### Fixed

- Incorporated Core fix.

## [0.36.1] - 2022-12-07 13:31:54

### Fixed

- PolicyEngine-Core pinned to a minor version.

## [0.36.0] - 2022-12-06 12:00:54

### Changed

- Roles to 'member'.

## [0.35.0] - 2022-10-22 18:22:07

### Changed

- Moved to PolicyEngine Core.

## [0.34.1] - 2022-10-04 11:02:45

### Fixed

- UC amount for single, under-25s after the last uprating.

## [0.34.0] - 2022-09-27 15:37:07

### Added

- Flat basic income amount.

## [0.33.0] - 2022-09-21 11:06:49

### Added

- Metadata for SDLT, LTT and LBTT parameters.

## [0.32.0] - 2022-09-17 16:24:23

### Added

- Wealth tax.

## [0.31.1] - 2022-09-15 13:40:02

### Fixed

- Validation page.

## [0.31.0] - 2022-09-14 19:32:06

### Added

- Energy Price Guarantee parametric reform.

## [0.30.1] - 2022-09-11 15:04:15

### Added

- New monthly CPI values until July.

## [0.30.0] - 2022-09-07 12:15:01

### Added

- Ofgem energy price cap subsidy parameters.

## [0.29.0] - 2022-08-28 14:45:36

## [0.28.1] - 2022-08-25 17:36:23

### Fixed

- Round marriage allowance.

## [0.28.0] - 2022-07-27 10:14:59

### Added

- TV licence fee.

## [0.27.0] - 2022-07-25 11:14:58

### Added

- Dashboard tool for the calibration procedure.
- Loss components for aggregates in demographic targets.

### Fixed

- A bug causing Pension Credit to under-react to increases in Income Tax.

## [0.26.1] - 2022-06-05 20:28:29

### Added

- References for some tax and UC parameters.

## [0.26.0] - 2022-05-26 16:16:50

### Added

- Disability benefits to COL support measures.

## [0.25.0] - 2022-05-26 13:04:11

### Added

- UK Government cost-of-living support measures.

## [0.24.0] - 2022-05-26 10:46:43

### Added

- Miscellaneous benefit payment.

## [0.23.3] - 2022-05-22 15:27:50

### Fixed

- Baseline variables are now generated before calibration (fixes a bug causing overestimation of benefit caseloads).

## [0.23.2] - 2022-05-21 16:01:32

### Changed

- Reorganize documentation and variables.

## [0.23.1] - 2022-05-19 14:58:06

### Fixed

- National Insurance thresholds pre-July, post-Spring Statement (inflation adjustments).

## [0.23.0] - 2022-05-16 14:02:26

### Added

- Household-level phase-outs for basic income.

## [0.22.0] - 2022-04-29 09:29:26

### Changed

- Calibration process improved with country-level targets.

## [0.21.0] - 2022-04-26 12:10:51

### Changed

- Pension Credit code quality improvements.

### Fixed

- Pension Credit missing disability elements.

## [0.20.4] - 2022-04-22 21:26:10

### Fixed

- Land and carbon are calculated based off UK-wide statistics, not in-model statistics.

## [0.20.3] - 2022-04-14 13:10:26

### Fixed

- MANIFEST.in file re-added (caused previous two issues).

## [0.20.2] - 2022-04-14 12:48:06

### Fixed

- Failed imports of reform tools.

## [0.20.1] - 2022-04-14 12:36:43

### Fixed

- Failed import of policyengine_uk.tools

## [0.20.0] - 2022-04-14 11:46:45

### Added

- Dataset generation.

## [0.19.5] - 2022-04-08 10:35:59

### Fixed

- Chart on carbon intensities.

## [0.19.4] - 2022-04-07 10:36:03

### Added

- Carbon emissions (production-based) by industry.

## [0.19.3] - 2022-04-07 09:51:58

### Fixed

- A bug preventing the Synthetic FRS from loading.

## [0.19.2] - 2022-04-05 14:23:50

### Added

- Carbon tax model page added.

## [0.19.1] - 2022-04-05 12:28:40

### Fixed

- Spring Statement Class 4 NI change correctly follows 2022/23 adjustment.

## [0.19.0] - 2022-04-05 09:41:35

### Added

- Total wealth variable.

## [0.18.0] - 2022-04-03 19:28:24

### Fixed

- Synthetic FRS now successfully loads.
- Incorporates better calibration and imputations.

## [0.17.0] - 2022-03-27 14:13:20

### Added

- Tax and benefit changes announced in the 2022 Spring Statement.
- Inflation and real disposable income.
- Parameters for PIP, DLA, SDA, AA and Carer's Allowance.

### Changed

- Added calibration make.

## [0.16.2] - 2022-03-24 03:05:39

### Fixed

- Bugs related to uprating parameters.

## [0.16.1] - 2022-03-24 03:05:39

### Fixed

- Pull request merge action didn't correctly update the repo.

## [0.16.0] - 2022-03-24 00:22:00

### Added

- Forecasting to 2027: new and improved household weights.

## [0.15.0] - 2022-03-23 00:00:00

### Added

- Forecasting to 2027: new and improved household weights.

## [0.14.4] - 2022-03-08 00:00:01

## [0.14.3] - 2022-03-08 00:00:00

### Fixed

- Basic income means-test inclusion previously didn't work correctly (when turned off) for Housing Benefit and Pension Credit.

## [0.14.2] - 2022-03-04 00:00:01

### Changed

- Re-weighting procedure improved with consolidated categories and added income source targeting.

## [0.14.1] - 2022-03-04 00:00:00

### Added

- Added a production-based carbon emissions parameter.

## [0.14.0] - 2022-02-28 00:00:01

### Changed

- Re-weighting procedure formalised with cross-validation and logging.

## [0.13.0] - 2022-02-28 00:00:00

### Added

- Pensioner exemption switch for Income Tax rate and threshold reforms.

## [0.12.4] - 2022-02-25 00:00:00

### Added

- Historical carbon emissions parameter.

## [0.12.3] - 2022-02-14 00:00:02

### Changed

- Set basic income phaseout threshold default to 0.

## [0.12.2] - 2022-02-14 00:00:01

### Added

- Basic income parameters and logic.

## [0.12.1] - 2022-02-14 00:00:00

### Changed

- OpenFisca-Tools bumped to v0.3

## [0.12.0] - 2022-02-06 00:00:00

### Added

- The Energy Bills Rebate scheme.

## [0.11.0] - 2022-02-04 00:00:00

### Added

- Re-weighting routine for the Family Resources Survey, matching aggregates, participation and populations.

## [0.10.10] - 2022-01-22 00:00:01

### Added

- Unit test for benefit unit rent.

### Changed

- OpenFisca-Tools dependency patch increased.

## [0.10.9] - 2022-01-22 00:00:00

### Fixed

- Baseline HBAI-excluded income variable now uses the Synthetic FRS when the enhanced FRS is not available.

## [0.10.8] - 2022-01-18 00:00:00

### Added

- Metadata (period, unit, name, label) for all Universal Credit parameters.

## [0.10.7] - 2022-01-17 00:00:01

### Fixed

- Household gross income calculated directly from household benefits and market income.
- Savings allowance was previously set to zero erroneously for households in Scotland at the starter or intermediate bands.

## [0.10.6] - 2022-01-17 00:00:00

### Added

- Stocks/flows metadata for PolicyEngine-facing variables.

## [0.10.5] - 2022-01-16 00:00:00

### Added

- When datasets are not available, a prompt is displayed to download them or use synthetic data.
- CLI interface trigger changed from `openfisca-uk-setup` to `openfisca-uk` and default years updated.

## [0.10.4] - 2022-01-14 00:00:00

### Changed

- PolicyEngine-UK-Data version increased to 0.7.0.

## [0.10.3] - 2022-01-12 00:00:00

### Added

- Sure Start Maternity Grant (reported).

### Changed

- Education benefits summed in a formula.

### Fixed

- Some maternity benefits (SSMG, SMP) and WFA not included in benefits.

## [0.10.2] - 2022-01-08 00:00:01

### Changed

- Removes the `u` prefix from all variable label strings.

## [0.10.1] - 2022-01-08 00:00:00

### Changed

- Label metadata for tax variables.

## [0.10.0] - 2022-01-07 00:00:01

### Added

- Parameter representing the Child Tax Credit's child limit.

### Changed

- Renamed parameter representing Universal Credit's child limit.

## [0.9.2] - 2022-01-07 00:00:00

### Added

- Metadata for the Dividend, Property and Trading Allowances.

## [0.9.1] - 2021-12-29 00:00:02

### Added

- Microsimulation tests and YAML data for Child Benefit, Tax Credits and Council Tax.
- Documentation page for Tax Credits.
- Simplified dataset usage to enhanced FRS only.

## [0.9.0] - 2021-12-29 00:00:01

### Added

- Minimum tax credit benefit amount.

## [0.8.1] - 2021-12-29 00:00:00

## [0.8.0] - 2021-12-27 00:00:00

### Added

- Historical Working Tax Credit parameters since 2002 (previously since 2016).
- Legislative references for Working Tax Credit parameters.

### Changed

- Working Tax Credit child care parameters represent the maximum amount, prior to the share covered.

### Fixed

- Apply Working Tax Credit old-age provision to 60-year-olds.
- Qualify people working 30 hours for the Working Tax Credit.
- Point afcs to afcs_reported instead of AA_reported.
- Fix units on some variables.

## [0.7.17] - 2021-12-23 00:00:00

### Added

- Units for some variables.

### Changed

- Code refactoring.

## [0.7.16] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.15] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.14] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.13] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.12] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.11] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.10] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.9] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.8] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.7] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.6] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.5] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.4] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.3] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.2] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.1] - 2021-07-05 00:00:00

### Changed

- Patch update

## [0.7.0] - 2021-07-05 00:00:00

### Changed

- Minor update

## [0.6.0] - 2021-07-05 00:00:00

### Changed

- Minor update

## [0.5.0] - 2021-07-05 00:00:00

### Changed

- Minor update

## [0.4.0] - 2021-07-05 00:00:00

### Added

- Tests for variable naming conventions.
- Postcode lookup optional features available.
- LHA rates for all BRMA areas added.

### Changed

- PolicyEngine-UK now runs from the official OpenFisca-Core.

## [0.3.0] - 2021-07-04 00:00:00

### Added

- New interface for microsimulation.
- Sources in tax logic.
- Tests.

### Changed

- Microdata now generated and loaded in-model.
- Variable time periods made more consistent.
- Derivative calculations made more efficient and have more options.

## [0.2.3] - 2021-04-21 00:00:00

### Changed

- MicroDataFrame and MicroSeries returned by default.

### Fixed

- Bugs.

## [0.2.2] - 2021-04-20 00:00:00

### Added

- Jupyter-Book documentation.
- More detailed disability variables.

### Fixed

- IndividualSim reform handling.

## [0.2.1] - 2021-04-19 00:00:00

### Changed

- Improved documentation of parameters.
- Tests now occur in 2021 to ensure FY20-21 parameters are used.

### Fixed

- Bug in CB-HITC that caused overestimation.

## [0.2.0] - 2020-12-05 00:00:00

### Changed

- Time periods now appropriate, using an implementation of WEEK for most benefits.
- MTRs handled properly and include a breakdown.
- Simulation tools are improved and included in a class.

## [0.1.0] - 2020-11-08 00:00:00

### Added

- Income Tax and National Insurance.
- All benefits are at least taken from survey reporting (can be switched on-off).
- Child Benefit is modelled, others such as Income Support, JSA (both types), Tax Credits can be simulated/reformed but require more reviewing in how to account for discrepancies caused by take-up rates.
- Four budget-neutral UBI reforms are implemented.
- 15 test cases (unit and integration) testing benefits and taxes.
- Simulation helper tools.



[2.74.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.73.2...2.74.0
[2.73.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.73.1...2.73.2
[2.73.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.73.0...2.73.1
[2.73.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.72.4...2.73.0
[2.72.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.72.3...2.72.4
[2.72.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.72.2...2.72.3
[2.72.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.72.1...2.72.2
[2.72.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.72.0...2.72.1
[2.72.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.71.1...2.72.0
[2.71.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.71.0...2.71.1
[2.71.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.7...2.71.0
[2.70.7]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.6...2.70.7
[2.70.6]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.5...2.70.6
[2.70.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.4...2.70.5
[2.70.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.3...2.70.4
[2.70.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.2...2.70.3
[2.70.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.1...2.70.2
[2.70.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.70.0...2.70.1
[2.70.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.69.0...2.70.0
[2.69.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.68.1...2.69.0
[2.68.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.68.0...2.68.1
[2.68.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.67.0...2.68.0
[2.67.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.66.0...2.67.0
[2.66.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.9...2.66.0
[2.65.9]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.8...2.65.9
[2.65.8]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.7...2.65.8
[2.65.7]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.6...2.65.7
[2.65.6]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.5...2.65.6
[2.65.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.4...2.65.5
[2.65.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.3...2.65.4
[2.65.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.2...2.65.3
[2.65.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.1...2.65.2
[2.65.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.65.0...2.65.1
[2.65.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.64.1...2.65.0
[2.64.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.64.0...2.64.1
[2.64.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.63.0...2.64.0
[2.63.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.62.1...2.63.0
[2.62.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.62.0...2.62.1
[2.62.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.61.4...2.62.0
[2.61.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.61.3...2.61.4
[2.61.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.61.2...2.61.3
[2.61.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.61.1...2.61.2
[2.61.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.61.0...2.61.1
[2.61.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.60.0...2.61.0
[2.60.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.59.0...2.60.0
[2.59.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.58.0...2.59.0
[2.58.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.57.1...2.58.0
[2.57.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.57.0...2.57.1
[2.57.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.56.1...2.57.0
[2.56.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.56.0...2.56.1
[2.56.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.55.3...2.56.0
[2.55.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.55.2...2.55.3
[2.55.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.55.1...2.55.2
[2.55.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.55.0...2.55.1
[2.55.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.54.2...2.55.0
[2.54.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.54.1...2.54.2
[2.54.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.54.0...2.54.1
[2.54.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.53.1...2.54.0
[2.53.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.53.0...2.53.1
[2.53.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.52.1...2.53.0
[2.52.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.52.0...2.52.1
[2.52.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.51.0...2.52.0
[2.51.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.50.0...2.51.0
[2.50.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.49.5...2.50.0
[2.49.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.49.4...2.49.5
[2.49.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.49.3...2.49.4
[2.49.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.49.2...2.49.3
[2.49.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.49.1...2.49.2
[2.49.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.49.0...2.49.1
[2.49.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.48.0...2.49.0
[2.48.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.47.4...2.48.0
[2.47.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.47.3...2.47.4
[2.47.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.47.2...2.47.3
[2.47.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.47.1...2.47.2
[2.47.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.47.0...2.47.1
[2.47.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.46.3...2.47.0
[2.46.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.46.2...2.46.3
[2.46.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.46.1...2.46.2
[2.46.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.46.0...2.46.1
[2.46.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.45.5...2.46.0
[2.45.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.45.4...2.45.5
[2.45.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.45.3...2.45.4
[2.45.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.45.2...2.45.3
[2.45.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.45.1...2.45.2
[2.45.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.45.0...2.45.1
[2.45.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.44.1...2.45.0
[2.44.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.44.0...2.44.1
[2.44.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.43.5...2.44.0
[2.43.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.43.4...2.43.5
[2.43.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.43.3...2.43.4
[2.43.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.43.2...2.43.3
[2.43.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.43.1...2.43.2
[2.43.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.43.0...2.43.1
[2.43.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.42.0...2.43.0
[2.42.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.41.4...2.42.0
[2.41.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.41.3...2.41.4
[2.41.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.41.2...2.41.3
[2.41.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.41.1...2.41.2
[2.41.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.41.0...2.41.1
[2.41.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.40.2...2.41.0
[2.40.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.40.1...2.40.2
[2.40.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.40.0...2.40.1
[2.40.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.39.3...2.40.0
[2.39.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.39.2...2.39.3
[2.39.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.39.1...2.39.2
[2.39.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.39.0...2.39.1
[2.39.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.38.2...2.39.0
[2.38.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.38.1...2.38.2
[2.38.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.38.0...2.38.1
[2.38.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.37.0...2.38.0
[2.37.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.36.1...2.37.0
[2.36.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.36.0...2.36.1
[2.36.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.35.1...2.36.0
[2.35.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.35.0...2.35.1
[2.35.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.34.5...2.35.0
[2.34.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.34.4...2.34.5
[2.34.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.34.3...2.34.4
[2.34.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.34.2...2.34.3
[2.34.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.34.1...2.34.2
[2.34.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.34.0...2.34.1
[2.34.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.33.0...2.34.0
[2.33.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.32.4...2.33.0
[2.32.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.32.3...2.32.4
[2.32.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.32.2...2.32.3
[2.32.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.32.1...2.32.2
[2.32.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.32.0...2.32.1
[2.32.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.31.0...2.32.0
[2.31.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.30.0...2.31.0
[2.30.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.29.0...2.30.0
[2.29.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.28.3...2.29.0
[2.28.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.28.2...2.28.3
[2.28.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.28.1...2.28.2
[2.28.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.28.0...2.28.1
[2.28.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.27.0...2.28.0
[2.27.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.26.1...2.27.0
[2.26.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.26.0...2.26.1
[2.26.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.25.0...2.26.0
[2.25.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.24.2...2.25.0
[2.24.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.24.1...2.24.2
[2.24.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.24.0...2.24.1
[2.24.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.23.2...2.24.0
[2.23.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.23.1...2.23.2
[2.23.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.23.0...2.23.1
[2.23.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.8...2.23.0
[2.22.8]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.7...2.22.8
[2.22.7]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.6...2.22.7
[2.22.6]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.5...2.22.6
[2.22.5]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.4...2.22.5
[2.22.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.3...2.22.4
[2.22.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.2...2.22.3
[2.22.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.1...2.22.2
[2.22.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.22.0...2.22.1
[2.22.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.21.0...2.22.0
[2.21.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.20.0...2.21.0
[2.20.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.19.4...2.20.0
[2.19.4]: https://github.com/PolicyEngine/openfisca-uk/compare/2.19.3...2.19.4
[2.19.3]: https://github.com/PolicyEngine/openfisca-uk/compare/2.19.2...2.19.3
[2.19.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.19.1...2.19.2
[2.19.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.19.0...2.19.1
[2.19.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.18.0...2.19.0
[2.18.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.17.0...2.18.0
[2.17.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.16.0...2.17.0
[2.16.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.15.1...2.16.0
[2.15.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.15.0...2.15.1
[2.15.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.14.1...2.15.0
[2.14.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.14.0...2.14.1
[2.14.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.13.2...2.14.0
[2.13.2]: https://github.com/PolicyEngine/openfisca-uk/compare/2.13.1...2.13.2
[2.13.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.13.0...2.13.1
[2.13.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.12.0...2.13.0
[2.12.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.11.0...2.12.0
[2.11.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.10.0...2.11.0
[2.10.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.9.0...2.10.0
[2.9.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.8.0...2.9.0
[2.8.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.7.0...2.8.0
[2.7.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.6.0...2.7.0
[2.6.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.5.0...2.6.0
[2.5.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.4.0...2.5.0
[2.4.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.3.0...2.4.0
[2.3.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.2.0...2.3.0
[2.2.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/PolicyEngine/openfisca-uk/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/PolicyEngine/openfisca-uk/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.8.0...2.0.0
[1.8.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.7.4...1.8.0
[1.7.4]: https://github.com/PolicyEngine/openfisca-uk/compare/1.7.3...1.7.4
[1.7.3]: https://github.com/PolicyEngine/openfisca-uk/compare/1.7.2...1.7.3
[1.7.2]: https://github.com/PolicyEngine/openfisca-uk/compare/1.7.1...1.7.2
[1.7.1]: https://github.com/PolicyEngine/openfisca-uk/compare/1.7.0...1.7.1
[1.7.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.6.0...1.7.0
[1.6.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.5.1...1.6.0
[1.5.1]: https://github.com/PolicyEngine/openfisca-uk/compare/1.5.0...1.5.1
[1.5.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.4.0...1.5.0
[1.4.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/PolicyEngine/openfisca-uk/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.6...1.0.0
[0.86.6]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.5...0.86.6
[0.86.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.4...0.86.5
[0.86.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.3...0.86.4
[0.86.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.2...0.86.3
[0.86.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.1...0.86.2
[0.86.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.86.0...0.86.1
[0.86.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.85.0...0.86.0
[0.85.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.84.0...0.85.0
[0.84.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.83.2...0.84.0
[0.83.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.83.1...0.83.2
[0.83.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.83.0...0.83.1
[0.83.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.82.0...0.83.0
[0.82.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.81.0...0.82.0
[0.81.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.80.0...0.81.0
[0.80.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.79.0...0.80.0
[0.79.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.78.0...0.79.0
[0.78.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.77.0...0.78.0
[0.77.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.76.0...0.77.0
[0.76.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.75.0...0.76.0
[0.75.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.74.1...0.75.0
[0.74.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.74.0...0.74.1
[0.74.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.73.1...0.74.0
[0.73.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.73.0...0.73.1
[0.73.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.72.0...0.73.0
[0.72.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.71.0...0.72.0
[0.71.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.70.0...0.71.0
[0.70.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.69.1...0.70.0
[0.69.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.69.0...0.69.1
[0.69.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.68.0...0.69.0
[0.68.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.67.0...0.68.0
[0.67.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.66.0...0.67.0
[0.66.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.65.0...0.66.0
[0.65.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.64.0...0.65.0
[0.64.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.63.2...0.64.0
[0.63.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.63.1...0.63.2
[0.63.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.63.0...0.63.1
[0.63.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.62.2...0.63.0
[0.62.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.62.1...0.62.2
[0.62.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.62.0...0.62.1
[0.62.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.61.3...0.62.0
[0.61.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.61.2...0.61.3
[0.61.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.61.1...0.61.2
[0.61.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.61.0...0.61.1
[0.61.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.60.0...0.61.0
[0.60.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.59.0...0.60.0
[0.59.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.58.2...0.59.0
[0.58.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.58.1...0.58.2
[0.58.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.58.0...0.58.1
[0.58.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.57.0...0.58.0
[0.57.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.56.4...0.57.0
[0.56.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.56.3...0.56.4
[0.56.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.56.2...0.56.3
[0.56.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.56.1...0.56.2
[0.56.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.56.0...0.56.1
[0.56.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.55.4...0.56.0
[0.55.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.55.3...0.55.4
[0.55.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.55.2...0.55.3
[0.55.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.55.1...0.55.2
[0.55.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.55.0...0.55.1
[0.55.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.54.0...0.55.0
[0.54.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.53.0...0.54.0
[0.53.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.52.0...0.53.0
[0.52.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.51.1...0.52.0
[0.51.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.51.0...0.51.1
[0.51.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.50.1...0.51.0
[0.50.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.50.0...0.50.1
[0.50.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.49.1...0.50.0
[0.49.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.49.0...0.49.1
[0.49.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.48.0...0.49.0
[0.48.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.47.0...0.48.0
[0.47.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.46.0...0.47.0
[0.46.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.45.1...0.46.0
[0.45.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.45.0...0.45.1
[0.45.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.44.3...0.45.0
[0.44.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.44.2...0.44.3
[0.44.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.44.1...0.44.2
[0.44.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.44.0...0.44.1
[0.44.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.43.0...0.44.0
[0.43.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.42.1...0.43.0
[0.42.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.42.0...0.42.1
[0.42.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.11...0.42.0
[0.41.11]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.10...0.41.11
[0.41.10]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.9...0.41.10
[0.41.9]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.8...0.41.9
[0.41.8]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.7...0.41.8
[0.41.7]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.6...0.41.7
[0.41.6]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.5...0.41.6
[0.41.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.4...0.41.5
[0.41.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.3...0.41.4
[0.41.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.2...0.41.3
[0.41.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.1...0.41.2
[0.41.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.41.0...0.41.1
[0.41.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.40.0...0.41.0
[0.40.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.39.0...0.40.0
[0.39.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.6...0.39.0
[0.38.6]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.5...0.38.6
[0.38.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.4...0.38.5
[0.38.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.3...0.38.4
[0.38.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.2...0.38.3
[0.38.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.1...0.38.2
[0.38.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.38.0...0.38.1
[0.38.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.6...0.38.0
[0.37.6]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.5...0.37.6
[0.37.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.4...0.37.5
[0.37.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.3...0.37.4
[0.37.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.2...0.37.3
[0.37.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.1...0.37.2
[0.37.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.37.0...0.37.1
[0.37.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.36.2...0.37.0
[0.36.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.36.1...0.36.2
[0.36.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.36.0...0.36.1
[0.36.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.35.0...0.36.0
[0.35.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.34.1...0.35.0
[0.34.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.34.0...0.34.1
[0.34.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.33.0...0.34.0
[0.33.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.32.0...0.33.0
[0.32.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.31.1...0.32.0
[0.31.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.31.0...0.31.1
[0.31.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.30.1...0.31.0
[0.30.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.30.0...0.30.1
[0.30.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.29.0...0.30.0
[0.29.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.28.1...0.29.0
[0.28.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.28.0...0.28.1
[0.28.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.27.0...0.28.0
[0.27.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.26.1...0.27.0
[0.26.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.26.0...0.26.1
[0.26.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.25.0...0.26.0
[0.25.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.24.0...0.25.0
[0.24.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.23.3...0.24.0
[0.23.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.23.2...0.23.3
[0.23.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.23.1...0.23.2
[0.23.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.23.0...0.23.1
[0.23.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.22.0...0.23.0
[0.22.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.21.0...0.22.0
[0.21.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.20.4...0.21.0
[0.20.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.20.3...0.20.4
[0.20.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.20.2...0.20.3
[0.20.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.20.1...0.20.2
[0.20.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.20.0...0.20.1
[0.20.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.19.5...0.20.0
[0.19.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.19.4...0.19.5
[0.19.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.19.3...0.19.4
[0.19.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.19.2...0.19.3
[0.19.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.19.1...0.19.2
[0.19.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.19.0...0.19.1
[0.19.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.18.0...0.19.0
[0.18.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.17.0...0.18.0
[0.17.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.16.2...0.17.0
[0.16.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.16.1...0.16.2
[0.16.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.16.0...0.16.1
[0.16.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.15.0...0.16.0
[0.15.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.14.4...0.15.0
[0.14.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.14.3...0.14.4
[0.14.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.14.2...0.14.3
[0.14.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.14.1...0.14.2
[0.14.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.14.0...0.14.1
[0.14.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.13.0...0.14.0
[0.13.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.12.4...0.13.0
[0.12.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.12.3...0.12.4
[0.12.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.12.2...0.12.3
[0.12.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.12.1...0.12.2
[0.12.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.12.0...0.12.1
[0.12.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.11.0...0.12.0
[0.11.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.10...0.11.0
[0.10.10]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.9...0.10.10
[0.10.9]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.8...0.10.9
[0.10.8]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.7...0.10.8
[0.10.7]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.6...0.10.7
[0.10.6]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.5...0.10.6
[0.10.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.4...0.10.5
[0.10.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.3...0.10.4
[0.10.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.2...0.10.3
[0.10.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.1...0.10.2
[0.10.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.10.0...0.10.1
[0.10.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.9.2...0.10.0
[0.9.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.9.1...0.9.2
[0.9.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.9.0...0.9.1
[0.9.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.8.1...0.9.0
[0.8.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.8.0...0.8.1
[0.8.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.17...0.8.0
[0.7.17]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.16...0.7.17
[0.7.16]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.15...0.7.16
[0.7.15]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.14...0.7.15
[0.7.14]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.13...0.7.14
[0.7.13]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.12...0.7.13
[0.7.12]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.11...0.7.12
[0.7.11]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.10...0.7.11
[0.7.10]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.9...0.7.10
[0.7.9]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.8...0.7.9
[0.7.8]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.7...0.7.8
[0.7.7]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.6...0.7.7
[0.7.6]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.5...0.7.6
[0.7.5]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.4...0.7.5
[0.7.4]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.3...0.7.4
[0.7.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.2...0.7.3
[0.7.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.1...0.7.2
[0.7.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.7.0...0.7.1
[0.7.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.6.0...0.7.0
[0.6.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.5.0...0.6.0
[0.5.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.2.3...0.3.0
[0.2.3]: https://github.com/PolicyEngine/openfisca-uk/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/PolicyEngine/openfisca-uk/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/PolicyEngine/openfisca-uk/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/PolicyEngine/openfisca-uk/compare/0.1.0...0.2.0

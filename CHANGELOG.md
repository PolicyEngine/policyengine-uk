## [2.144.0] - 2026-10-21

### Added

- Add `pip_dl_points` and `pip_m_points` person-level inputs and points-threshold parameters under `gov.dwp.pip.{daily_living,mobility}.points_thresholds`, and derive `pip_dl_category` and `pip_m_category` from each person's latest points when the category is not provided as input. A person's category supplied for an earlier year still carries forward unless that person has points for a later year.


## [2.143.0] - 2026-10-21

### Added

- Added a PIP point system planning page (docs/book/programs/gov/dwp/pip-points-plan.md) setting out the SI 2013/377 scoring rules and a phased route to modelling them, starting from #1661.
- Added a regional childcare planning page (docs/book/programs/gov/dfe/regional-childcare-plan.md) listing the Scottish, Welsh and Northern Ireland childcare schemes not yet modelled and how to add them.
- Added a plan for modelling Cold Weather Payment and the Scottish Winter Heating Payment (#435) at `docs/book/programs/gov/dwp/cold-weather-payment-plan.md`.
- Added a plan for a rule-based Bereavement Support Payment and historical Widowed Parent's Allowance (#466, #465) at `docs/book/programs/gov/dwp/bereavement-support-plan.md`.
- Added a plan for modelling the Warm Home Discount (#502) at `docs/book/programs/gov/ofgem/warm-home-discount-plan.md`, reflecting the benefit-based eligibility in England and Wales from winter 2025-26 and the separate Scottish scheme.
- Added a page (docs/book/policy/future-date-announcements.md) on encoding announced policy changes as date-keyed parameter values, and how those dates become model-year values.
- Add a planning docs page for child maintenance (`docs/book/programs/gov/cms/child-maintenance.md`): how `maintenance_income` and `maintenance_expenses` are treated today, the gap for spousal maintenance in Universal Credit, and a route to modelling the Child Maintenance Service calculation.
- Add a documentation page (`docs/book/programs/gov/hmrc/pensions-comparison-stbm.md`) comparing PolicyEngine UK's treatment of pension contributions in income tax with the Scottish Tax-Benefit Model's source code, including a gap both share: contributions do not reduce adjusted net income for the personal allowance taper.
- Add a documentation page at `docs/book/programs/gov/hmrc/pension-tax-relief.md` explaining how PolicyEngine UK models personal pension tax relief (full marginal-rate reduction in taxable income via `pension_contributions_relief`, with separate annual-allowance excess charge via `personal_pension_contributions_tax`), and clarifying that the model correctly reports the *total* relief (both relief-at-source + higher-rate top-up combined) for the scenarios reported in #704.
- Added a plan for a reform impacts dashboard (#806) at `docs/book/validation/reform-impacts-dashboard-plan.md`, tracking the regression fixtures in `reforms_config.yaml` over model and dataset versions.
- Documented how capital gains are modelled and imputed (#818, #817) at `docs/book/assumptions/capital-gains-distribution-plan.md`, including the Microcosm UK stages that now fit gains jointly to HMRC Table 3 and what is left to do.
- Add a planning docs page (`docs/book/assumptions/non-uk-benefit-receipt-plan.md`) on benefit spending that does not reach UK private households (payments abroad, institutions, fraud and error) and how calibration targets should exclude it.
- Add a planning docs page (`docs/book/policy/indirect-tax-effects-plan.md`) on letting indirect tax revenue respond to direct tax reforms through a consumption elasticity, from a single household-level factor to per-category elasticities and a link to `consumer_incident_tax_revenue_change`.
- Documented the Ubuntu vs macOS reproducibility issue (#1209) at `docs/book/validation/ubuntu-vs-macos.md`: the import-time uprating cause, how it was resolved, and the October 2026 check that the parameter tree is byte-identical across macOS and Linux.
- Add a planning docs page for firm-level VAT (`docs/book/programs/gov/hmrc/firm-vat.md`): a proposed `Firm` entity, the registration threshold and supply split, output, input and net VAT, the data needed for a synthetic firm panel, and open questions.
- Added an effective take-up analysis plan (docs/book/assumptions/takeup-analysis-plan.md) listing each programme's take-up flag, reference parameter and current handling, where the data builds' seed rates live, and how to measure drift from them.
- Added a child poverty validation page (docs/book/validation/child-poverty-tcl.md) comparing the two-child limit removal on Microcosm UK 2024-25 (about 463,000 children lifted after housing costs, £3.26bn in 2029-30) with the DWP, Budget 2025 (OBR-certified) and Resolution Foundation estimates.
- Added a UK pipeline alignment planning page (docs/book/assumptions/uk-pipeline-alignment-plan.md): the model-side take-up gap still open, and what Microcosm UK now covers (reported-anchored take-up, the SPI stage-2 fill).
- Documented the policyengine.py household-impact zero-return diagnosis (docs/book/validation/policyengine-py-household-impact.md); the UK model returns the expected values, re-checked on 2.123.7.
- Add a planning docs page (`docs/book/assumptions/mp30k-uk-switch-plan.md`) setting out the gates and rollback path for changing the default dataset. It was written for Microplex UK and now applies to its successor, Microcosm UK.

### Fixed

- Stack capital gains on top of taxable income when splitting them between the higher and additional CGT bands, so reforms to either rate no longer give every gainer the whole higher band, and set the annual exempt amount against the gains where each pound saves most tax.
- - Northern Ireland Local Housing Allowance rates now follow new gov.dfc.LHA.freeze and gov.dfc.LHA.percentile parameters, so reforms to gov.dwp.LHA.freeze and gov.dwp.LHA.percentile change Great Britain rates only.


## [2.142.0] - 2026-10-21

### Added

- - Add `defined_benefit_pension_share`, `defined_benefit_pension_contributions` and `defined_benefit_pension_input_amount`, so data can say which workplace pension contributions go to defined-benefit arrangements and supply their statutory pension input amount (Finance Act 2004 s. 234) for the annual allowance. Where the input amount is not supplied it is those contributions times `gov.simulation.pensions.defined_benefit_input_per_contribution`, set at 1 from the accrual and contribution rates of the main public service schemes.

### Changed

- - Estimate unused annual allowance carried forward (Finance Act 2004 s. 228A) from 2020-21 where none is supplied, instead of nil: each of the five previous years' pension input is this year's times `gov.simulation.pensions.prior_year_input_ratio` (1), with incomes and input deflated by average earnings growth, against that year's tapered allowance, used earliest first (s. 228A(7)).

### Fixed

- - Use one definition of relevant UK earnings (Finance Act 2004 s. 189(2)) for pension contribution relief, the annual allowance income tests and the pension deduction in adjusted total income: employment income after allowable expenses but before pension deductions, and trading profits after capital allowances and the trading allowance but before losses brought forward. Relief previously counted pay before expenses and trading profits before capital allowances and the trading allowance.
- - Uprate water and sewerage charges by country when a dataset is projected: England and Wales by Ofwat's average bills, Scotland by a new Scottish Water series (8.8% in 2024-25, 9.9% in 2025-26 and 8.67% in 2026-27, then the CPI + 2% cap in WICS's draft 2027-33 determination), and Northern Ireland, which has no domestic water charges, not at all. The charges were previously held flat to 2030 and then grown by the England and Wales series everywhere.
- - Derive the Universal Credit benefit cap's earnings exception threshold each year from the national living wage: the pay for 16 hours a week, times 52 and divided by 12, with any fraction of a pound disregarded (Universal Credit Regulations 2013 regs. 82(1)(a) and 6(1A)(za)), and a fixed £430 a month before April 2017. It was fixed at the 2025-26 figure of £10,152 a year for every year; it is now £9,516 in 2024-25 and £10,572 in 2026-27. The national living wage parameter ends at its April 2026 rate, so the threshold stays at £10,572 in later years until that parameter is projected.


## [2.141.12] - 2026-10-21

### Fixed

- - Fixed the Carer's Allowance earnings-limit property test to count pence in the precision the model stores earnings in (float32), as the formula does, so a draw whose float32 arithmetic rounds across a penny boundary no longer fails at random.


## [2.141.11] - 2026-10-21

### Fixed

- - Indexed the annual savings starting-rate limit by September CPI from 2031–32, with statutory £10 rounding after the freeze.


## [2.141.10] - 2026-10-21

### Changed

- - Reuse Pension Credit earnings tax calculations when checking Universal Credit housing contribution exemptions.

### Fixed

- Apply the Pension Credit earnings disregards of SPC Regs 2002 Schedule VI: 20 pounds a week for lone parents, carers and claimants or partners on a listed disability benefit (including working tax credit with a disability element) or certified blind, otherwise 5 pounds (single) or 10 pounds (couple), capped at net earnings. Employed earnings are net of the income tax they add; self-employed earnings, in Pension Credit income too, are net of the notional tax and contributions of the Computation of Earnings Regulations 1996 reg. 14. The Housing Benefit savings-credit-only route now deducts only the higher Housing Benefit disregards.


## [2.141.9] - 2026-10-21

### Fixed

- Council Tax Reduction income now counts the applicant's and partner's industrial injuries disablement benefit, severe disablement allowance and incapacity benefit in every scheme (SI 2012/2885 Sch 1 para 16; SI 2012/2886 Sch paras 39 and 54; WSI 2013/3029 Sch 1 para 10 and Sch 6 para 17; SSI 2012/319 reg 27; SSI 2021/249 reg 57).


## [2.141.8] - 2026-10-21

### Changed

- Clarify domestic and overseas carbon flows and household incidence, including imported emissions in the consumption footprint and the chart's 2019 DEFRA fallback intensities.
- Use public Core operations for UK parameter initialization and dated-cache clearing while preserving parameter and reform behavior.

### Fixed

- Updated recent residential SDLT purchase schedules and applied the inclusive first-time-buyer price maximum, retaining annual sampling and contract-protection limitations.
- - Kept the pension salary-sacrifice cap in National Insurance earnings without inflating ordinary pay or member pension contributions, retained actual supplied ordinary returns in the annual-allowance calculations, and preserved the childcare income tests in #2173.


## [2.141.7] - 2026-10-21

### Fixed

- - Added the 2022–23 annual employee National Insurance schedule for explicitly declared full-year category A directors in one employment, preserving ordinary employees and other years.
- - Corrected the JSA, ESA and DLA program registry variable mappings, narrowed Benefit Cap's parameter prefix to its own subtree, removed Maternity Allowance's unrelated DWP parameter prefix, and added validation of all declared registry variables and parameter prefixes.
- - Reject data-axis aggregate-impact comparisons when either measurement omits its Python version or machine identity.


## [2.141.6] - 2026-10-20

### Fixed

- - Uprate `water_and_sewerage_charges`, `housing_service_charges` and `pension_contributions_via_salary_sacrifice`, which declared an uprating index but were absent from `uprating_indices.yaml` and so stayed flat through 2030. Also uprate twelve columns added since with the same gap, each by the index it declares: `cash_isa`, `stocks_and_shares_isa`, `mortgage_debt`, `consumer_debt`, `rent_paid_as_boarder`, `rent_paid_as_lodger`, `owned_company_capital`, `owned_company_holding_value` and `owned_company_trade_assets` (per-capita GDP) and `self_employment_gross_receipts` and `owned_company_income_share` (per-capita mixed income), plus `pension_contributions_via_salary_sacrifice_pre_2015` (average earnings). Adds a code-health test asserting that every variable declaring `uprating` appears in that file under the matching index, so the gap fails at the point it is introduced. `rail_usage` is excluded because its declared index is a cumulative level rather than a year-on-year rate, and the three energy columns because the data build already prices them (#1868). Updates Ofwat water bill growth to the published 27% for 2025-26 (was the 26% forecast) and 5.4% for 2026-27 (was a 5.5% projection), and documents the sources and vintage of the water bill and population growth series.
- - Limited the ordinary income-tax loss-cap pension uplift above earnings to relief-at-source contributions.


## [2.141.5] - 2026-10-20

### Fixed

- Means-test the Council Tax Reduction applicant and their partner rather than the benefit unit's claimant and partner, so a household head who is liable for the council tax but shares a benefit unit with a young couple is assessed on her own income, allowance, premiums and exemption.


## [2.141.4] - 2026-10-20

### Fixed

- A before-load `Scenario` change to DfE, DHSC or DfT spending now constructs: `adjust_budgets` skips a year with no allocation instead of writing NaN, and scales each year's allocation by that year's own budget change without carrying an earlier year's change forward.


## [2.141.3] - 2026-10-20

### Fixed

- - The Aggregate impact report now compares a pull request's merge commit with that commit's first parent, the tip of the branch it merges into. It used the event's `pull_request.base.sha`, which lags that branch once it moves on, so newer merges to `main` were counted as the pull request's impact.
- - Fixed Universal Credit deductions and benefit cap reductions to report what the award actually loses under a protected minimum floor, so the components sum to the reduction applied instead of over-reporting it. Where the floor binds, deductions are met first and the cap reduction absorbs the rest, however heavily the award is capped.
  - Added `uc_benefit_cap_reduction_after_floor`, the benefit cap reduction applied to a Universal Credit award after the protected floor and bounded by the award, leaving the regulation 81 amount `uc_benefit_cap_reduction` gross.
  - Fixed a protected floor above 1 adding money to Universal Credit awards, by clamping the permitted reduction at zero.
  - Fixed Universal Credit deductions applying to benefit units that do not claim Universal Credit. Deductions and the applied cap reduction use the same claim test as the award (`claims_universal_credit`), so a claim made when legacy benefits close keeps both.
  - Corrected the effective date of the 25% deductions cap to 12 April 2021, and the one-penny minimum payable citation to Schedule 6, paragraph 3(1)(a) of SI 2013/380.


## [2.141.2] - 2026-10-20

### Fixed

- - Council Tax Reduction and Income Support read their own pension contribution deduction shares (one-half in each scheme) instead of a hard-coded 0.5, and the Council Tax Reduction pensioner earnings disregards cap at net earnings with the scheme's own share, so a reform of Housing Benefit's share no longer moves them.
- - Carer's Allowance earnings read their pension contribution deduction share (one-half, Computation of Earnings Regulations 1996 regs. 10(4)(b) and 13) from a new parameter, `gov.dwp.carers_allowance.pension_contribution_deduction_rate`, instead of a hard-coded 0.5, so the share can be reformed.


## [2.141.1] - 2026-10-20

### Fixed

- Give pension-age Housing Benefit claimants who attained State Pension age on or after 1 April 2021 (and couples who both did) the lower personal allowance in SI 2006/214 Sch 3 para 1(1)(c) and (2)(c), £238.00 and £363.25 a week in 2026-27, instead of the £256.00 and £383.35 kept by earlier cohorts. England's pensioner Council Tax Reduction applies the same split (SI 2012/2885 Sch 2 para 1); Scotland and Wales keep one rate. Adds `state_pension_age_date`, the day each person attains State Pension age.


## [2.141.0] - 2026-10-20

### Fixed

- - Pension Credit income now counts industrial injuries disablement benefit, severe disablement allowance, incapacity benefit and maternity allowance (SPC Regs 2002 reg 15(1)); Savings Credit treats working tax credit, incapacity benefit, severe disablement allowance and maternity allowance as non-qualifying income (reg 9); Housing Benefit income now counts industrial injuries disablement benefit, severe disablement allowance and incapacity benefit.
- - Count war disablement pensions, war widow's or widower's pensions and Armed Forces Compensation Scheme guaranteed income payments of the claimant and partner in Pension Credit income, each payment less £10 a week (State Pension Credit Regulations 2002 Sch. IV para. 1). Housing Benefit and Council Tax Reduction continue to disregard them in full, including where they take the Pension Credit assessment of a savings-credit-only award.

### Removed

- - Removed the unused duplicate parameter `gov.dwp.pension_credit.income.savings_credit_excluded_sources`; `gov.dwp.pension_credit.savings_credit.excluded_income` is the list the model reads.


## [2.140.1] - 2026-10-20

### Fixed

- - Fixed Housing Benefit applicable income to use the configured pension contribution deduction rate, preserving the current 50% deduction.
- Preserve dataset-supplied values for variables with formulas in default input DataFrame exports, so reloading an export retains inputs such as reported State Pension. Exclude calculated caches and model-generated pseudo-inputs while retaining recorded input storage and branch precedence.
- - Based TV licence charges on licensable viewing and corrected the HBAI free-licence value.


## [2.140.0] - 2026-10-20

### Added

- Added normalized annual BHC and AHC squared poverty-gap components and documented person-weighted aggregation and undefined poverty-line handling.
- - Added a configurable Income Support withdrawal rate, preserving the existing 100% default.

### Fixed

- Use Scotland's working-age Council Tax Reduction young-person definition for the severe disability premium's non-dependant test within the applicant's benefit unit, retaining existing looked-after and other-benefit-unit treatment.
- Count Incapacity Benefit and Severe Disablement Allowance as Universal Credit unearned income from the GB transitional commencement, preserving earlier history and the existing annual-model limitations.
- Fix stale construction-time reform wrappers after foreign writes or direct edits while preserving copied scenarios and constructor readings; document mixed-composite replay, indexed-threshold construction and the existing rejection of built overrides whose keys contain no 1 January annual value.


## [2.139.5] - 2026-10-20

### Changed

- - Documented employer NI incidence assumptions, input handling, revenue measures and current household examples.

### Fixed

- - Separated Universal Credit's higher disabled child condition from tax credits, included certified blindness, and prevented the lower and higher additions from stacking.
- - Corrected Working Tax Credit eligibility so age, disability and hours conditions applied to the same claimant or partner, while preserving the parental combined-hours and partner-exception routes.
- - Restricted the Child Tax Credit family element to families responsible for a qualifying child or young person born before 6 April 2017, while preserving earlier supported years.
- - Excluded Child Benefit from Great Britain's pensioner Council Tax Reduction general-rule income, preserving working-age and statutory-pay treatment.


## [2.139.4] - 2026-10-19

### Fixed

- - Corrected dividend income-tax band thresholds from 2016 to 2025 to use their statutory tax-year dates.
- - Corrected historical Care to Learn weekly caps while preserving the existing annual date approximation.
- - Exempted non-dependants responsible for a child under five from Universal Credit housing cost contributions.
- - Applied the shared Pension Credit eligibility conditions to computed Savings Credit amounts.
- - Included statutory sick and maternity pay in the relevant earnings limits for pension contribution relief and annual-allowance income tests.


## [2.139.3] - 2026-10-19

### Fixed

- - Updated Welsh residential Land Transaction Tax tables for annual model years from 2023 (main rates) and 2025 (higher rates), retaining their statutory change dates.


## [2.139.2] - 2026-10-19

### Fixed

- - Updated the Scottish Additional Dwelling Supplement to 8% for annual model years from 2025, retaining its statutory 5 December 2024 parameter date.
- - Reduced the savings starting-rate band from the first pound of taxable non-savings income, correcting savings tax on mixed incomes.
- - Added migration directions for saved reforms using the removed couple carer premium parameter.
- - Fixed group inputs being assigned to the wrong benefit unit or household when dataset tables were not sorted by identifier.
- - Froze the Scottish higher, advanced and top income tax thresholds through 2028-29 under the announced Budget policy, with subsequent CPI projections starting from the frozen amounts.


## [2.139.1] - 2026-10-19

### Fixed

- - Corrected OBR labour supply grouping so cohabiting couples receive the same demographic coefficients as married couples.
- - Corrected the 2016-17 personal allowance to £11,000, fixing income tax calculations for that tax year.
- - Corrected Carer's Allowance earnings to deduct notional Class 2 and Class 4 National Insurance only when the carer is liable for those contributions.
- - Corrected residential property uprating and the High Value Council Tax Surcharge's 2026 valuation conversion to use the OBR house-price index.
  - Aligned projected additional-dwelling purchase prices with residential house-price growth.
  - Preserved exact 2026 surcharge-band classifications in later-year property projections without rounding household valuations.


## [2.139.0] - 2026-10-19

### Added

- Record the unused FYE 2019 joint Income Support/income-related ESA caseload take-up benchmark with its publication-date availability and sampling interval.

### Fixed

- - Count other investment income (National Savings, securities and trust interest) in `total_income`, which income tax already charges, so post-tax income and the Winter Fuel Payment income test see it. Housing Benefit and national Council Tax Reduction non-dependant deductions keep banding on income without it until the remunerative-work test is modelled (#2007) (#2174).
  - Keep the Winter Fuel Payment for a pensioner whose total income is exactly £35,000: the winter fuel payment charge applies only where total income exceeds £35,000 (ITEPA 2003 s.681I(1)(b)).


## [2.138.0] - 2026-10-19

### Added

- Document the field-specific handling of negative FRS tax, benefit and income amounts, with pinned source code and the boundary between raw survey fields and model inputs.

### Fixed

- Document parameter description conventions and validate year-zero YAML, required descriptions and malformed files without silently skipping them.


## [2.137.1] - 2026-10-19

### Changed

- - Clarified the Pension Credit qualifying-age documentation for men born on 6 November 1953, who reach it at their State Pension age of 65.
- - Documented historical Housing Benefit child personal allowance rules and their deferred implementation.

### Fixed

- - Updated England childcare entitlement valuations to the published 2025–26 and 2026–27 national-average funding rates.
- - Fixed non-finite wealth and consumption tax incidence when dataset-weighted totals were zero.


## [2.137.0] - 2026-10-19

### Added

- Compare two datasets on one model with the aggregate-impact tool: measure an unpinned built file by its SHA-256, and `compare --axis data` fails unless both sides ran the same model, runtime, partition and metric definitions.


## [2.136.1] - 2026-10-19

### Fixed

- - Fixed Universal Credit capital assessment so reported financial savings do not suppress countable property, with assessment-year sale-expense and secured-debt valuation and property allocation independent of financial reports. Retained the inherited residual financial convention, including subtraction of complete overrides from the financial pool, and company substitution after ordinary-source overrides, and documented the legacy pension-proxy limitation. Complete overrides consume their owners' disregarded company holdings once. Override floors and separate holding deductions share one household corporate-wealth budget proportionally, preventing inconsistent holdings from consuming ordinary savings. Bounded each holding before that budget to isolate negative and infinite inputs from other units' capital.


## [2.136.0] - 2026-10-18

### Added

- - Added an aggregate-impact report (`python -m policyengine_uk.utils.aggregate_impact`) that measures a model checkout on the pinned certified dataset and compares base with head: receipts by tax head, spending and caseloads, poverty, inequality, deciles and the standard reform costings over 2025-26 to 2031-32, with accounting identities and a counted-once check against a reviewed fiscal partition (`policyengine_uk/data/fiscal_partition.yaml`).

### Changed

- - Microsimulation tests now run on the certified uk-data 1.58.1 dataset, pinned by commit and SHA-256, and fail instead of skipping when `POLICYENGINE_UK_REQUIRE_TEST_DATA` is set and the data is unavailable; the reform-cost fixtures are rebased onto it, keeping their earlier values as receipts.


## [2.135.7] - 2026-10-18

### Changed

- Split the undated VAT grossing factor `gov.simulation.microdata_vat_coverage` (0.38) into two documented factors: `gov.simulation.vat.household_share_of_receipts` (0.7, HMRC's share of VAT liabilities on household consumption) and `gov.simulation.vat.survey_consumption_coverage` (0.67, derived on Microcosm UK 2024-25 against OBR VAT receipts). Total VAT on that dataset now matches 2024-25 receipts instead of overshooting by 24%. `microdata_vat_coverage` is kept as a deprecated parameter equal to their product (0.469); a reform that sets it to another value still takes effect.

### Fixed

- - Add `war_widows_pension_reported` (CPI-uprated) and `war_widows_pension`, counted wherever `bsp` is, so datasets can move FRS benefit code 9 (War Widow's or Widower's Pension) out of `bsp_reported`. Bereavement Support Payment rates have been frozen since April 2017, but `bsp_reported` is about 90% war widow's pension in FRS 2024-25, so it keeps CPI uprating until the datasets split the two (#2381). Results are unchanged for existing datasets.


## [2.135.6] - 2026-10-17

### Fixed

- - Corrected the pension annual allowance taper to use separate threshold and adjusted income tests, including employer pension inputs, full salary sacrifice before the NICs exemption cap and gross pension relief. Applied whole-pound rounding and the statutory limits from 2016–17 onwards.
  - Removed the NICs-only salary-sacrifice reclassification from the taper income tests, including post-75 and basic relief-at-source cases.
  - Excluded member contributions made at 75 or over from the default DC pension input while retaining all employer contributions and salary sacrifice.
  - Recomputed income-dependent trading-loss relief from actual income for both annual allowance income tests, including the general-income and relief-cap limits.
  - Limited trading-loss relief after relievable net-pay contributions in every year and kept supplied adjusted-net-income inputs independent of the NICs cap.
  - Restricted the basic pension-relief uplift above earnings to relief at source when rebuilding the annual allowance trading-loss cap.


## [2.135.5] - 2026-10-17

### Fixed

- - A clone or branch that applies a reform now links the tax-benefit system to itself while it does, so a reform that sets inputs, such as `disable_simulated_benefits`, sets the clone's or branch's inputs and never its parent's. A reform applied after the simulation is built (one passed as `reform=`, or applied to a built simulation, clone or branch) now keeps through `reset_calculations` (and, before policyengine-core 3.33.0, `derivative`) every input it stores and leaves in place, however it stores it, including one that replaces an input set since the build; an input set since the build that the reform did not store is still reset, as before, unless the reform stores an input of the same variable (a reset keeps or clears whole variables).
  - Under `disable_simulated_benefits`, set the claimant's and partner's income-related ESA and income-based JSA (`claimant_or_partner_esa_income`, `claimant_or_partner_jsa_income`) for each year from the dataset-year reports of whoever is the claimant or partner that year, and set Income Support from their reports alone. The reform holds each benefit at its dataset-year amount while the reported amounts are uprated, so in a later year the stored award matched neither reading of the reports and another member's award was taken to be the claimant's. Another member's own Income Support report is left out of household income, as it is with the reform off, where Income Support is calculated only for the claimant's family.
  - Under `disable_simulated_benefits`, no family is moved off its legacy benefits: the reform holds `legacy_benefits_closed` false for its ten years, since it pays every reported legacy award and Universal Credit in every year. So, after the closure of income-based JSA and Income Support from April 2026, an adult outside the couple is still on the income-related ESA the reform pays them, and the closure ends no family's Housing Benefit or tax credit eligibility and prompts no Universal Credit claim. Only the closure is held: the model's other rules still apply, though the reform pays the amounts reported. So a family the model has claim Universal Credit anyway is still not eligible for Housing Benefit or tax credits, and an adult outside the couple is on the income-based JSA they report, as their own claim, only in the years the model has the scheme open (to 2025); the claimant and partner are on the award the reform holds for them.
  - Under `disable_simulated_benefits`, count a Scottish carer's reported Carer's Allowance once. The reform set `carers_allowance` from the report in every country and left `carer_support_payment` simulated, so from 2025, when the model pays a carer in Scotland Carer Support Payment in place of Carer's Allowance, a Scottish carer was paid both. Now, as with the winter heating payments, in each year the report is the `carer_support_payment` of a carer living in Scotland that year, from 2025, and their `carers_allowance` before then, and everyone else's `carers_allowance`; neither benefit is simulated beside it. The entitlements before the overlapping-benefit reduction stay the model's for both. This split and the winter heating one read where the household lives in each year, as the model does, when the reform is applied, so a household that moves into or out of Scotland is paid under that year's scheme: before, both read the dataset year's country, so a carer who moved to Scotland was paid Carer's Allowance and lost the Scottish Carer Supplement.
  - Neutralizing `esa_income` or `jsa_income` also neutralizes the claimant's and partner's award, so an award entered for them, or set by the reform, no longer outlives the benefit it is part of.
  - Read the claimant's and partner's income-related ESA and income-based JSA in the benefit cap (its total of welfare benefits, and the ESA support component exemptions from both the Universal Credit and Housing Benefit caps) from `claimant_or_partner_esa_income` and `claimant_or_partner_jsa_income` wherever the cap's couple is the claimant and partner. Under `disable_simulated_benefits` the cap read an award held for another member of the benefit unit (a non-dependent adult claiming in their own right) as the couple's in every year after the dataset year, so it raised the cap's total and could exempt a claimant with a support component who receives no ESA. An award entered for those variables directly now reaches the cap too, and an award within half a penny of zero is no award there, as elsewhere. A Universal Credit couple that is not the claimant and partner (only with `is_uc_claimant` or `is_uc_assessed_claimant` entered, or more than two members entered as claimant or partner) is still read from `esa_income` and `jsa_income` by value.
  - Read the claimant's and partner's income-related ESA and income-based JSA in `income_support_eligible` from `claimant_or_partner_esa_income` and `claimant_or_partner_jsa_income`, as the means tests and passports do, so an award entered for them directly, or set by the reform, is read the same way everywhere. The two variables share one formula, which now treats an award within half a penny of zero as no award, as `income_support_eligible` did, so the float residual left by reports that exactly match the tariff income is no longer the claimant's or partner's award, and no passport or status that reads their award counts it. A member outside the couple is still on their own award as before: it is read from their own report, without that rule. When `esa_income` or `jsa_income` holds the plain total of the reported awards, Income Support now reads the plain total of the claimant's and partner's reports, as the two variables already did; it used to read their award after the capital test.


## [2.135.4] - 2026-10-17

### Changed

- - Tests cover more release manifests that pypi-state must refuse (a missing, repeated or unreadable entry), the manifest check-dist writes being the one pypi-state reads, and agreement with a clean dist under every --require state.


## [2.135.3] - 2026-10-17

### Fixed

- - Fixed standalone dated-reform modifiers silently dropping parameter changes, warned when UC rebalancing supersedes an LCWRA amount reform, and restored new-claimant draws for data-built core simulations.
  - Preserved standalone modifier order across repeated and reordered reforms and retained no-op behavior for already-effective reforms on copies.
  - Deferred LCWRA override warnings until standalone tuple and sum modifiers finish, with one warning per amount-reform application.
  - Preserved callback-only Scenario.apply compatibility for lightweight simulation objects without a tax-benefit system.
  - Replayed mixed statutory and legacy modifiers in their requested order, restricting composite no-ops to exact latest write sequences with current values.


## [2.135.2] - 2026-10-17

### Fixed

- - The release workflow's PyPI checks compare PyPI with the manifest of the files it built and tested, written before publishing, so the attestation files trusted publishing adds to dist no longer fail the release after upload, and releases are tagged and announced to policyengine.py again.


## [2.135.1] - 2026-10-17

### Fixed

- - Pay no Pension Credit child amount (SPC Regs 2002 Schedule IIA) to a family awarded child tax credit or working tax credit, including an award at a nil rate (reg 6(6)(d) and (11); TCA 2002 s.14(3)). The new variable `has_tax_credit_award` records the award.
  - Pay no Schedule IIA amount before it began on 1 February 2019 (SI 2018/676 reg 2). The new parameter `gov.dwp.pension_credit.guarantee_credit.child.in_effect` dates it.


## [2.135.0] - 2026-10-17

### Added

- Per-scheme benefit cap variables (`uc_benefit_cap`, `is_uc_benefit_cap_single_claimant_rate`, `is_uc_benefit_cap_exempt`, `is_uc_benefit_cap_exempt_earnings`, `is_uc_benefit_cap_exempt_specified_benefit`, `is_uc_benefit_cap_exempt_qualifying_age`, `uc_benefit_cap_reduction`; `housing_benefit_benefit_cap`, `is_housing_benefit_benefit_cap_single_claimant_rate`, `is_housing_benefit_benefit_cap_exempt`, `is_housing_benefit_benefit_cap_exempt_working_tax_credit`, `is_housing_benefit_benefit_cap_exempt_specified_benefit`, `housing_benefit_benefit_cap_reduction`; `benefit_cap_welfare_benefits`), with the parameter `gov.dwp.housing_benefit.minimum_weekly_amount`.

### Fixed

- Universal Credit and Housing Benefit each apply their own benefit cap. The UC cap (UC Regs 2013 regs 79-83) treats a member of a couple claiming as a single person (reg 3(3)) as a single claimant, lifts the cap for earnings and the LCWRA and carer elements but not for working tax credit, lifts it on age only where the single claimant or both joint claimants have reached the qualifying age for State Pension Credit (SI 2014/1230 reg 60C), and takes the childcare costs element off the reduction (reg 81). The HB cap (HB Regs 2006 Part 8A) treats that couple as a couple, lifts the cap for working tax credit and the benefits in reg 75F (the partner's included) but not for earnings or UC elements, does not reach pension-age claims (reg 5), and leaves at least 50 pence a week of HB (reg 75D(2)). A family paid both (Housing Benefit for specified or temporary accommodation alongside UC, which the model gives only when both are supplied) is capped once, through UC: UC counts the Housing Benefit as nil (reg 80(2A)) and the HB cap does not apply to a claimant receiving UC (reg 75F(1)(g)). The UC shared accommodation test (`is_lha_shared_accommodation_rate_specified_renter`, UC Sch 4 paras 27-29) applies reg 3(3) whatever legacy benefits the family reports, and armed forces independence payment now excepts a renter under 35 from it (UC reg 2). Armed forces independence payment lifts the UC cap only when a claimant receives it (UC reg 83(1)(c) with reg 2), no longer when a young person does, and lifts the HB cap when the claimant, the partner or a young person they are responsible for receives it (HB reg 75F(1)(ea)). The shared-rules stopgap for reg 3(3) single claims (`stays_on_legacy_benefits` and the two helpers built on it) is gone.

### Removed

- The shared benefit cap variables `benefit_cap`, `is_benefit_cap_exempt`, `is_benefit_cap_exempt_earnings`, `is_benefit_cap_exempt_health_disability`, `is_benefit_cap_exempt_other` and `is_benefit_cap_single_claimant_rate`, replaced by each scheme's own. `benefit_cap_reduction` remains as the sum of the Universal Credit and Housing Benefit reductions.


## [2.134.9] - 2026-10-16

### Fixed

- - After a dated reform to the personal allowance or the basic rate limit (indexed by ITA 2007 ss57 and 21) or to the NICs secondary threshold ends, indexation now resumes from the changed amount, as it does after the Finance Act 2021 freeze. The NICs thresholds aligned with the allowance and limit follow them, and one changed on its own is aligned again afterwards. Uprated amounts such as benefit rates still return to their uprated path.


## [2.134.8] - 2026-10-16

### Fixed

- - Deducted relieved pension contributions from adjusted net income so that the Personal Allowance taper and High Income Child Benefit Charge reflect pension relief, while retaining a single deduction from the income tax base and restoring pension relief consistently for supplied ANI in the marriage-neutral reform.


## [2.134.7] - 2026-10-16

### Fixed

- - A dated reform starting exactly on a parameter's first stated date no longer has its value backdated to the years before it.


## [2.134.6] - 2026-10-16

### Fixed

- - Applied the Universal Credit Act 2025 standard allowance uplifts for 2027-28 to 2029-30 through a dedicated uprating index under `gov.economic_assumptions.indices`, including when dated reforms rebuild parameters, while preserving the legislated 2026-27 rates.


## [2.134.5] - 2026-10-16

### Fixed

- - Limited pension contributions relief by relevant UK earnings (or the £3,600 basic amount through relief at source) instead of the annual allowance. Calculated the annual allowance charge across UK or Scottish tax bands with unused allowance carried forward, applying the statutory named-rate ordinary-income condition to the RAS band extension and preserving Gift Aid's separate gross band extension. Separate savings and UK property rates do not establish RAS eligibility.


## [2.134.4] - 2026-10-16

### Fixed

- - From 2030-31, keep paying pre-2026 (protected) Universal Credit LCWRA claimants the protected amount, uprated from its 2029-30 level by the LCWRA element's uprating index, and new claimants the new-claimant amount. The rebalancing scenario used to stop in 2029-30, so every claimant fell to the new-claimant amount (a protected claimant from £457.15 to £235.86 a month). The new-claimant share is now the parameter `gov.dwp.universal_credit.rebalancing.new_claimant_share`, held at 22% after 2029-30.


## [2.134.3] - 2026-10-16

### Fixed

- - Corrected the Scottish 48% top-rate threshold to £125,140 of taxable income for 2024–25, 2025–26 and 2026–27, accounting for the fully withdrawn personal allowance.


## [2.134.2] - 2026-10-15

### Fixed

- - Hold the Universal Credit LCWRA element at £217.26 a month for 2026-27 to 2029-30, as Universal Credit Act 2025 s. 3 freezes it, and uprate it from that amount by the benefit uprating index from 2030-31. It was CPI-uprated from 2027-28. The freeze is `gov.dwp.universal_credit.rebalancing.health_element_freeze` and applies while the rebalancing reforms are active. The amount the rebalancing scenario pays new claimants (`rebalancing.new_claimant_health_element`) follows the same path, so lifting the freeze reaches them.


## [2.134.1] - 2026-10-15

### Fixed

- Stop charging a household's whole stock of other residential and non-residential property as a purchase whenever it buys its main residence. `property_purchased` now sets only the main-residence purchase; `additional_residential_property_purchased` (the price of one additional dwelling, charged at the higher rates for additional dwellings) and `non_residential_property_purchased` are inputs, nil unless set directly or imputed by a dataset, and are uprated like the property stocks when a dataset supplies them.


## [2.134.0] - 2026-10-15

### Added

- - Added `capital_gains_response_assumption` (`policyengine_uk.utils.capital_gains`), which reports the capital gains realisation response a simulation applies in a year (the convention, each elasticity and where it came from), and `CapitalGainsResponseWarning`, issued when an `mtr_elasticity` applies in place of the retention-rate default.

### Changed

- - Made a retention-rate elasticity of 1.0 the default capital gains realisation response (`gov.simulation.capital_gains_responses.elasticity`, previously 0), the central value Advani, Lonsdale and Summers (2024, pp. 36-37) use for the medium-term effect of a package that also broadens the base, with 0.5 and 2.0 as sensitivities. For a rate change alone their reasoning points to a higher value, and responses in the first year can be larger, so the default can overstate what a rate rise raises; for a large rise it can even give the opposite sign to official costings. CGT reforms are no longer costed statically unless the elasticity is set to 0, and gains qualifying for Business Asset Disposal Relief take the same 1.0. Reforms to income tax bands and allowances also move realised gains, by changing the rate gains are taxed at, so costings that include CGT move too. Household net income counts gains no longer realised as income lost, so household and distributional results for these reforms change as well as revenue. An `mtr_elasticity` set while the retention-rate settings keep their defaults now applies alone in its periods, with a `CapitalGainsResponseWarning`; retention-rate settings changed to nonzero values still raise alongside it. Simulations that apply their baseline's rules (any simulation without a reform, and a reform's own baseline) and populations without gains no longer measure marginal rates on gains, and marginal tax rates on earnings hold realised gains fixed instead of measuring the response again at the higher pay. `marginal_tax_rate_on_capital_gains` now measures the rise in capital gains tax rather than the fall in household net income, which gives the same rate at about a sixth of the cost.


## [2.133.0] - 2026-10-15

### Added

- - Added `policyengine_uk.utils.measurement_branches`: `measurement_branch`, which measures a simulation's results at set inputs in a branch with every behavioural response switched off, and `held_behavioural_responses` and `hold_behavioural_responses`, which hold the responses fixed in a branch that steps an input to measure a marginal rate.

### Fixed

- - Measured the elasticity-based labour supply responses against the reform's baseline simulation rather than a copy of the reform, so a reform that changes marginal rates or net income now gets a response when `gov.simulation.labour_supply_responses` elasticities are set. The labour supply and capital gains measurements now start from what their simulation was given, not what it had already calculated, and hold every behavioural response at zero, so neither response depends on what was calculated first or includes the other. Marginal tax rates (on earnings, on employer cost and on capital gains) hold every behavioural response at the simulation's values in the branches where they step an input, instead of measuring the responses again there. A branch that shares its simulation's rules, such as the Pension Credit branch of the UC non-dependant exemption, takes the simulation's labour supply response instead of measuring it again, and a labour supply term whose elasticity is zero is zero without a measurement.


## [2.132.6] - 2026-10-15

### Fixed

- `Scenario.apply` on a built simulation now changes the parameter a deprecated `labor_supply_responses` path copies, as constructing the simulation with the scenario does; it used to edit only the alias copy, which formulas do not read, unless the scenario had been summed.


## [2.132.5] - 2026-10-15

### Fixed

- - Fixed loading local multi-year H5 datasets saved by `UKMultiYearDataset.save` by distinguishing yearly groups from single-year pandas tables.


## [2.132.4] - 2026-10-15

### Fixed

- - HBAI household net income before housing costs now resets a negative figure to zero, as HBAI does; income after housing costs, deciles, poverty flags and poverty gaps follow from the reset figure. Poverty headcounts do not change while both person-weighted BHC and AHC median incomes are positive (as on the enhanced FRS); poverty gaps fall and income totals rise by the sum of the negative incomes. Households whose income is reset now count in the bottom income decile instead of being left out with decile -1, as long as households at zero hold at most a tenth of people, so bottom-decile figures move. The figure before the reset is the new `hbai_household_net_income_before_reset_to_zero`, which the labour supply responses use, so they are unchanged.


## [2.132.3] - 2026-10-15

### Fixed

- Dataset caching no longer couples a macro scenario to other simulations: a scenario built first left its projected incomes for its own baseline and every later simulation from the same `hf://` or `gs://` dataset, and one built after a baseline got current law's data. Dated parameter changes that change what the dataset projection reads, such as a reform dict setting an OBR growth rate for a year, are now written before the data is built, so incomes, rents and council tax follow them.


## [2.132.2] - 2026-10-15

### Changed

- - Added Winter Fuel Payment and Pension Age Winter Heating Payment tests for couples on Income Support, income-based jobseeker's allowance and income-related employment and support allowance: couples of pensionable age, who get one payment, and couples whose claimant is under pensionable age, in the 2024 and 2025 qualifying weeks.


## [2.132.1] - 2026-10-14

### Fixed

- - Removed the projection-horizon job's working notes (`REPORT.md` and `PROGRESS.md`), committed to the repository root by mistake with #2376, and made Lint fail when agent working notes are committed there.


## [2.132.0] - 2026-10-14

### Fixed

- - A sum of scenarios keeps the timing of each part's modifier. A part applied before data load, such as `no_economic_assumptions`, is still applied before it when added to a reform, so `no_economic_assumptions + reform` freezes the data as well as the parameters. Likewise a macro scenario applied before data load, plus a reform, projects the data with the macro growth. Modifiers of parts applied after data load, including ones that edit the data, still run after it. A sum with a part applied before data load applies all of its parameter changes first, as `+` merges them, so the data follows them all and a modifier's edits survive. A simulation with a scenario applied before data load no longer reads or writes the `hf://` and `gs://` dataset cache, so its projection no longer reaches its baseline or later simulations. The sum of scenarios that are all applied before data load is now applied before it. A sum now calls the modifiers its operands had when it was made. Its fields still hold the whole sum, and `Scenario.parts_by_data_load()` returns what is applied before and after data load.

### Removed

- - Removed `gov.simulation.labour_supply_responses.obr_elasticities` and its legacy alias `gov.simulation.labor_supply_responses.obr_elasticities`. Nothing read this switch, so setting it changed no output. A reform or saved policy that still names it now fails with directions to `gov.dynamic.obr_labour_supply_assumptions`, the switch under which `Simulation.apply_dynamics` applies the OBR labour supply elasticities.


## [2.131.2] - 2026-10-14

### Fixed

- - Fixed HBAI household income after housing costs to deduct ground rent and housing service charges, so equivalised AHC income and poverty measures include these costs.


## [2.131.1] - 2026-10-14

### Fixed

- A bare-year reform key, or a key dated 1 January, on the economic growth rates, the indices built from them and the household parameters now names that calendar year. A bare year used to name the fiscal year from 6 April, which moved the next year: a 2027 earnings growth rate showed as 2027's but moved the 2028 index and the April 2029 triple lock. A 1 January key used to override that one day after processing, which nothing built from the parameter read. A change to an uprated household parameter past its last stated value now leaves the years around it on their projected path instead of freezing them. Reforms to series built during processing (the triple lock rate, the indices, the lagged series) now uprate what is built from them. Deprecated `labor_supply_responses` paths in reform dicts reach the parameters formulas read, and changes to a parameter given by both its path and its alias are merged in order instead of one being silently dropped.


## [2.131.0] - 2026-10-14

### Added

- - Added Income Tax trade loss relief against general income under ITA 2007 s.64, subject to available net income and the s.24A relief cap.

### Changed

- - Uprated trading losses separately from profits, applied programme-specific UC and tax-credit income rules, and included losses as negative market and HBAI income. Income Tax carry-forward now uses only explicitly supplied unrelieved losses; Class 4 retains its separate automatic loss history.
  - Coordinated the taxpayer's trading allowance election with current-year Income Tax and Class 4 loss relief, retaining whichever gives the greater current-year income deduction.

### Fixed

- - Base the trading allowance election on losses supplied for that tax year, preserving earlier Class 4 loss balances when later loss inputs are unset.
- - Fixed Universal Credit trading-loss netting to include company trade results.


## [2.130.1] - 2026-10-14

### Fixed

- - Fixed the benefit-cap earnings exemption to count statutory pay and use Universal Credit's actual net earnings before the minimum income floor, with a pinned regression for the release failure.


## [2.130.0] - 2026-10-13

### Added

- - Universal Credit now applies regulation 77 to a person who stands as sole owner or partner of a company carrying on a trade or property business.
    - A trading company's income counts as their self-employed earnings on top of any pay from it. A company loss is set against the profit of any trade they carry on themselves, the tax and National Insurance on their trades come off that total, and a negative result counts as nil, so neither a loss nor the tax on a trade it cancels comes off their pay.
    - Only a claimant's or partner's company earnings reduce the award.
    - The minimum income floor applies when the trade is their main employment.
    - The company's capital replaces the value of their shares. Trade assets are disregarded while they work in the trade. In households with several benefit units, the shares leave the household's capital before it is shared out, including a dependant's, which count for nobody.
    - The intermediaries (IR35) exclusion follows reg. 77(5) as in force: Chapters 8 and 9 of ITEPA Part 2 until 27 November 2018, and Chapters 8 to 10 from main-employment activities from 28 November 2018. Annual simulations take the rule in force at the start of the year, so 2018 uses the earlier rule throughout.
    - New `owned_company_*` inputs describe the company. Every input defaults to no such company, so existing datasets are unchanged.
- - Added explicit, versioned capital-gains projection scenarios shared by dataset and household simulations, with population adjustments, bounded years, errors for direct reforms to generated paths and an experimental OBR EOT sensitivity.
  - Added per-variable and period application provenance distinguishing supplied inputs, applied projections and defaults, an explicit supplied-input flag, and a warning when supplied future gains bypass an explicitly selected projection, including annual inputs read by monthly calculations. Population rebuilds reset this provenance.
  - Added an experimental marker to projection metadata and cache fingerprints, set for the bundled OBR EOT sensitivity without changing its growth assumptions.


## [2.129.1] - 2026-10-13

### Fixed

- - End a reported income-related ESA award when the claimant is engaged in remunerative work or the partner is (Welfare Reform Act 2007 Sch 1 para 6(1)(e), (f)). For the claimant that is any paid work other than exempt work (ESA Regs 2008 reg 41(1)): work with earnings of no more than £20 a week, or of under 16 hours a week with earnings within 16 times the National Minimum Wage rounded up to the next 50p (£195.50 in 2025-26, £203.50 in 2026-27; reg 45(2), (4), (9A)). Earnings (new `esa_exempt_work_earnings`) are pay less PAYE and primary Class 1 on the pay alone and half the pension contributions (reg 96(3)), with statutory sick, maternity and paternity pay, which are not earnings (reg 95(2)(b)), adding neither to the pay nor to the tax and Class 1 taken off it, plus a self-employed profit less reg 99's notional basic-rate tax above the personal and blind person's allowances, main-rate Class 4 on the profit itself (reg 99(4)'s chargeable income, before capital allowances, the trading allowance and loss relief; reg 98(5)), Class 2 until 5 April 2024 (reg 99(3)(a); new `gov.dwp.ESA.income.self_employment_class_2.{deducted, above_lower_profits_threshold}`) and half the personal pension contributions (reg 98(3)), with no loss set against pay (reg 98(11)). The claimant's test is the new `esa_income_claimant_remunerative_work`. For the partner it is 24 hours a week or more (reg 42(1)), except for a carer (reg 43(2)(c)); hours come from the new `esa_income_remunerative_work_hours`.
  - End a reported income-based JSA award when the claimant works 16 hours a week or more (Jobseekers Act 1995 s.1(2)(e); JSA Regs 1996 reg 51(1)(a)) or the partner works 24 or more (s.3(1)(e); reg 51(1)(b)). A member of a joint-claim couple whose partner works 16 to under 24 hours can claim alone (reg 3E(2)(g)), so 24 hours is the limit for the other member of any couple. The JSA regulations have no exception for carers doing unrelated paid work. Hours come from the new `jsa_remunerative_work_hours`.
  - The claimant is a member who reports the award; when the claimant or partner reports one, only they are tested, so a non-dependant's award never changes theirs, other than through the legacy closure (`legacy_benefits_closed`), which reads every member's reports. The Income Support gate reads the screened awards. A member outside the couple, such as a non-dependent adult, claims in their own right, so `is_on_income_related_esa` and `is_on_income_based_jsa` test their own claim on their own work (the ESA claimant's exempt work limits, or JSA's 16 hours) as well as their report, tariff income and the capital limit: a working one's own report no longer exempts them from a council tax reduction non-dependant deduction, and a non-working one stays on their award when the claimant's own claim fails, though not once the family's legacy benefits have closed (`legacy_benefits_closed`), which the model applies to every member's award (a simplification: SI 2014/1230 reg 46(1) ends only the claimant's and partner's). New parameters `gov.dwp.ESA.exempt_work.{lower_earnings_limit, hours_limit, higher_earnings_limit}`, `gov.dwp.ESA.income.remunerative_work.partner_hours` and `gov.dwp.JSA.remunerative_work.{claimant_hours, partner_hours}`; the descriptions of `gov.dwp.JSA.hours.single` and `couple` now say what reg 51 sets.


## [2.129.0] - 2026-10-13

### Added

- - Add `esa_includes_support_component`: whether a person's employment and support allowance includes the support component. Datasets and users can supply it; otherwise it is assumed for anyone with an ESA award of their own. Household calculations with ESA outside the support group should set it to false.
  - Add `has_own_esa_award`: whether a person claims ESA themselves (a reported award, or a directly entered income-related award attributed to the claimant who heads the benefit unit).
  - Add `uc_limited_capability_for_work`: limited capability for work, for the Universal Credit work allowance, reduced minimum age, work preparation group and the partner's exception to the childcare work condition.

### Fixed

- - Lift the benefit cap for employment and support allowance only where the claimant's or partner's allowance includes the support component (HB Regs 2006 reg 75F(1)(a); UC Regs 2013 reg 83(1)(a)), for contributory and income-related ESA alike. Any income-related ESA, and any member's contributory ESA, used to lift it. Without other information the support component is assumed for a person with their own allowance, as for about nine in ten ESA recipients in the Family Resources Survey.
  - Lift the benefit cap for a disability or carer benefit only when the person the regulations name receives it: the claimant or partner for attendance allowance, industrial injuries benefit and armed forces compensation; also a child or young person they are responsible for, for disability living allowance; also a young person, for personal independence payment, Carer's Allowance and Carer Support Payment, and a Housing Benefit young person for armed forces independence payment. A 16-year-old who receives benefits in their own right or is looked after is not a young person here. The Universal Credit LCWRA and carer exceptions now need the element in the award: an element entered directly, or given by a reform's formula, lifts the cap when positive whatever the members' circumstances, and the element the model calculates lifts it unless only members who are not claimants have limited capability or caring responsibilities. This holds in 2026-2029 too: the Universal Credit rebalancing's rescaled LCWRA element is the model's own, not an entered one (`utils/supplied_inputs.set_model_value`). A partner who cannot be a joint claimant (UC Regs 2013 reg 3(3)) lifts no cap with their own benefits. For a family on Universal Credit the claimant and partner are the award's claimants (`is_uc_assessed_claimant`), otherwise Housing Benefit's claimant and partner; the two are the same unless `is_uc_claimant` is entered. A non-dependent adult's disability and carer benefits, ESA, disability flag and caring no longer lift the family's cap.
  - Count armed forces independence payment towards the benefit cap exception.
  - Take a person whose own ESA lacks the support component not to have limited capability for work-related activity (`uc_limited_capability_for_WRA`), whatever their disability flag, since that determination is what gives ESA the support component and Universal Credit takes it (UC Regs 2013 reg 40(1)(a)(ii)). Datasets flag every ESA recipient as disabled and the support component is assumed, so this changes nothing in the data until a dataset reports the ESA group.
  - Give the Universal Credit work allowance and reduced minimum age their own limited capability for work test (`uc_limited_capability_for_work`, UC Regs 2013 regs 8(1)(a), 22, 39): limited capability for work-related activity or the disability flag, so an ESA recipient outside the support group keeps both. The work preparation group (Welfare Reform Act 2012 s.21(1)(a)) and the partner's exception to the childcare work condition (UC Regs 2013 reg 32(1)(b)(i)) read it too, so a claimant flagged as disabled without limited capability for work-related activity is in the work preparation group, outside the minimum income floor, and as a partner still lets a working claimant meet the childcare work condition.
  - Count in the benefit cap only the welfare benefits the claimant or couple is entitled to (UC Regs 2013 reg 80(1); HB Regs 2006 reg 75A): the claimant's and partner's contributory ESA, JSA, incapacity benefit and SDA, their income-related ESA and income-based JSA (`claimant_or_partner_esa_income`, `claimant_or_partner_jsa_income`), and the family's Child Benefit, CTC, Income Support, Universal Credit and Housing Benefit. For a family on Universal Credit the couple is the award's claimants, including the other member of a couple where one member claims as a single person (UC Regs 2013 reg 78(2)); otherwise it is the claimant and partner. Another member's own award no longer reduces the family's Universal Credit or Housing Benefit; it still counts in household income.
  - Give the benefit cap's single or couple limit by the award's claimants where the claimants of a family on Universal Credit are entered (`is_uc_claimant`) and are not Housing Benefit's claimant and partner (UC Regs 2013 reg 80A); otherwise `is_couple` decides, as before.
- - Count only the parent's and partner's own income-related ESA in the extended childcare parent and partner conditions (SI 2022/1134 regs 11A(1)(e), 14(4) and 15(4)): another member of the benefit unit with an award of their own no longer lets a non-working parent or partner meet them.
  - Add tests that the choice between the working-age and pension-age Housing Benefit regulations (HB Regs 2006 reg 5(1)(b)) reads only the claimant's and partner's Income Support, income-based JSA and income-related ESA, as it already does.
  - Add tests that the mixed-age couple Pension Credit saving (SI 2019/37) reads only the couple's own Income Support, JSA and ESA reports, as it already does.

### Removed

- - Remove the unused benefit sums from `is_benefit_cap_exempt_earnings` and `is_benefit_cap_exempt_other`; the earnings and age exceptions keep their results and the armed forces and ESA exceptions move, limited to the claimant and partner, into `is_benefit_cap_exempt_health_disability`.
  - Remove the input `uc_has_limited_capability_for_work`. The work preparation group reads `uc_limited_capability_for_work`, which datasets and users can set instead.


## [2.128.3] - 2026-10-13

### Fixed

- - Count the Pension Age Winter Heating Payment (`pawhp`) in `household_benefits`, `hbai_household_net_income` and `hbai_benefits`, as the Winter Fuel Payment is. It was in `gov_spending` only, so Scottish pensioners' winter heating payment was missing from household net income and HBAI income from the 2024 qualifying week.
  - Make `gov.contrib.policyengine.disable_simulated_benefits` run. `Simulation` now sets `tax_benefit_system.simulation`, through which structural reforms reach the simulation, and the reform no longer names reported amounts that do not exist (Attendance Allowance, DLA and PIP follow the reported award through their categories).
  - Under `disable_simulated_benefits`, count the reported winter heating payment once: as `pawhp` for a household in Scotland in the years PAWHP is paid, and as `winter_fuel_allowance` otherwise.


## [2.128.2] - 2026-10-13

### Fixed

- - Lift the tax credit income test for a claimant or couple entitled to State Pension Credit, guarantee credit or savings credit (TCA 2002 s.7(2); SI 2002/2008 reg 4(1)(d)). Working tax credit is Pension Credit income (SPCA 2002 s.15(1)(b)), so the passport applies where Pension Credit is payable with the passported award counted as income. The new parameter `gov.dwp.tax_credits.means_test.pension_credit_passport` dates the rule from 26 November 2003.
  - Add `tax_credits_current_year_income`, the tax credit income before the passport (TCA 2002 s.7(4); SI 2002/2006 reg 3). `tax_credits_applicable_income` is that income, or nil while the test is lifted. The targeted childcare tax credit criteria now test the gross income against the £16,190 limit (SI 2014/2147 reg 1(2)), not the nil income of a passported award.


## [2.128.1] - 2026-10-12

### Fixed

- - UC deduction draws now apply to every simulation built from data, including a constituency or local authority filtered from the national data, instead of only those carrying over a million benefit units of weight. Simulations rebuilt in place, and policyengine-core simulations built over the UK system from data, count as data too. Household situations never get imputed UC deductions or private school attendance, whatever their weight. `filter_dataset` carries each person's private school attendance into the household it extracts. Private school attendance is still imputed only for data carrying at least a million people of weight, until the data carries a national income rank.
- - Keep the universal and targeted childcare hours when a family becomes eligible for the extended (working parent) entitlement, and value the extended entitlement as each child's working parent hours above them (Childcare Act 2016 s.1(6)). A family whose hours cap is under 15 a week no longer loses funded hours by becoming eligible, and `is_child_receiving_extended_childcare` now counts each child on its own working parent hours.
  - Allocate participating children's first funded hours to the legally applicable universal or targeted programme even when standalone take-up is false, preserving total support and counting only the remaining hours as extended childcare.


## [2.128.0] - 2026-10-12

### Added

- - Move families onto Universal Credit when DWP closes a legacy benefit they receive: tax credits from 2025-26, Income Support and income-based JSA from 2026-27. Families on Pension Credit, and families on Child Tax Credit only that meet the Pension Credit age conditions, go to Pension Credit instead (SI 2019/167 art. 3A). Pension-age families on Working Tax Credit can claim Universal Credit with the upper age condition waived (SI 2014/1230 reg 60A), and protected mixed-age couples on it can claim jointly (UC Regulations 2013 reg 3(2)(a)); either leaves the pension-age route only by claiming and having positive Universal Credit entitlement before the benefit cap and deductions. A new dataset input, `would_claim_uc_at_legacy_closure` (default true), says whether the family claims. `claims_universal_credit` replaces `would_claim_uc` wherever the model asks whether a family claims Universal Credit, including whose claim counts a household's non-dependants. The family's other legacy awards end at the closure whether or not it claims (SI 2014/1230 regs 8 and 46).

### Changed

- - Publish to PyPI with trusted publishing instead of the organisation-wide PyPI token.
- - Cut the CPU the Python tests spend in garbage collection: each test process raises the first-generation GC threshold and freezes the objects that exist once the tests are collected (#2316).

### Fixed

- - Projected single-year datasets to 2032 (fiscal year 2032-33) rather than 2030, so 2031-32, the last year of a forecast made in 2026-27, is a dataset year. Before, 2031 and later were served from 2030: earnings, other incomes and weights grew by their `uprating` indices, but rent, council tax and Northern Ireland domestic rates were held flat, recorded Pension Credit capital fell to -1 (the household capital proxy), and tax-free savings income and other stored inputs with formulas were recalculated.
  - Preserved variable-index growth after 2030 for inputs omitted from the dataset projection map, including salary-sacrifice pension contributions and housing charges. Energy inputs retain their documented FY26/27 price basis, and already projected inputs are reset under `no_economic_assumptions`.
- - Fixed Universal Credit closure claims with ineligible partners, preserved protected mixed-age couples' pension-age route when Universal Credit entitlement is nil, and applied the nation-specific Council Tax Reduction rules for pension-age tax credit migrants.
- - Fixed Gift Aid income tax relief by extending rate limits instead of deducting donations from taxable income, and deducting grossed-up gifts from adjusted net income.
- - Stop the Python tests' memory growing with every Simulation under sys.monitoring coverage: each test process compiles each variable file once and every tax-benefit system runs that code (#2330).
  - Release dead tax-benefit systems' variable modules in the Python tests once eight more systems own modules than were alive at the last release, checked as each new system starts adding its variables as well as after each test.
  - Hand freed memory back to the system after each test file (glibc malloc_trim), and stop keeping the unpinned latest dataset cached after its smoke test.
- - Counted statutory sick, maternity and paternity pay as Universal Credit earned income (UC Regs 2013 reg. 55(4)). Universal Credit already deducted the National Insurance on all three, and the income tax on sick and maternity pay, so it rose as the payments rose. Statutory paternity pay is now also counted in household benefits, HBAI income and government spending, as sick and maternity pay already were.
- - Counted the Scottish Child Payment, Healthy Start vouchers and the Two Child Limit Payment in government spending, so `gov_balance` no longer leaves out benefits that households receive.
- - A failed batch of legacy parameter overrides is now rolled back whole, nodes a structural reform adds to the parameters survive later rebuilds and reprocessing, and the scenario docs say that `Scenario.apply` on a built simulation edits the annualised values.
- - Added tests that building the model and running a simulation leave the process's warning filters and numpy's error state unchanged, and that importing the package adds no filter that ignores a built-in warning category everywhere. A `ReformPeriodWarning` is no longer also written to the log, since warnings now reach the caller.


## [2.127.0] - 2026-10-12

### Added

- - Added a Fix evidence pull request check using a trusted base-branch checker to require bug fixes to name a collectable Python or executable YAML test from the PR's git objects, with an exemption only when model files and dependencies are unchanged.

### Changed

- - Publish only the policyengine-uk release files whose checks passed. The release workflow makes the version commit on the latest main, retrying instead of failing when main moves. It builds the wheel and sdist once from that commit and runs the full test suite on the installed wheel in the locked environment. It uploads the same files only after the tests pass, and tags that exact commit, failing on tag errors. CI tests now fail on any skip, expected failure or XPASS that is not on a reviewed allowlist.

### Fixed

- - `in_receipt_of_savings_credit_only` now requires a Pension Credit payment, so a reform that stops Pension Credit being paid no longer leaves savings-credit-only families assessed on the Pension Credit route for Council Tax Reduction and pension-age Housing Benefit, with or without the Pension Credit freeze. Under `disable_simulated_benefits`, which sets Pension Credit to the reported amount, receipt now also needs reported Pension Credit.


## [2.126.12] - 2026-10-12

### Fixed

- - Every reform route now writes dated changes onto the statutory parameter timeline and reprocesses it as current law is processed. A dict reform dated 6 April now sets that fiscal year, and uprating, threshold indexation and the aligned NICs thresholds follow reformed values. A bounded change on an uprated or indexed parameter now resumes prior law's projected path, not a stale stated value. Reforms applied after the data load now reach the Universal Credit rebalancing inputs and the parameter-gated structural reforms. `parameters.baseline` stays current law under `Scenario(parameter_changes=...)`.


## [2.126.11] - 2026-10-12

### Changed

- Documentation pages in docs/book/assumptions, validation, policy and programs/gov/<agency> are now picked up by folder, so a new page no longer needs a myst.yml entry. This also publishes eight existing pages that were missing from the contents.
- - Removed the stale non-strict expected failure for the 2023-24 Class 4 lower profits limit (#1968, fixed by #2058), so the alignment test now asserts that year.

### Fixed

- Warned when `UKSingleYearDataset` is given a `fiscal_year` alongside a file path, where it cannot take effect, and when it is built from DataFrames without one. Removed the process-wide `warnings.filterwarnings("ignore")` that importing the package installed, which hid these and every other warning from callers.
- - Split the CI `Test` job into a YAML job and three parallel shards of the Python tests, with a check that every collected test ran in exactly one shard, and measured coverage with `sys.monitoring` (#2099).
- Put the petrol and diesel pump prices that convert spending into litres on the DESNZ annual ULSP and ULSD series (the basis Microcosm UK prices fuel spending on), replacing the January 2024 RAC prices, and re-derived the petrol and diesel spending litre proxies so weighted litres still follow the HMRC/OBR road-fuel volume path (part A of #2169).
- - Stop paying Carer's Allowance to a carer whose net earnings exceed the earnings limit (£204 a week from April 2026).
- - Round the High Income Child Benefit Charge as ITEPA 2003 s. 681C(3) requires: the percentage down to a whole number, and the Child Benefit and the charge down to whole pounds.
- - Stop relieving a miscellaneous loss against other income in Income Tax, adjusted net income, total income and Universal Credit earnings: ITA 2007 s. 152(4) allows it only against miscellaneous income.
- Set the Personal Savings Allowance on the rest-of-UK bands for Scottish taxpayers, as ITA 2007 s. 12B(8) requires; give the higher amount at exactly the basic rate limit and the lower amount at exactly the higher rate limit (ITA 2007 s. 10); and use the right bands for periods 2016 and 2017.
- Band savings and dividend income above property income, which is non-savings income (ITA 2007 ss. 16, 16A), including in the income the annual allowance charge's marginal rate is read from.


## [2.126.10] - 2026-10-11

### Fixed

- - Fixed `Simulation.to_input_dataframe()` leaving out the person, benefit unit and household identifiers for years in which a simulation was given inputs after it was built, such as the Universal Credit health element status for 2026 to 2029, so that an exported frame loads back to a simulation that exports the same frame.


## [2.126.9] - 2026-10-11

### Fixed

- Set DWP benefit rates to the amounts announced in DWP's Benefit and pension rates publications and set by the Up-rating Orders, replacing CPI projections: 2025-26 values (including the Pension Credit standard minimum guarantee, £227.10 and £346.60, and the pension-age Housing Benefit allowances, £244.40 and £366.00), the legacy premiums, Constant Attendance Allowance and Pension Credit additions (uprated from a fixed start value, so years without a published key, and every year from 2027-28, were projected from that value; the premiums' and Constant Attendance Allowance's only early key was the 2020-21 rate, keyed at 2015), Income Support personal allowances, Housing Benefit non-dependant deductions, and earlier years where they differed. Fixed amounts the law does not uprate (WTC childcare limits, which Housing Benefit also uses, and the CTC family element) are no longer projected. The pension-age Housing Benefit allowances now cite SI 2006/214 rather than SI 2006/213.


## [2.126.8] - 2026-10-11

### Fixed

- - Let a household situation state whether its Universal Credit health element is at the new-claimant rate (`uc_receives_new_claimant_health_element`, default false), so a household's award no longer depends on its position among the other benefit units in a simulation; simulations built from data keep the seeded draw.
- - Corrected a property test that claimed adding an adult outside the claimant's family never changes the legacy award readers: an adult non-dependant ends the family's severe disability premium, so the test now checks that what such a member reports never changes a reader, that their presence changes one only through that premium, and that Income Support then falls by at most the premium. The benefit cap, which counts such a member's own awards, is held at zero in that test until #2298 is fixed.


## [2.126.7] - 2026-10-11

### Fixed

- - Fixed `Simulation(dataset=<DataFrame>)` for frames in which a benefit unit or household has more than one person. Each benefit unit and household now takes the value on its members' rows, single-person groups no longer take each other's values when the rows are not in identifier order, identifier columns are matched by exact name, an exported frame saved as CSV loads back, and the simulation's `dataset` holds the multi-year dataset the frame describes. Identifiers are read as whole numbers, value by value; frames whose identifier columns contradict each other, repeat a person, or name people or groups only with floats that may stand for more than one identifier (32-bit floats of `2**24` or more) are refused instead of merging households.
  - Fixed the NHS, education and other public spending budget reforms (`gov.contrib.policyengine.budget`) raising `KeyError` when a simulation's data leaves an income decile empty, as a small sample does. An empty decile's share now goes to nobody.


## [2.126.6] - 2026-10-11

### Fixed

- - Defined the young person in Scotland's working-age Council Tax Reduction scheme as a Universal Credit qualifying young person from 2022-23 (Council Tax Reduction (Scotland) Regulations 2021 reg. 6), for lone-parent status and for the members whose income counts; other schemes keep the Child Benefit definition.


## [2.126.5] - 2026-10-11

### Fixed

- - Stopped counting a benefit unit's own claimant or partner as its child or qualifying young person for Child Benefit, Child Tax Credit and Pension Credit (SSCBA 1992 ss.141 and 143 and Child Benefit (General) Regulations 2006 regs 12-13; CTC Regs 2002 reg. 3; SPC Regs 2002 Sch. IIA para. 3), so a lone 16- to 19-year-old no longer gets Child Benefit, a Child Tax Credit child element or a Pension Credit child addition for themselves.


## [2.126.4] - 2026-10-11

### Fixed

- - Place a household with no BRMA input in its region's BRMA with the most private-rented households, from the 2021 and 2022 censuses (Maidstone if the region is unknown), instead of Maidstone in every region. A household that sets no region is in London, the region default, so it now gets Inner South East London's LHA rates. A BRMA input still carries forward to later years while the household stays in the same region.


## [2.126.3] - 2026-10-10

### Fixed

- - Pay pre-2026 Universal Credit health element claimants the legislated protected LCWRA amount (£429.80 a month in 2026-27, one amount for every claimant type), and project later years at the Universal Credit Act 2025 s. 4 floor.
- - Stopped a negative income source, such as a property loss or a self-employment loss, from reducing a claimant's other Pension Credit income.


## [2.126.2] - 2026-10-10

### Fixed

- - Counted salary sacrifice pension contributions only for people with pay, so from 2029 the excess over the £2,000 cap no longer gives employment income to people without pay.
- - From 2031-32, index the personal allowance and basic rate limit by the previous September's CPI with the statutory round-ups (Income Tax Act 2007 ss57 and 21), keep the primary threshold, upper earnings limit and Class 4 profits limits aligned with them, and raise the secondary threshold by September CPI. Before, they followed calendar-year CPI series without rounding.


## [2.126.1] - 2026-10-10

### Fixed

- - Raised the `Test` job's timeout from 60 to 120 minutes: the suite now takes about an hour, so pull request runs were being cancelled at the limit.


## [2.126.0] - 2026-10-10

### Added

- - Add `is_on_pension_credit` and `is_on_universal_credit` (whether the award is payable to the person) and `tax_credit_award` (the tax credit award payable to them). For the claimant and partner they read their couple's award: Pension Credit is paid to one member (the one who reports it, else the claimant, among members who have attained the qualifying age), and Universal Credit and tax credits are joint awards (but not for a partner who cannot be a joint Universal Credit claimant, whose partner claims as a single person). Anyone else is on an award only through their own report.
  - Add person-level `winter_fuel_payment` and `pension_age_winter_heating_payment`, with `winter_fuel_payment_eligible`, `pawhp_eligible`, `is_on_winter_fuel_payment_relevant_benefit` and `is_on_pawhp_relevant_benefit`. The household `winter_fuel_allowance` and `pawhp` now add up their members' payments.

### Fixed

- - Test receipt of a relevant benefit for the Winter Fuel Payment and the Pension Age Winter Heating Payment person by person. Under SI 2000/729, SI 2025/969 and NISR 2025/142 a person is on a relevant benefit when it is paid to them: Income Support, income-based JSA, income-related ESA and Pension Credit are paid to one member of a couple, while Universal Credit is awarded and paid to the couple jointly. Under SI 2024/869 reg 2(5), NISR 2024/160 reg 2(5) and SSI 2024/351 a member of a couple is also on one when the other member is (`partner_receipt_counts`). A non-dependant's income-related ESA, income-based JSA, Income Support or Pension Credit no longer qualifies a pensioner in the same household, or exempts them from the Winter Fuel Payment income test.
  - Count Universal Credit as a relevant benefit for both payments, and a tax credit award of at least £26 for the 2024 qualifying week, as SI 2024/869, SI 2025/969 and SSI 2024/351 list them.
  - Pay each person the amount the regulations set: one payment for a couple on a relevant benefit, the full amount to anyone else living without another entitled person, and the shared amounts (£100, or £200 or £150 over 80, and the PAWHP equivalents) otherwise. Two benefit units in one household can now both be paid.
  - Pay the Winter Fuel Payment in Scotland up to the 2023 qualifying week (SI 2000/729 covered Great Britain) and the Pension Age Winter Heating Payment only from the 2024 week.
  - From the 2025 qualifying week, pay the Pension Age Winter Heating Payment to everyone of pensionable age in Scotland at the legislated amounts (SSI 2025/282, SSI 2025/100 and SSI 2026/170) instead of a flat £100 to households not on a relevant benefit.
  - Cite the Winter Heating Assistance (Pension Age) (Scotland) Regulations 2024 (SSI 2024/351) in the PAWHP parameters; they cited SSI 2024/250, a planning instrument.

### Removed

- - Remove `gov.social_security_scotland.pawhp.amount.base`: the regulations set no flat amount for households not on a relevant benefit; the new shared amounts replace it.


## [2.125.2] - 2026-10-10

### Changed

- - Require policyengine-core 3.32.27, which gives each clone its own record of `set_input` values and forgets the record of a value `Holder.delete_arrays` deletes (PolicyEngine/policyengine-core#561), and remove the `Simulation.clone` override that worked around policyengine-core#559. The `Simulation.delete_arrays` override and the `Simulation.calculate` sweep stay, now for the records that rebuilding the populations leaves behind (PolicyEngine/policyengine-core#605).


## [2.125.1] - 2026-10-10

### Fixed

- - Fix Class 2 National Insurance for 2015-16 to 2023-24 against s.11 SSCBA 1992: charge £3.45 a week in 2023-24; from 2022-23 charge only profits above the Class 2 lower profits threshold (£11,908, then £12,570), with profits from the small profits threshold up to it treated as paid; keep the small profits threshold at £6,725 in 2023-24 and 2024-25 and correct it to £5,965 in 2015-16 and 2016-17; date the abolition 6 April 2024. Class 2 now tests its thresholds on the profits Class 4 is charged on (s.11(3)), after capital allowances, the trading allowance and loss relief, not on self-employment income. A full year of Class 2 is every contribution week in it, so 53 weeks in 2019-20. The Universal Credit minimum income floor's notional Class 2 follows the same rule, so it deducts no Class 2 in 2022-23 and 2023-24 on a threshold the lower profits threshold covers. Every value now cites its amending instrument.
- - Fixed Class 4 NICs against s.15 SSCBA 1992: the 2023-24 lower profits limit is £12,570 (it was £11,908), the 2022-23 rates are 9.73% and 2.73% for the whole year (they were 10.25% and 3.5%), the 2023-24 additional rate is 2% (it was 3.5%), and the 2015-16 upper profits limit is £42,385. Every Class 4 limit and rate from 2015-16 to 2025-26 now cites its legal source.


## [2.125.0] - 2026-10-09

### Added

- - Add `claimant_or_partner_esa_income` and `claimant_or_partner_jsa_income`: the income-related award of the claimant and partner. When `esa_income` or `jsa_income` holds what the reported awards give (its formula, or their plain total), this is the same on the claimant's and partner's reports; any other stored value is taken to be theirs, and a stored zero is zero. An entered award equal to either reported amount, to within half a penny at stored precision, is read through the reports, so enter these variables directly to state the claimant's or partner's award.
  - Add `is_on_income_related_esa`, `is_on_income_based_jsa` and `is_on_income_support`: whether the award is payable to the person. Of the claimant and partner, that is the payee of their award (the one who reports it, or the claimant); for anyone else, the award on their own report alone, after tariff income from the benefit unit's capital and within the capital limit, while the benefit unit's award is positive (for Income Support: their own report while Income Support is active and not neutralised), so another member's report never changes it.

### Fixed

- - Count only the claimant's and partner's income-related ESA and income-based JSA in Housing Benefit, council tax reduction and tax credit income, and in the passports for Housing Benefit (`in_receipt_of_income_support_jsa_ib_or_esa_ir`), working-age council tax reduction, Scottish Child Payment and targeted childcare. Another member of the benefit unit, such as a non-dependent adult, who reports an award claims in their own right; their award still counts in household income.
  - Exempt a council tax reduction non-dependant in the local working-age schemes only when Income Support, income-based JSA or income-related ESA is payable to them, not to their partner or another benefit-unit member. A non-dependant couple on one of these benefits therefore pays the partner's deduction. The maintenance loan schedule for students entitled to benefits now reads whether income-related ESA is payable to the student (HB Regs 2006 reg 56(2)(a)), alongside the existing parent and disability tests, and adds reg 56(2)(c): a student who is the claimant or partner qualifies when their applicable amount would include the disability or severe disability premium, as when their partner receives a disability benefit.
  - Treat a family as claiming Income Support (`would_claim_IS`) when the claimant or partner reports it, or when every entitled benefit is claimed (`claims_all_entitled_benefits`); another member's report no longer counts.


## [2.124.0] - 2026-10-09

### Added

- - Added `benunit_reported_capital`, the benefit unit's recorded savings and investments (such as the FRS's TOTCAPB4; -1 when nothing is recorded). `uc_reported_capital` and `pension_credit_reported_capital` are now formulas that default to it, so a dataset records the observed capital once and each means test derives its own; either can still be set directly. The input uprates like `savings`, as does either programme variable when a dataset stores it directly. Results are unchanged for datasets and situations that do not supply the new input, except as noted under Changed.

### Changed

- - `uc_reported_capital` and `pension_credit_reported_capital` set directly in a situation now apply only to the years they are set, as for any formula variable; later years derive from `benunit_reported_capital`, which is uprated from the year it is set. Before, a value set for one year carried into later years (uprated, for Pension Credit). A dataset that stores `uc_reported_capital` now has it uprated by per-capita GDP, like `savings`, where it used to be held flat; stored `pension_credit_reported_capital` uprates as before.

### Fixed

- - Fixed `build_metadata` reporting the commit of an enclosing git repository, such as a policyengine-uk-data checkout whose virtualenv holds policyengine-uk, as policyengine-uk's `git_sha`. It now reads only policyengine-uk's own checkout or the installer's PEP 610 git record, and otherwise returns `None`.
- - Add the 15.05% employer Class 1 rate for 2022-23 (Health and Social Care Levy Act 2021 s.5(2)(b)) and its end on 6 November 2022 (Health and Social Care Levy (Repeal) Act 2022 s.2(1)). Model year 2022 now reads 15.05%, as the employee main rate reads 13.25%.


## [2.123.10] - 2026-10-09

### Fixed

- - Bar Income Support when the claimant is engaged in remunerative work, 16 hours a week or more of paid work, or the partner is, 24 hours or more (SSCBA 1992 s.124(1)(c); IS Regs 1987 reg 5(1) and (1A), with 24 hours for both before 7 April 1992 and 16 for the partner until 6 October 1996). A carer within Sch 1B para 4, claimant or partner, is not treated as engaged in remunerative work (reg 6(4)(c)). The hours come from the new `income_support_remunerative_work_hours`, which is usual weekly hours and can be entered directly to average fluctuating hours or to leave out work that reg 6(1) excludes, such as child minding at home or a councillor's duties.
  - Bar Income Support when the claimant is entitled to a jobseeker's allowance of either kind, or the partner to income-based JSA (s.124(1)(f)). The partner's contribution-based JSA does not bar it. Income-based JSA is the award on the claimant's and partner's reported amounts after the JSA capital test. A `jsa_income` that holds anything the reported amounts do not give (neither that award on everyone's reports nor their plain total), such as an award entered directly or a reform that removes it, is taken to be theirs. As for ESA, an amount within half a penny of zero is no award, so a float residual does not bar the claim.


## [2.123.9] - 2026-10-09

### Changed

- Cancel superseded test runs on main and give every lint, docs and versioning job a timeout, so outdated or hung jobs free shared GitHub Actions runners.


## [2.123.8] - 2026-10-08

### Fixed

- Universal Credit for a member of a couple who claims as a single person (UC Regs 2013 reg. 3(3)): the single-claimant standard allowance at the claimant's own age, no LCWRA or carer element for the other member, the single-claimant benefit cap and the shared accommodation rate, while the couple's capital and income still count. The other member's own disability and other personal benefits no longer lift the benefit cap. In the childcare work condition the claimant must meet the paid work limb and the other member the partner limb, and only the claimant can be treated as in paid work under regulation 32(2). A partner under 18 outside regulation 8 is now identified as such a partner. The benefit cap rate and exceptions and the LHA shared accommodation test, which Housing Benefit shares, keep the couple rules for a family that stays on legacy benefits (reports one and would not claim Universal Credit).


## [2.123.7] - 2026-10-08

### Fixed

- - Correct the Energy Bills Support Scheme amounts, monthly timing, and eligibility in Great Britain and Northern Ireland.
- - Corrected the 2020 over-75 TV licence Pension Credit transition to start on 1 August while preserving its Boolean eligibility rule.


## [2.123.6] - 2026-10-08

### Fixed

- Assess each family that claims Council Tax Reduction under its own scheme and its own non-dependant exemption, so in a shared-rent household a working-age sharer no longer takes the pensioner scheme because the household head's family is pension-age (or the reverse), and one claimant's disability no longer exempts another's claim from non-dependant deductions.
- - Disregard Housing Benefit income and capital on receipt of Guarantee Credit, so pensioners who do not claim Pension Credit retain the ordinary means test.


## [2.123.5] - 2026-10-07

### Fixed

- - Corrected the Class 1 secondary threshold for 2015-16 and 2016-17 to the statutory £156 a week (£8,112 a year); it held the £155 primary threshold.


## [2.123.4] - 2026-10-07

### Fixed

- - Apply the Income Support ESA and existing-award conditions only to the claimant and partner (SSCBA 1992 s.124(1)). Another member of the benefit unit who is neither the claimant nor the partner (a non-dependent adult or a dependent young person) no longer bars the claim by having income-related ESA, and no longer counts as having an existing Income Support award.
  - Treat the claimant or partner who reports the existing Income Support award as the claimant. No new claim can be made (UC (Transitional Provisions) Regs 2014 reg 6A(1), from 25 July 2022; the model applies this in every year), and a partner who takes over an award makes a claim (Claims and Payments Regs 1987 reg 4(4)). That person must be under the qualifying age for State Pension Credit, in a prescribed category and without ESA, so a partner who cares can no longer take over the other partner's award.
  - Bar Income Support when the claimant is entitled to contributory ESA (s.124(1)(h)). Income-related ESA of the claimant or partner still bars it. An `esa_income` that the reported awards do not explain (one entered directly, or set by a reform) is taken to be theirs. An amount within half a penny of zero is no award, so a float residual no longer bars the claim.
  - Add the IS Regs 1987 Sch 1B para 2 prescribed category: a single claimant or lone parent with a child under 16 placed by a local authority (proxied by `is_looked_after_by_local_authority`).
  - Leave a child placed by a local authority out of `youngest_child_age_for_legacy_benefits`; such a child is not a member of the claimant's household (IS Regs 1987 reg 16(4)).


## [2.123.3] - 2026-10-07

### Fixed

- Preserved Energy Price Guarantee effective dates and added an explicit indicator for when the subsidy applies.
- Corrected the Energy Price Cap parameter to use Ofgem's final quarterly Direct Debit illustrations.
- Added the Energy Price Guarantee prepayment discount from July 2023 through March 2024. Current UK microsimulation data does not identify households using prepayment meters, so the discount applies only when that input is supplied.


## [2.123.2] - 2026-10-07

### Fixed

- - Store the Class 1 secondary threshold from 2025-26 as £5,000 / 52 a week, so employer National Insurance uses the statutory annual £5,000 (SI 2001/1004 reg 11(3A)(b)) rather than 52 x the rounded weekly £96 = £4,992. Employer NI falls by up to £1.20 a year per employee earning above the threshold.


## [2.123.1] - 2026-10-07

### Fixed

- - Split the reported State Pension at the legislated data-year rate, so a State Pension rate reform changes `state_pension` when it also sets the data year's rate: undated reforms, and every reform in a simulation without a dataset (a household calculation), where the data year is the period.
- - Charge the High Value Council Tax Surcharge only on households that own their main residence (owned outright or with a mortgage). Owners, not occupiers, are liable, so tenants now owe nothing even when a positive `main_residence_value` is supplied. Households with no `tenure_type` take the `RENT_PRIVATELY` default and are no longer charged.


## [2.123.0] - 2026-10-07

### Added

- - Added landlords' residential finance-cost tax reduction (ITTOIA 2005 ss. 272A, 274A and 274AA) from three new optional inputs: `property_rental_income` (gross receipts), `property_finance_costs` and `property_finance_costs_brought_forward`. The reduction is the property basic rate (the basic rate before 2027-28) on the lowest of the relievable costs, the property profits and adjusted total income, is limited to the tax left at Step 5, and reports the unrelieved costs as `property_finance_costs_carried_forward`. A new `disallowed_share` parameter carries the 2017-18 to 2020-21 phase-in, and setting it to nil restores full deductibility. Universal Credit sets the reduction against the tax on property income, not the tax on earnings, and the means tests that count property income (tax credits, Housing Benefit, Income Support, Pension Credit and council tax reduction) count it after finance costs.

### Fixed

- - Corrected the reduced VAT rate history from April 1994 through August 1997.
- - Corrected the Tax Credits withdrawal rate effective date to 6 April 2011.
- - Included income equal to the minimum guarantee in Guarantee Credit eligibility.
- - Stopped the property allowance being deducted on top of expenses already netted out of `property_income` (ITTOIA 2005 Part 6A Chapter 2). It now gives full relief only where profit, or receipts when known, are within the allowance, and partial relief when `property_rental_income` shows that expenses fall short of it. A landlord takes the allowance or the finance-cost reduction, whichever leaves less income tax. The allowance now starts in 2017-18.


## [2.122.3] - 2026-10-06

### Fixed

- Put a Universal Credit claimant who has reached the qualifying age for State Pension Credit in the group with no work-related requirements (UC Regs 2013 reg. 89(1)(a)), reading that age (State Pension Credit Act 2002 s. 1(6)) instead of the claimant's own State Pension age. The two differ only for men born before 6 December 1953, in 2018-19 and earlier: such a man in a mixed-age couple now leaves the minimum income floor from his qualifying age rather than from 65.


## [2.122.2] - 2026-10-06

### Changed

- - Note that the council tax reduction (CTR) capital-route loss in #1909 is an artefact of the `corporate_wealth` proxy, so CTR offsets in pension costings that rest on it should not be read as real effects. A pensioner whose Pension Credit award is savings credit only is tested against the CTR capital limit on Pension Credit's capital (`council_tax_reduction_assessable_capital`), and Pension Credit's capital sources count `corporate_wealth` but not `private_pension_wealth`. In datasets built before the `private_pension_wealth` split, `corporate_wealth` also holds imputed pension wealth, which Pension Credit disregards (State Pension Credit Regulations 2002 Sch V paras 22 and 23), so these pensioners can fail the £16,000 limit on pension wealth that is not countable capital. A benefit unit that records `pension_credit_reported_capital` bypasses the proxy. See #1837 and #1936. Two CTR test cases pin the route, and a new Housing Benefit case pins the savings-credit-only route of #1945 for a household built from age, pensions, rent, tenure and capital alone.


## [2.122.1] - 2026-10-06

### Fixed

- Read one household head per household in every programme, so an `is_household_head` input that flags several members, or none, can no longer leave rent, non-dependant and Council Tax Reduction rules disagreeing about whose household it is.


## [2.122.0] - 2026-10-05

### Added

- Add `uc_work_related_group_apart_from_earnings`, `uc_is_responsible_carer`, `uc_expected_hours`, `uc_youngest_child_age` and `uc_is_in_gainful_self_employment`; the inputs `uc_has_limited_capability_for_work`, `uc_is_in_pregnancy_or_post_confinement_period`, `uc_is_adopter_in_first_year`, `uc_is_student_with_no_work_related_requirements`, `uc_is_responsible_foster_parent_of_child_under_one`, `uc_is_foster_parent_or_new_friend_or_family_carer` and `uc_is_ineligible_partner`; and the parameters under `gov.dwp.universal_credit.work_requirements` for the responsible carer's child ages and expected hours and the 16-hour threshold, with `gov.dwp.universal_credit.means_test.minimum_income_floor.no_requirements_partner_hours` and `gov.dwp.universal_credit.means_test.minimum_income_floor.ineligible_partner_hours` (the 35 hours of reg. 90(3)(b)(ii)). Without a recorded nomination, `uc_is_responsible_carer` takes the joint claimant who works fewer hours (`hours_worked`), then the elder; `hours_worked` defaults to 0, so set `uc_is_responsible_carer` (or each member's hours) for a couple with a child entered without hours.

### Fixed

- Apply the Universal Credit minimum income floor only to claimants who would otherwise be subject to all work-related requirements (UC Regs 2013 reg. 62(1)(b)): not to claimants with limited capability for work or work-related activity, carers, claimants over State Pension Credit qualifying age, the responsible carer of a child under 3, or the prescribed descriptions of regs. 89 and 91 (Welfare Reform Act 2012 ss. 19 to 21). Set the floor from the expected hours of reg. 88 (30 a week for the responsible carer of a child under 13, as DWP does, in place of 35), and build the couple threshold from each partner's own threshold (reg. 90(2) and (3)): 16 hours for a partner in the work-focused interview or work preparation group, nothing for a partner with no work-related requirements, and 35 hours at the national living wage for a partner who cannot be a joint claimant.


## [2.121.0] - 2026-10-05

### Added

- - Price supplied person-level bus journeys with regional yields, single-fare caps and proportional reform controls, preserving reported spending for legacy data.

### Fixed

- - Keep the unimplemented Scottish Two Child Limit Payment inactive in the baseline, with explicit counterfactual tests.
- - Recognise housing-association tenants as renting and share the rental tenure predicate between households and benefit units.
- - Preserve the independent Child Benefit claim gate, restore opted-out claimants' payments when a reform lowers the charge below a configurable behavioural threshold, and handle cliff charges without division warnings.


## [2.120.0] - 2026-10-05

### Added

- - Add `is_uc_assessed_claimant`: the single claimant or the two joint claimants whose income a Universal Credit award assesses (`is_uc_claimant`, limited to the two eldest when inputs flag more).

### Fixed

- - Count only the claimants' income in Universal Credit (UC Regs 2013 reg. 22(1); WRA 2012 s. 8(4)). `uc_earned_income` and `uc_unearned_income` also counted the claimant's children and qualifying young people, so a dependant's wages, profits or pension reduced the parents' award. The benefit cap earnings exception (reg. 82(1)(a)), the capped benefit total (WRA 2012 s. 96(1)) and the childcare work condition (reg. 32(1)) now read the claimants only, so a dependant's job neither lifts the cap nor meets or blocks the work condition.


## [2.119.0] - 2026-10-05

### Added

- Add `date_of_birth`, each person's day of birth as a YYYYMMDD number from `age` and `months_since_last_birthday`, which can also be set directly (with `age` as the person's age on 6 October) and then sets State Pension age and the cutoffs below; and add date parameters for the 6 April 2017 cutoffs: `gov.dwp.universal_credit.elements.child.limit.born_before`, `gov.dwp.tax_credits.child_tax_credit.limit.born_before` and `gov.dwp.pension_credit.guarantee_credit.child.first.born_before`, and for the Pension Credit mixed-age couple saving, `gov.dwp.pension_credit.mixed_age_couples.saving_latest_birth_date` (5 February 1954).

### Changed

- `birth_year` is now the calendar year of `date_of_birth`. It is unchanged for household situations with whole ages; in survey data, people whose birthday falls from 7 October to 31 December now have the year before the period less their age, and a fractional age no longer truncates to the year before.

### Fixed

- Apply the "born before 6 April 2017" rules by date of birth: the Universal Credit child limit and higher first child element (UC Regs 2013 reg 24A(3); UC (Transitional Provisions) Regs 2014 reg 43), the Child Tax Credit child limit (Tax Credits Act 2002 s.9(3A)), the Pension Credit first child addition (SPC Regs 2002 Sch IIA para 10), and the Pension Credit mixed-age couple saving, which needs the older member born on or before 5 February 1954 to have reached the qualifying age by 14 May 2019 (SI 2019/37 art. 4). The child rules compared a birth year of the period less the whole age with 2017, so in survey data the whole cohort born from October 2016 to October 2017 counted as born after the cutoff, when about half was born before it. Universal Credit and Pension Credit also now order children by date of birth (UC Regs reg 24B), so the first or eldest child is the one born first. For the child rules, household situations with whole ages, which place each person in the middle of their year of age, are unchanged; a fractional age is now read as the exact age on 6 October, as it already is for State Pension age. The mixed-age saving does change for whole ages: a situation's older member aged period less 1954 is placed on 6 April 1954, after the cutoff, where the birth year admitted them.

### Removed

- Remove `gov.dwp.universal_credit.elements.child.limit.start_year` and `gov.dwp.tax_credits.child_tax_credit.limit.start_year`, which held the year 2017, and `gov.dwp.pension_credit.mixed_age_couples.saving_latest_birth_year` (1954). A reform to a cutoff now sets the matching date parameter, written as a YYYYMMDD number: `born_before` (20170406) or `saving_latest_birth_date` (19540205).


## [2.118.0] - 2026-10-04

### Added

- Add the `gov.dwp.universal_credit.means_test.minimum_income_floor.self_employed_national_insurance` parameter and the `uc_minimum_income_floor_gross`, `uc_minimum_income_floor_income_tax`, `uc_minimum_income_floor_national_insurance` and `uc_individual_earned_income_before_mif` variables; `uc_minimum_income_floor` is now the net floor.

### Fixed

- Apply the Universal Credit minimum income floor as the law sets it (UC Regs 2013 reg. 62): compare each self-employed claimant's earned income after their own tax, NI and pension contributions with the individual threshold converted to a net amount (reg. 62(4)) by deducting the income tax and Class 2 and Class 4 NI due on it, as DWP does, rather than the gross threshold less the tax on their actual profits; apply the couple rule of reg. 62(3); use the minimum wage for the person's age, never the apprenticeship rate (reg. 90(2)); apply the floor to claimants only, including those with a trading loss; and stop setting a trading loss against employed earnings (reg. 57(2)).

### Removed

- Remove `uc_mif_capped_earned_income`, which applied a gross floor to gross earnings; use `uc_individual_earned_income`.


## [2.117.2] - 2026-10-04

### Fixed

- Give Council Tax Reduction to the household head's family, the liable resident, instead of the oldest adult's, so families tied for oldest no longer both get a full award.


## [2.117.1] - 2026-10-04

### Fixed

- - Disregard the earnings, whole income and whole capital of a Housing Benefit claimant on Universal Credit, as SI 2006/213 Schedule 4 paragraph 12, Schedule 5 paragraph 4 and Schedule 6 paragraph 5 (Northern Ireland: SR 2006/405 Schedule 5 paragraph 12, Schedule 6 paragraph 4 and Schedule 7 paragraph 5) require, so where Housing Benefit is paid alongside Universal Credit the means test gives the maximum. Being on Universal Credit means being entitled to it, whether it is in payment or not (regulation 2(3B)), which the model reads as Universal Credit above nil before the benefit cap and deductions. The limb applies from 28 October 2013 in Great Britain and 8 May 2018 in Northern Ireland (`gov.dwp.housing_benefit.means_test.universal_credit_passport`). Adds `housing_benefit_on_passporting_benefit`, which the three passports now read. No family receives both benefits in the model yet, so outputs on the Enhanced FRS do not change.


## [2.117.0] - 2026-10-04

### Added

- - Add `partners_care_for_same_severely_disabled_person` (benefit unit). Two people caring for the same severely disabled person cannot both be entitled to Carer's Allowance (SSCBA s.70(7ZA)) or Carer Support Payment (SSI 2023/302 reg 5(3)), so they get one carer premium. Unless it is supplied, partners are treated as caring for the same person unless both are entitled with an award, reported (`carers_allowance_reported`) or supplied directly as an allowance or entitlement that caring hours do not explain, since caring hours cannot show who is cared for.

### Fixed

- - Pay the legacy carer premium once for each claimant or partner entitled to Carer's Allowance or Carer Support Payment (IS Regs 1987 Sch 2 paras 14ZA(1) and 15(7), with the matching Housing Benefit and council tax reduction schedules), rather than one premium for the couple. A couple who both have Carer's Allowance awards get two premiums; a couple who care for the same severely disabled person, or who are both entitled on caring hours alone, get one. The premium enters the Income Support, Housing Benefit and council tax reduction applicable amounts.
  - Correct the 2025-26 carer premium to £46.40 a week.

### Removed

- - Remove the `gov.dwp.carer_premium.couple` parameter. It held the single rate, while the law pays the per-person amount (`gov.dwp.carer_premium.single`) once for each qualifying claimant and partner. Reforms should change `gov.dwp.carer_premium.single`.


## [2.116.1] - 2026-10-04

### Changed

- Document which Local Housing Allowance category and determination Housing Benefit and Universal Credit each read, and drop Universal Credit test inputs that the published rates no longer use.


## [2.116.0] - 2026-10-04

### Added

- - Add the working-age Housing Benefit earnings disregard for claimants in specified or temporary accommodation (SI 2006/213 Schedule 4 paragraph 18, from 5 October 2026, inserted by SI 2026/753 as substituted by SI 2026/978; Northern Ireland: SR 2006/405 Schedule 5 paragraph 18, inserted by SR 2026/157). Where the claimant or partner is an employed or self-employed earner, £61.41 a week for a single claimant or lone parent under 25 and £77.73 at 25 or over; for a couple, £97.33 where both are under 18, £61.53 where one is 18 or over but both are under 25, and £119.70 where one is 25 or over. It is added to the £5, £10 and £25 disregards, capped at net earnings, and counts in the £17.10 additional disregard's earnings test (paragraph 17(3)(a)). It reads the new `in_specified_or_temporary_accommodation` input, which defaults to false, so it changes no dataset result. The model reads 2026-27 at 30 April 2026, so it applies from 2027-28.


## [2.115.0] - 2026-10-04

### Added

- Added `state_pension_credit_qualifying_age` and `has_attained_state_pension_credit_qualifying_age`, the qualifying age for State Pension Credit from each person's date of birth, and `ni_class_4_liable`, Class 4 liability by age at the start of the tax year.

### Changed

- Winter Fuel Payment uses pensionable age from 2024-25 and the State Pension Credit qualifying age in earlier years, as the regulations in force in each year require.

### Fixed

- Class 4 National Insurance now stops from the first tax year that begins on or after the day State Pension age is reached (Social Security (Contributions) Regulations 2001 reg 91(a)): a person over State Pension age on 6 April is excepted, and one who reaches it during the year pays Class 4 for that whole year. Before, anyone over State Pension age on 6 October was excepted.
- Pension Credit, Universal Credit, Housing Benefit, Council Tax Reduction, Income Support, the benefit cap (which reaches only working-age Housing Benefit and Universal Credit) and Winter Fuel Payment now use the qualifying age for State Pension Credit (State Pension Credit Act 2002 s.1(6)) instead of each person's own State Pension age. For a man born before 6 December 1953 that is the State Pension age of a woman born on the same day, not 65, so these programmes change only in 2018-19 and earlier. National Insurance and State Pension keep using the person's own State Pension age; Class 4 now reads it at the start of the tax year (see the Class 4 entry). Housing Benefit and Council Tax Reduction choose their pension-age or working-age allowances, means tests and premium schedules with their own statutory tests (HB(SPC) Regs 2006 reg 5 and the CTR pensioner tests), which exclude families on Universal Credit, Income Support, income-based Jobseeker's Allowance or income-related Employment and Support Allowance; the pension-age severe disability premium follows the qualifying age. Income Support uses its own working-age premiums, and its age test applies to the claimant, who must also be the one in a prescribed category such as carer, so a mixed-age couple can claim it through the younger partner unless the couple is on Pension Credit (SSCBA 1992 s.124(1)(aa), (e) and (g)).


## [2.114.3] - 2026-10-04

### Fixed

- - Local Housing Allowance rates now come from the published determinations instead of the 30th percentile of the 2020 list of rents uprated by the private rent index. Sources: VOA, the Welsh and Scottish Governments, the NIHE, and monthly Universal Credit rates from DWP (Great Britain) and nidirect (Northern Ireland). Determinations from April 2020 are recomputed from the published 30th percentile rents with the national maxima, the anomalous-rate rule (Rent Officers Order Sch 3B para 3) and the March 2020 minimum (para 3A, which also applies to Northern Ireland's Universal Credit rates). This reproduces every published rate and stops rates falling with dwelling size. Universal Credit uses the monthly determination rather than 52 weeks of the weekly one.
- - Replaced the Scottish lists of rents, which were copies of English BRMAs' lists, with Rent Service Scotland's own lists released under FOI 202200303624, so percentile reforms scale Scottish LHA rates by Scotland's rent distributions.


## [2.114.2] - 2026-10-04

### Fixed

- - Care to Learn pays each qualifying child's childcare costs up to the weekly maximum per child, once per child, and only to young parents on a study programme (ESFA conditions of grant 2026-27).
  - The extended childcare entitlement requires a qualifying young child (SI 2022/1134 reg 13: aged three, two from April 2024, nine months from September 2024), and lets a parent or partner with limited capability for work or a specified benefit qualify without the work and income tests when the other meets them (regs 14(4) and 15(4)). The income test's boundaries now match regs 14(3)(c) and 18.
  - Maintenance loan household income treats students aged 25 or over as independent (Education (Student Support) Regulations 2011 Sch 4 para 2(1)(a)).
  - Tax-Free Childcare's caring and incapacity route uses the benefits in SI 2015/448 reg 13(1), not the Pension Credit child disability list, and treats a qualifying partner as meeting the minimum income (reg 13(2)(b)).


## [2.114.1] - 2026-10-04

### Fixed

- Use the Pension Credit assessment of income and capital, plus the savings credit payable, for Housing Benefit where the Pension Credit award is savings credit only (HB(SPC) Regs 2006 reg 27). For pensioners without earnings, while the award remains savings credit only, a rise in private pension no longer lowers net income (tested for council tenants in Great Britain); losing Pension Credit passports, such as the free TV licence at 75, still applies when savings credit ends.


## [2.114.0] - 2026-10-04

### Added

- - Add `cash_isa` and `stocks_and_shares_isa` Household wealth input variables for ISA balances.


## [2.113.6] - 2026-10-04

### Changed

- Document what `pension_credit_reported_capital` must contain (countable capital after the Schedule V disregards and reg. 19 valuation) and what it replaces, and restate its monotonicity property around the savings credit's intended exception.


## [2.113.5] - 2026-10-04

### Fixed

- - Corrected pension-age Housing Benefit and Council Tax Reduction premiums by removing adult disability and adult enhanced disability premiums absent from their statutory schedules and applying the severe disability premium's qualifying-benefit, couple, Housing Benefit non-dependant and shared carer-attribution conditions. The carer condition does not yet count Universal Credit carer-element awards (#2120).


## [2.113.4] - 2026-10-04

### Changed

- - Documented that policy changes must be mirrored in Axiom RuleSpec (rulespec-uk), and added a pull request template with the required `axiom:` line.


## [2.113.3] - 2026-10-04

### Fixed

- Split additional State Pension by each person's State Pension type in the year simulated, as basic and new State Pension already are, instead of their type in the data year. Survey ages are held fixed across projected years, so records that were on the basic State Pension in the data year stand for new State Pension cohorts later, and the part of their reported State Pension between the two flat rates was paid twice. Basic, new and additional State Pension now add up to the reported amount uprated by the flat rate.
- Council Tax Reduction income now counts Carer Support Payment, which Scottish carers receive in place of Carer's Allowance (Council Tax Reduction (Scotland) Regulations 2021 reg 57(1)(b)(iva); Council Tax Reduction (State Pension Credit) (Scotland) Regulations 2012 reg 27(1)(j)). The Scottish Carer Supplement stays out.


## [2.113.2] - 2026-10-04

### Fixed

- Deduct from each person's Universal Credit earnings only their own income tax and National Insurance on that employment or self-employment (UC Regs 2013 reg. 55(5)(b), reg. 57(2) step 3), not the whole benefit unit's tax on all income, so tax on pensions, State Pension, property, savings and dividends, the High Income Child Benefit Charge and voluntary Class 3 contributions no longer reduce earned income.


## [2.113.1] - 2026-10-04

### Changed

- - Documented that `afcs_reported` is FRS benefit code 8 (Armed Forces Compensation Scheme payments and war disablement pensions, not armed forces independence payment) and tested that AFCS payments never confer severe disability.


## [2.113.0] - 2026-10-04

### Added

- - Give joint tenants and other sharers their share of the household's rent, boarders and lodgers their own rent and private tenure, a Housing Benefit LHA category (with its own size criteria and shared-accommodation rule) beside the Universal Credit one, statutory non-dependant exclusions and apportionment, the Housing Benefit meals deduction, and Council Tax Reduction on the council tax divided among jointly liable people, each claim under its own family's scheme and exemption from non-dependant deductions.


## [2.112.1] - 2026-10-03

### Fixed

- The legacy severe disability premium and the Pension Credit severe disability addition now share one attribution of whom each carer benefit is paid for caring for (`is_cared_for_by_carer_benefit_recipient`), so a carer in another benefit unit of the household bars the legacy premium as it already barred the addition, even when that carer is ignored as a non-dependant.
- - Counted a trading loss for Class 4 NICs only in the year it is entered for, so a one-off `trading_loss` is relieved once and only its unrelieved part reduces later years' profits (new `ni_class_4_trading_loss`).
  - Isolated supplied-input provenance between simulation clones and removed it for deleted inputs, preventing Class 4 from relieving cached carry-over losses again.
  - Corrected the Class 4 property-test reference to use each year's trading allowance parameter, including the zero allowance in historical years.
- - Charged Class 4 NICs on the profits chargeable under ITTOIA 2005 Part 2 Chapter 2, after capital allowances and the trading allowance, less trading losses under SSCBA 1992 Sch. 2 para. 3 (new `ni_class_4_profits`). Losses reduce only trade profits for Class 4 and carry forward until used.


## [2.112.0] - 2026-10-03

### Added

- Add `months_since_last_birthday`, which places a person's date of birth within their year of age, and `months_since_state_pension_age`.

### Changed

- - Read Attendance Allowance from its dataset award category when supplied, retained an explicitly approximate amount fallback otherwise, and applied Northern Ireland's separate AFIP and PIP commencement dates to the legacy severe disability premium.

### Fixed

- - Apply the pensioner Council Tax Reduction earnings disregards in England (SI 2012/2885 Sch 4), Wales (WSI 2013/3029 Sch 3) and Scotland (SSI 2012/319 Sch 2). A pension-age family's net earnings are now reduced by £25 a week for a lone parent, £10 for a couple and £5 otherwise, capped at net earnings, plus the £17.10 additional earnings disregard where a work condition is met and net earnings cover it (£37.10 in Scotland from 6 April 2020 to 4 April 2021). These sums are fixed in law and are not uprated. Before, pensioner CTR disregarded no earnings.
- - Uprate Northern Ireland domestic rates when projecting datasets, by the growth in the combined regional and district rate poundage (Department of Finance poundages to 2026-27, weighted by council domestic rates paid; 4.33% a year from 2027-28). Previously every projected year kept the data year's bills.
- Gave the generated adults in the Universal Credit capital-income and State Pension property tests explicit claimant-or-partner roles, so an adult under 20 is no longer presumed to be the other adult's child.
- The legacy benefit severe disability premium now qualifies on the benefits the Regulations list (Attendance Allowance, the DLA care component at the middle or highest rate, the PIP daily living component at either rate, and Armed Forces Independence Payment), pays a couple only when both partners qualify or the other partner is blind, pays the single rate when a carer benefit is paid for one partner, and is barred by a non-dependant aged 18 or over or by a carer benefit paid for the claimant. The tax credit severe disability flag now counts higher-rate Attendance Allowance and Armed Forces Independence Payment instead of all Armed Forces Compensation Scheme payments.
- Set State Pension age from each person's date of birth under Pensions Act 1995 Schedule 4 paragraph 1, including the rise from 66 to 67 for people born on or after 6 April 1960 (Pensions Act 2014 s.26): 66-year-olds move below State Pension age through 2026-27 and 2027-28, and are all below it from 2028-29. The Savings Credit age test, the split between basic and new State Pension, and additional State Pension now follow each person's own State Pension age.
- - Removed NumPy's generic-timedelta deprecation warning from State Pension date arithmetic without changing calculated dates.
- - Household calculations default an unspecified birthday position to six months before 6 October, implying a 6 April birth date and making an entered age of 66 above State Pension age at that check in 2026-27 and below it in 2027-28, while fractional ages or `months_since_last_birthday` can specify a different inferred birth date even when other people supply birthday months.
- - Added replacement guidance for reforms, structural reforms, nested scenarios and saved API policies using the removed male and female State Pension age parameters, rejecting obsolete simulation changes before resetting existing policy.
- - A member at least 16 years younger than a claimant flagged as a parent is now presumed to be their child at any age, unless a member under 20 and at least 16 years younger already explains the flag. So a flagged lone parent living only with an adult son or daughter is no longer inferred as a couple. Without any parent flag the under-20 limit stays, because survey childless couples carry no flags.

### Removed

- Remove `gov.dwp.state_pension.age.male` and `gov.dwp.state_pension.age.female`, a single State Pension age for each year. The statutory timetable by date of birth replaces them: `gov.dwp.state_pension.age.age_by_birth_date` (the age, in months) and `day_by_birth_date` (the day), with `male.age` and `male.born_before` for men born before 6 December 1953. A reform to State Pension age now changes those rows, for example the ages for births from a given date; code that read a State Pension age should read `state_pension_age` or `is_SP_age`.


## [2.111.2] - 2026-10-03

### Fixed

- - Apply the State Pension Credit severe disability addition's residence and carer conditions (SPC Regs 2002 Sch I paras 1-2 and reg 6(5)): no other resident aged 18 or over, ignoring qualifying-benefit recipients, blind people and qualifying young persons; and a carer benefit reduces or removes the addition only when it is paid for caring for a qualifying claimant or partner, so a claimant's own Carer's Allowance no longer removes it. Pension-age Housing Benefit and Council Tax Reduction follow once their severe disability premium reads this variable.


## [2.111.1] - 2026-10-03

### Fixed

- - Take the Housing Benefit earnings disregards from net earnings only, as SI 2006/213 and SI 2006/214 Schedule 4 require. The £5, £10 and £25 weekly disregards are now capped at the claimant's and partner's net earnings instead of being deducted from any income, including the State Pension, and they are no longer uprated with CPI. The additional earnings disregard is £17.10 (it was £37.10, uprated), and it now needs its work conditions (one person aged at least 25 working 30 hours, or 16 hours for lone parents, couples with a child and disabled workers) and net earnings covering the other disregards, childcare charges and £17.10. A working-age claimant on Income Support, income-based Jobseeker's Allowance or income-related Employment and Support Allowance has all earnings disregarded.


## [2.111.0] - 2026-10-03

### Added

- - Add `uc_has_offer_of_paid_work_starting_by_end_of_next_assessment_period` (reg 32(1)(a)) and `uc_is_temporarily_absent_from_claimant_household` (reg 32(1)(b)(iii)) inputs, and `uc_childcare_treated_as_in_paid_work` and `uc_unable_to_provide_childcare` for the Universal Credit childcare work condition.

### Fixed

- - Apply the Universal Credit childcare work condition's partner exceptions and treated-as-working rules (UC Regs 2013 reg 32). A couple now meets it when one member is in paid work and the other is in paid work or unable to provide childcare because of limited capability for work, caring for a severely disabled person or temporary absence. A claimant receiving statutory sick, maternity or paternity pay or maternity allowance is treated as in paid work.


## [2.110.0] - 2026-10-03

### Added

- Add `carers_allowance_pre_overlap`, `carer_support_payment_pre_overlap`, their `*_overlapping_benefits` totals, `overlapping_state_pension` and `is_entitled_to_carer_benefit`. `carers_allowance` and `carer_support_payment` are now the amounts payable after the overlapping-benefit reduction.

### Fixed

- - Reduced Carer's Allowance and Carer Support Payment by overlapping benefits, required claimant or partner entitlement for Pension Credit carer additions and carer premiums, and required payment for the Universal Credit non-dependant carer exemption.


## [2.109.8] - 2026-10-03

### Changed

- Require policyengine-core 3.32.12 or later, whose simulation branches copy cached arrays only when they first read them, so marginal tax rates and labour supply responses use less memory with unchanged results.

### Fixed

- - `cliff_evaluated` no longer flags people under 18. It now flags exactly the adults whose marginal tax rate is simulated.
  - The Universal Credit two-child limit age exemption reform (`gov.contrib.two_child_limit.age_exemption.universal_credit`) now lifts the limit for exempt families. It no longer switches the higher first-child amount on or off.
  - `Simulation.apply_dynamics` now works under pandas 3. It gives zero rather than NaN FTE responses for people without employment income, and no longer changes employment income for people it excludes from labour supply responses. It now reads exclusions and elasticities in the year the dynamics apply to.
  - Replaced `policyengine_uk/tests/behavioral_responses/test_labour_supply_responses.yaml`, which never ran, with tests in `test_behavioral_responses.py` that run without survey data.
- Added the 1 April 2023 National Minimum Wage and National Living Wage rates (S.I. 2023/354); 2023 had used the April 2022 rates, for example £9.50 instead of £10.42 for workers aged 23 or over. Every minimum wage rate now cites the statutory instrument that set it.


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

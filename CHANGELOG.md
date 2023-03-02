# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- OpenFisca-UK-Data version increased to 0.7.0.

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
- Point AFCS to AFCS_reported instead of AA_reported.
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

- OpenFisca-UK now runs from the official OpenFisca-Core.

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

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

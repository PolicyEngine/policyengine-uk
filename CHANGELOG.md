# Changelog

### 0.1.0

* First stable version with tax modelling, UBI reforms, and some benefits modelling.
* Details:
  - Income Tax, National Insurance, Capital Gains Tax.
  - All benefits are at least taken from survey reporting (can be switched on-off).
  - Child Benefit is modelled, others such as Income Support, JSA (both types), Tax Credits can be simulated/reformed but require more reviewing in how to account for discrepancies caused by take-up rates.
  - Four budget-neutral UBI reforms are implemented.
  - 15 test cases (unit and integration) testing benefits and taxes.
  - Simulation helper tools.

### 0.2.0

* Improvements to handling of time periods, MTRs and more
* Details:
  - Time periods now appropriate, using an implementation of WEEK for most benefits
  - MTRs handled properly and include a breakdown
  - Simulation tools are improved and included in a class

### 0.2.1

* Improved documentation of parameters
* Tests now occur in 2021 to ensure FY20-21 parameters are used
* Fixed bug in CB-HITC that caused overestimation

### 0.2.2

* Added Jupyter-Book documentation
* More detailed disability variables
* Fixed IndividualSim reform handling

### 0.2.3

* Bug fixes
* MicroDataFrame and MicroSeries returned by default

### 0.3.0

* New interfact for microsimulation
* Microdata now generated and loaded in-model
* Sources added to tax logic
* Tests added
* Variable time periods made more consistent
* Derivative calculations made more efficient and have more options

### 0.4.0

* OpenFisca-UK now runs from the official OpenFisca-Core
* Tests for variable naming conventions
* Postcode lookup optional features available
* LHA rates for all BRMA areas added

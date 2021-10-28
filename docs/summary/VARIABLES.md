# Variables

This document describes the input variables expected for microsimulation. None of them are compulsory - simulation will provide results for any subset of the variables, taking default values of 0. However for best results it is advisable to provide as many as possible.

## Entities

OpenFisca-UK deals with three main entity types:
- Person: a singular entity, either adult or child.
- Benefit Unit: standard unit for benefit entitlement, consisting of:
  - 1 adult
  - 1 spouse (optional)
  - Any number of dependent children (optional)
- Household: the formal address containing at least one person, and at least one benefit unit.

Note. Benefit Units are often referred to as "families". While this is often equivalent, it can be misleading given that families can often contain multiple benefit units.

## Entity variables

Each entity type has a set of variables which can be populated. In OpenFisca-UK, all variable definitions are organised by their entity type. These are detailed with descriptive statistics in ```docs\VARIABLE_STATS.md```.

IMPORTANT: All variables are weeklysed. This decision has been taken because the FRS weeklyises practically all variables - this has been preserved in OpenFisca-UK in order to minimise the risk of incorrectly imputing values. However, OpenFisca itself does not provide a WEEK period for variables, so currently all variables use the ETERNITY period. This should be interpreted as a variable describing an abstract week, instead of a particular week in time. Suggestions very welcome on other approaches than this imperfect solution.

## Obtaining datasets

OpenFisca country models can deal with either manual input of individual data, or CSV input for datasets. The primary use of OpenFisca-UK is in simulating tax changes across survey data - specifically, the Family Resources Survey. This is obtainable via the [UK Data Service](https://beta.ukdataservice.ac.uk/datacatalogue/series/series?id=200017), and comes in two forms, safeguarded (accessible only to academic members) and restricted (accessible only to vetted users in a secure environment). OpenFisca-UK has been designed to take inputs from the safeguarded version - for code which automates this process, see [frs-tools](https://github.com/nikhilwoodruff/frs-tools).

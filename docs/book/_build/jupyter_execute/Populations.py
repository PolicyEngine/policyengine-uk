# Populations

In calculating over weighted survey microdata, we use the Family Resources Survey. This isn't redistributable, but is available to academics. We use the package ```frs``` to convert the source TAB files into OpenFisca-compatible CSV files.

## Prerequisite: install and initialise ```frs```

The FRS package converts the Family Resources Survey into OpenFisca-UK input files by calculating the required variables for each person, benefit unit and household from the relational database format. It only needs to be set up once with the original files.

First, install and initialise the package ```frs``` (via ```pip install frs```):

!frs status

The FRS package needs to be pointed to a folder containing the source TAB files for a year of the FRS. Command-line hints are provided:

!frs --help

## Using ```PopulationSim```

The helper class ```PopulationSim``` uses the FRS package to load the input data:

from openfisca_uk import PopulationSim

sim = PopulationSim()

This helper class contains an OpenFisca Simulation object in ```sim.model```; the ```PopulationSim``` class provides some functions such as mapping between entity types, effective marginal tax rate calculation and DataFrame generation.

For example, we can generate a DataFrame containing all the variables for the ```person``` entity:

import pandas as pd

# entity_df(entity) generates a DataFrame with all entity-level variables

person_df = sim.entity_df(entity="person")

# display the results

person_df = person_df.filter(items=["age", "hours", "taxable_income", "total_tax", "unused_personal_allowance", "NI"])

person_df.describe()
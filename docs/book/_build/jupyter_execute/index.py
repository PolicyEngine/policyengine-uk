# OpenFisca-UK

This book contains an introduction to using OpenFisca-UK to model UK taxes and benefits. It is currently a work in progress and may be added to.

## Short demo

Calculating, for example, the average (employee-side) National Insurance liability by region can be done with the following code:

from openfisca_uk import PopulationSim # shortcut to FRS-populated simulations
from openfisca_uk.variables.household.attributes import Region
import pandas as pd
import numpy as np
from rdbl import gbp

sim = PopulationSim()
df = pd.DataFrame()
df["Region"] = sim.calc("region", period="2020").decode_to_str()
df["Population"] = sim.calc("people_in_household") * sim.calc("household_weight")
df["National Insurance"] = sim.calc("NI", map_to="household", period="2020") * sim.calc("household_weight")
df = df.groupby("Region").sum()
df["National Insurance per capita"] = df["National Insurance"] / df["Population"]
df["Population"] = df["Population"].apply(gbp)
df["National Insurance"] = df["National Insurance"].apply(gbp)
df["National Insurance per capita"] = df["National Insurance per capita"].apply(gbp)
df.sort_values(by="National Insurance per capita")




```{toctree}
:hidden:
:titlesonly:


Individuals
Populations
```

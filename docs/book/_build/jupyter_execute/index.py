# OpenFisca-UK

This book contains an introduction to using OpenFisca-UK to model UK taxes and benefits. It is currently a work in progress and may be added to.

## Contents

This book contains two main pages:
- Populations: demonstrating country-wide simulations using survey microdata.
- Individuals: demonstrating calculations and projections for hypothetical manually-defined people and groups.

## Short demo

Calculating, for example, the average (employee-side) National Insurance liability by region can be done with the following code:

from openfisca_uk import PopulationSim # shortcut to FRS-populated simulations
from openfisca_uk.variables.household.attributes import Region # for decoding region IDs
import pandas as pd
import numpy as np
from rdbl import gbp

# generate a UK simulation from survey microdata

sim = PopulationSim()
df = pd.DataFrame()

# calculate each variable by specifying the name and time period

# weights are needed to extrapolate to the UK population from
# survey respondents

df["Region"] = sim.calc("region", period="2020").decode_to_str()
df["Population"] = sim.calc("people_in_household", period="2020") * sim.calc("household_weight", period="2020")
df["National Insurance"] = sim.calc("NI", map_to="household", period="2020") * sim.calc("household_weight", period="2020")

# sum over UK regions

df = df.groupby("Region").sum()

# calculate per-capita NI

df["National Insurance per capita"] = df["National Insurance"] / df["Population"]

# make figures readable and display results

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

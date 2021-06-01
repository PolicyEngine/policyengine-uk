#!/usr/bin/env python
# coding: utf-8

# # Weighting
# 
# OpenFisca-UK calculates variables on each entity of a survey - people, benefit units (nuclear families) and households. Not everyone in the population is in the surveys, so each entity has a weight, all of which sum to the target population. OpenFisca-UK uses ```microdf```, a Python package that modifies ```pandas``` to handle survey weights behind-the-scenes, allowing the user to abstract away the concept of weighting. In practice, this means that results from the model already take into account weights, and the you can essentially treat the Series- and DataFrame-like objects returned from ```sim.calc``` and ```sim.df``` as if they contain everyone in the population. For example:

# In[2]:


from openfisca_uk import Microsimulation

sim = Microsimulation(year=2020)

sim.calc("income_tax")


# As can be seen above, this is not a Series but a MicroSeries, which associates weights with the results. The same happens with DataFrames (MicroDataFrames). We can see the statistics are different when weights are included.

# In[9]:


unweighted = sim.calc("income_tax").values.sum()
weighted = sim.calc("income_tax").sum()

import pandas as pd

pd.DataFrame({"Total Income Tax (£bn)": pd.Series([unweighted, weighted], index=["Unweighted", "Weighted"]).apply(lambda x: round(x / 1e+9, 1))})


#!/usr/bin/env python
# coding: utf-8

# # OpenFisca-UK
# 
# This book contains an introduction to using OpenFisca-UK to model UK taxes and benefits. It is currently a work in progress and may be added to. OpenFisca-UK is a microsimulation model of the UK tax and benefit system: it is a model which calculates variable values over UK entities from given policy parameters and structures. In practice, this gives it two main uses: calculating statistics under current tax and benefit law, and simulating effects of potential new changes to the legislation.
# 
# ## Short demo
# 
# ### Baseline estimation
# 
# Calculating, for example, the total tax (Income Tax and National Insurance) liability by region can be done with the following code:

# In[1]:


from openfisca_uk import Microsimulation
import pandas as pd

sim = Microsimulation(mode="frs", year=2018)

df = sim.df(["national_insurance", "income_tax", "people"])

summary = pd.DataFrame(df.groupby(sim.calc("region", map_to="person")).sum()).sort_values(by="people", ascending=False)
summary.national_insurance = summary.national_insurance.apply(lambda x: round(x / 1e+9, 1))
summary.income_tax = summary.income_tax.apply(lambda x: round(x / 1e+9, 1))
summary.people = summary.people.apply(lambda x: round(x / 1e+6, 1))
summary.columns = ["National Insurance (£bn)", "Income Tax (£bn)", "Population (millions)"]
summary


# ### Reform evaluation
# 
# Below is an example of simulating the effects of a reform (namely, increasing the basic rate of income tax from 20% to 23%). This uses the SPI mode of input - using administrative tax data instead of the FRS household survey.

# In[2]:


from openfisca_uk.api import *

def change_tax_parameters(parameters):
    parameters.tax.income_tax.rates.uk.brackets[0].rate.update(
        period=periods.period("year:2019:1"), value=0.23
    )
    return parameters

class reform(Reform):
    def apply(self):
        self.modify_parameters(change_tax_parameters)

baseline = Microsimulation(mode="spi")
reformed = Microsimulation(reform, mode="spi")
revenue = reformed.calc("tax").sum() - baseline.calc("tax").sum()
f"Revenue: £{round(revenue / 1e+9, 1)}bn"


# 
# ```{toctree}
# :hidden:
# :titlesonly:
# 
# 
# Reforms
# Weighting
# Individuals
# ```
# 

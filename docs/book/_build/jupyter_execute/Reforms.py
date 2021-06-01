#!/usr/bin/env python
# coding: utf-8

# # Reforms
# 
# To calculate the effects of a policy change, you need to:
# - Specify the reform using the OpenFisca API
# - Create a baseline simulation
# - Create a reformed simulation
# 
# OpenFisca-UK has a number of tools to aid this process, but the main process follows OpenFisca conventions.
# 
# ## About reforms
# 
# Reforms are essentially functions that take an existing tax-benefit system and modify it. When modelling a reform in OpenFisca-UK, you should first consider which parts of the reform are *structural* and which are *parametric* - these are the two main types of reform. Structural reforms change the decision-making process of the system (addding/removing variables, changing variable formulas), whereas parametric reforms replace the parameters of the system (rates, thresholds, other values that are looked up for the current time period).
# 
# OpenFisca-UK has the capability to consider tuples of reforms as reforms - for example, instead of writing one big tax reform, you can write a reform for each tax change, and perhaps permute them to see the effects of re-ordering the reform components. Or, you could write a reform and multiply a tuple contain it to repeatedly apply the reform.
# 
# ## Parametric reforms
# 
# Parametric reforms look like the following (this reform reduces the Personal Allowance):

# In[1]:


from openfisca_uk.api import *

# First, define a function to change the parameter tree

def modify_parameters(parameters):
    parameters.tax.income_tax.allowances.personal_allowance.amount.update(
        period=periods.period("year:2019:1"), # for a one-year period from 2019-01-01...
        value=10000 # set the personal allowance base amount to £10k/year
    )
    return parameters

# Then, define a reform class inheriting from Reform

class raise_tax(Reform):
    def apply(self):
        self.modify_parameters(modify_parameters)

# Reform specified, now we can estimate the effects

from openfisca_uk import Microsimulation

baseline = Microsimulation()
reformed = Microsimulation(raise_tax)

income = baseline.calc("household_net_income")
gain = reformed.calc("household_net_income") - income

import pandas as pd

summary = pd.DataFrame({
    "Disposable income change (£bn/year)": (gain.groupby(income.decile_rank()).sum() / 1e+9).apply(lambda x: round(x, 1))
})

summary.index = list(range(1, 11))

# Display household disposable income changes by decile
summary


# ## Structural reforms
# 
# Structural reforms involve adding, removing and changing variables. For example, raising tax rates would be a parametric reform, but adding a new tax *band* (e.g. Scottish rates) would be. See the following example below which introduces a universal basic income:

# In[2]:


# First, define the basic income variable

class basic_income(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    
    def formula(person, period, parameters):
        return where(person("is_adult", period), 3000, 1000)
    
# Then, include it in gross income

class gross_income(Variable):
    value_type = float
    entity = Person
    label = u"Gross income, including benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = [
            "employment_income",
            "pension_income",
            "self_employment_income",
            "property_income",
            "savings_interest_income",
            "dividend_income",
            "miscellaneous_income",
            "benefits",
            "basic_income" # add basic income to the component list
        ]
        return add(person, period, COMPONENTS)

# Finally, specify the reform class

class add_ubi(Reform):
    def apply(self):
        self.add_variable(basic_income)
        self.update_variable(gross_income)

# Estimate the effects

baseline = Microsimulation()
reformed = Microsimulation(add_ubi)

income = baseline.calc("household_net_income")
gain = reformed.calc("household_net_income") - income

import pandas as pd

summary = pd.DataFrame({
    "Disposable income change (£bn/year)": (gain.groupby(income.decile_rank()).sum() / 1e+9).apply(lambda x: round(x, 1))
})

summary.index = list(range(1, 11))

# Display household disposable income changes by decile
summary


# ## Combining reforms
# 
# Tuples of reforms are considered reforms in OpenFisca-UK. This means if we wanted to combine the tax reform with the basic income reform, we could do the following:

# In[3]:


tax_and_BI = (raise_tax, add_ubi)

def get_net_cost(reform):
    return Microsimulation(reform).calc("net_income").sum() - baseline.calc("net_income").sum()

net_costs = list(map(get_net_cost, (raise_tax, add_ubi, tax_and_BI)))

costs = pd.Series(net_costs, index=["Tax only", "UBI only", "Tax and UBI"]).apply(lambda x: round(x / 1e+9, 1))
pd.DataFrame({"Net cost": costs})


# ## General tips
# 
# - If you're trying out different policies, it's easier to write a function that declares the reform classes and returns them, e.g. ```make_tax_reform(basic_rate_rise: float) -> Reform```. Then, if you also have a function that transforms reform classes into results, you can use ```map```, etc. to analyse many reforms systematically. 
# - If you do the above, the ```tqdm``` module can come in useful - wrap a map call or list comprehension in ```list(tqdm(iterator))``` to have a progress bar keep track of the computation.
# - Only recalculate what you need to - the baseline simulation can often be left out of any reform functions.
# - Adding/subtracting amounts from variables is often easiest done by copy-pasting the original coded formula and working from there (see the source code for the formulas).

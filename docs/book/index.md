# PolicyEngine-UK

This book contains an introduction to using PolicyEngine-UK to model UK taxes and benefits. It is currently a work in progress and may be added to. PolicyEngine-UK is a microsimulation model of the UK tax and benefit system: it is a model which calculates variable values over UK entities from given policy parameters and structures. In practice, this gives it two main uses: calculating statistics under current tax and benefit law, and simulating effects of potential new changes to the legislation.

We're grateful to the [UKMOD](https://www.iser.essex.ac.uk/research/projects/ukmod) team for publishing descriptions of their model; our ability to reference these descriptions accelerated OpenFisca UK's development. UKMOD is maintained, developed and managed by the Centre for Microsimulation and Policy Analysis at the Institute for Social and Economic Research (ISER), University of Essex.

Code examples and outputs are re-run automatically on each new version of PolicyEngine-UK.

## Short demo

### Baseline estimates

Calculating, for example, the total Income Tax liability by region can be done with the following code:

```python
from policyengine_uk import Microsimulation
import pandas as pd

ENHANCED_FRS = "hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"

sim = Microsimulation(dataset=ENHANCED_FRS)

df = sim.calculate_dataframe(
    [
        "household_id",  # If the first variable is household level, the dataframe will project everything to households. Same for people.
        "income_tax",
        "region",
    ],
    period=2025,
)

df.groupby("region").income_tax.sum().sort_values(
    ascending=False
) / 1e9  # Weights automatically applied
```

### Reform evaluation

Below is an example of simulating the effects of a reform (namely, increasing the basic rate of income tax from 20% to 23%).

```python
from policyengine_uk.model_api import *


def change_tax_parameters(parameters):
    parameters.gov.hmrc.income_tax.rates.uk.brackets[0].rate.update(
        period=periods.period("year:2019:10"), value=0.23
    )
    return parameters


class reform(Reform):
    def apply(self):
        self.modify_parameters(change_tax_parameters)


baseline = Microsimulation(dataset=ENHANCED_FRS)
reformed = Microsimulation(dataset=ENHANCED_FRS, reform=reform)
revenue = (
    reformed.calculate("gov_balance", 2025).sum()
    - baseline.calc("gov_balance", 2025).sum()
)
f"Revenue: £{round(revenue / 1e9, 1)}bn"
```

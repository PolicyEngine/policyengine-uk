from openfisca_uk.tools.simulation import Simulation
import numpy as np

sim = Simulation(
    data_dir="C:\\Users\\Nikhil\\Documents\\Projects\\new-frs\\frs\\frs"
)
person = sim.entity_df(entity="person")
benunit = sim.entity_df(entity="benunit")
household = sim.entity_df(entity="household")
text = "# OpenFisca-UK Variable Statistics\n## Person\n"
for variable in person:
    name = variable
    label = sim.model.tax_benefit_system.variables[variable].label
    mean = round(np.mean(person[variable]), 2)
    median = round(np.median(person[variable]), 2)
    std = round(np.std(person[variable]), 2)
    text += f"{name}\n  - description: {label}\n  - mean: {mean}\n  - stddev: {std}\n  - median: {median}\n\n"

text += "## Benefit Unit\n"
for variable in benunit:
    name = variable
    label = sim.model.tax_benefit_system.variables[variable].label
    mean = round(np.mean(benunit[variable]), 2)
    median = round(np.median(benunit[variable]), 2)
    std = round(np.std(benunit[variable]), 2)
    text += f"{name}\n  - description: {label}\n  - mean: {mean}\n  - stddev: {std}\n  - median: {median}\n\n"

text += "## Household\n"
for variable in household:
    name = variable
    label = sim.model.tax_benefit_system.variables[variable].label
    mean = round(np.mean(household[variable]), 2)
    median = round(np.median(household[variable]), 2)
    std = round(np.std(household[variable]), 2)
    text += f"{name}\n  - description: {label}\n  - mean: {mean}\n  - stddev: {std}\n  - median: {median}\n\n"


with open("variable_stats.md", "w+") as f:
    f.write(text)

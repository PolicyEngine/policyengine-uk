from openfisca_uk.microdata.simulation import Microsimulation
import numpy as np
from tqdm import tqdm

sim = Microsimulation(mode="frs", year=2018, input_year=2019)

text = "# OpenFisca-UK Variable Statistics\n\nAll statistics generated from the 2018-19 Family Resources Survey, with simulation turned on.\n\n"

for name, var in tqdm(sim.simulation.tax_benefit_system.variables.items(), desc="Generating descriptions"):
    values = sim.calc(name)
    if var.value_type in (float, bool, int):
        text += f"\n- {name}:\n  - Type: {var.value_type}\n  - Entity: {var.entity.key}\n  - Description: {var.label}\n  - Mean: {values.mean()}\n  - Median: {values.median()}\n  - Stddev: {values.std()}\n  - Non-zero count: {(values > 0).sum()}\n\n"
    else:
        text += f"\n- {name}:\n  - Type: Categorical\n  - Entity: {var.entity.key}\n  - Description: {var.label}\n\n"


with open("variable_stats.md", "w+") as f:
    f.write(text)

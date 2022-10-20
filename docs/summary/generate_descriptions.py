from policyengine_uk.data import EnhancedFRS
from policyengine_uk import Microsimulation
from tqdm import tqdm

sim = Microsimulation(dataset=EnhancedFRS, year=2022)

text = "# OpenFisca-UK Variable Statistics\n\nAll statistics generated from the uprated (to 2022) 2019-20 Family Resources Survey, with simulation turned on.\n\n"

for name, var in tqdm(
    sim.simulation.tax_benefit_system.variables.items(),
    desc="Generating descriptions",
):
    values = sim.calc(name, 2022)
    if var.value_type in (float, bool, int):
        text += f"\n- {name}:\n  - Type: {var.value_type.__name__}\n  - Entity: {var.entity.key}\n  - Description: {var.label}\n  - Mean: {round(values.mean(), 1):,}\n  - Median: {round(values.median(), 1):,}\n  - Stddev: {round(values.std(), 1):,}\n  - Non-zero count: {(values > 0).sum():,}\n\n"
    else:
        text += f"\n- {name}:\n  - Type: Categorical\n  - Entity: {var.entity.key}\n  - Description: {var.label}\n\n"


with open("docs/summary/VARIABLE_STATS.md", "w+") as f:
    f.write(text)

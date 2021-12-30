from openfisca_uk_data.datasets.frs.frs_enhanced.frs_enhanced import (
    FRSEnhanced,
)
from openfisca_uk import Microsimulation
from openfisca_uk_data import FRSEnhanced
from tqdm import tqdm

sim = Microsimulation(dataset=FRSEnhanced, year=2019)

text = "# OpenFisca-UK Variable Statistics\n\nAll statistics generated from the uprated (to 2020) 2018-19 Family Resources Survey, with simulation turned on.\n\n"

for name, var in tqdm(
    sim.simulation.tax_benefit_system.variables.items(),
    desc="Generating descriptions",
):
    values = sim.calc(name, 2021)
    if var.value_type in (float, bool, int):
        text += f"\n- {name}:\n  - Type: {var.value_type.__name__}\n  - Entity: {var.entity.key}\n  - Description: {var.label}\n  - Mean: {round(values.mean(), 1:,)}\n  - Median: {round(values.median(), 1):,}\n  - Stddev: {round(values.std(), 1):,}\n  - Non-zero count: {(values > 0).sum():,}\n\n"
    else:
        text += f"\n- {name}:\n  - Type: Categorical\n  - Entity: {var.entity.key}\n  - Description: {var.label}\n\n"


with open("docs/summary/VARIABLE_STATS.md", "w+") as f:
    f.write(text)

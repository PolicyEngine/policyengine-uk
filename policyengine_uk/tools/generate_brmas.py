from policyengine_uk.data.gov import lha_list_of_rents, brma_to_region
import numpy as np
import pandas as pd
from policyengine_uk.variables.household.demographic.locations import BRMAName
from policyengine_uk import Microsimulation

sim = Microsimulation()
region = sim.populations["benunit"].household("region", 2023).decode_to_str()
lha_category = sim.calculate("LHA_category")

brma = np.empty(len(region), dtype=object)

# Sample from a random BRMA in the region, weighted by the number of observations in each BRMA
lha_list_of_rents = lha_list_of_rents.copy()

for possible_region in lha_list_of_rents.region.unique():
    for possible_lha_category in lha_list_of_rents.lha_category.unique():
        lor_mask = (lha_list_of_rents.region == possible_region) & (
            lha_list_of_rents.lha_category == possible_lha_category
        )
        mask = (region == possible_region) & (
            lha_category == possible_lha_category
        )
        brma[mask] = lha_list_of_rents[lor_mask].brma.sample(
            n=len(region[mask]), replace=True
        )

# Convert benunit-level BRMAs to household-level BRMAs (pick a random one)

df = pd.DataFrame(
    {
        "brma": brma,
        "household_id": sim.populations["benunit"].household(
            "household_id", 2023
        ),
    }
)

df = df.groupby("household_id").brma.aggregate(lambda x: x.sample(n=1).iloc[0])
brmas = df[sim.calculate("household_id")].values

df.to_csv("enhanced_frs_brmas.csv.gz", index=False, compression="gzip")

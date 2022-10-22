import logging
from typing import Tuple
import pandas as pd
from policyengine_core.data import Dataset, PrivateDataset
import h5py
from policyengine_uk.data.datasets.lcfs.raw_lcfs import RawLCFS
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER

CATEGORY_NAMES = dict(
    # Top-level COICOP categories
    P601="Food and non-alcoholic beverages consumption",
    P602="Alcohol and tobacco consumption",
    P603="Clothing and footwear consumption",
    P604="Housing, water and electricity consumption",
    P605="Household furnishings consumption",
    P606="Health consumption",
    P607="Transport consumption",
    P608="Communication consumption",
    P609="Recreation consumption",
    P610="Education consumption",
    P611="Restaurants and hotels consumption",
    P612="Miscellaneous consumption",
    # Specific items
    C72211="Petrol spending",
    C72212="Diesel spending",
    P537="Domestic energy consumption",
)

name_to_variable_name = {
    category: category.replace(",", "")
    .replace(" ", "_")
    .replace("-", "_")
    .lower()
    + ("_consumption" if category[1:] == "P" else "")
    for category in CATEGORY_NAMES.values()
}

CATEGORY_VARIABLES = list(name_to_variable_name.values())

HOUSEHOLD_LCF_RENAMES = {
    "G018": "is_adult",
    "G019": "is_child",
    "Gorx": "region",
}
PERSON_LCF_RENAMES = {
    "B303p": "employment_income",
    "B3262p": "self_employment_income",
    "B3381": "state_pension",
    "P049p": "pension_income",
}
REGIONS = {
    1: "NORTH_EAST",
    2: "NORTH_WEST",
    3: "YORKSHIRE",
    4: "EAST_MIDLANDS",
    5: "WEST_MIDLANDS",
    6: "EAST_OF_ENGLAND",
    7: "LONDON",
    8: "SOUTH_EAST",
    9: "SOUTH_WEST",
    10: "WALES",
    11: "SCOTLAND",
    12: "NORTHERN_IRELAND",
}


class LCFS(PrivateDataset):
    name = "lcfs"
    label = "LCFS"
    data_format = Dataset.ARRAYS
    folder_path = policyengine_uk_MICRODATA_FOLDER

    is_openfisca_compatible = True

    def generate(self, year: int):
        if year in self.years:
            self.remove(year)
        # Load raw FRS tables
        year = int(year)

        if len(RawLCFS.years) == 0:
            raise FileNotFoundError(
                "Raw LCFS not found. Please run `openfisca-uk data lcfs generate [year]` first."
            )

        if year > max(RawLCFS.years):
            logging.warning("Uprating a previous version of the LCFS.")
            if len(self.years) == 0:
                self.generate(max(RawLCFS.years))
            if len(self.years) > 0:
                lcfs_year = max(self.years)
                from policyengine_uk import Microsimulation

                sim = Microsimulation(
                    dataset=self, dataset_year=max(self.years)
                )
                lcfs = h5py.File(self.file(year), mode="w")
                for variable in self.keys(lcfs_year):
                    lcfs[variable] = sim.calc(variable).values
                lcfs.close()
                return
        households = RawLCFS.load(2019, "lcfs_2019_dvhh_ukanon")
        people = RawLCFS.load(2019, "lcfs_2019_dvper_ukanon201920")
        spending = (
            households[list(CATEGORY_NAMES.keys())].unstack().reset_index()
        )
        spending.columns = "category", "household", "spending"
        spending["household"] = households.case[spending.household].values
        households = households.set_index("case")
        spending.category = spending.category.map(CATEGORY_NAMES).map(
            name_to_variable_name
        )
        spending.spending *= 52
        spending["weight"] = (
            households.weighta[spending.household].values * 100
        )
        spending = pd.DataFrame(spending)

        for category in spending.category.unique():
            spending[category] = (
                spending.category == category
            ) * spending.spending

        lcf_df = (
            pd.DataFrame(
                spending[["household", "weight"] + CATEGORY_VARIABLES]
            )
            .groupby("household")
            .sum()
        )

        # Add in LCFS variables that also appear in the FRS-based microsimulation model

        lcf_household_vars = households[
            list(HOUSEHOLD_LCF_RENAMES.keys())
        ].rename(columns=HOUSEHOLD_LCF_RENAMES)
        lcf_person_vars = (
            people[list(PERSON_LCF_RENAMES) + ["case"]]
            .rename(columns=PERSON_LCF_RENAMES)
            .groupby("case")
            .sum()
        )

        lcf_with_demographics = pd.concat(
            [
                lcf_df,
                lcf_household_vars,
                lcf_person_vars,
            ],
            axis=1,
        )

        # LCFS incomes are weekly - convert to annual
        for variable in PERSON_LCF_RENAMES.values():
            lcf_with_demographics[variable] *= 52

        lcf_with_demographics.region = lcf_with_demographics.region.map(
            REGIONS
        )
        lcfs = lcf_with_demographics.sort_index()

        lcfs = lcfs.rename(columns=dict(weight="household_weight"))

        entity_index = (
            lcfs.index.values
        )  # One-person households for simplicity for now

        lcfs["household_weight"] = households.weighta * 1_000

        with h5py.File(self.file(year), mode="w") as f:
            for entity_id_var in [
                "person_id",
                "benunit_id",
                "household_id",
                "person_benunit_id",
                "person_household_id",
            ]:
                f[entity_id_var] = entity_index

            f["person_benunit_role"] = ["adult"] * len(entity_index)
            f["person_household_role"] = ["adult"] * len(entity_index)
            f["person_state_id"] = [1] * len(entity_index)
            f["state_id"] = [1]

            for variable in lcfs.columns:
                f[variable] = lcfs[variable].values


LCFS = LCFS()

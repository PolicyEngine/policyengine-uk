import logging
from policyengine_core.data import Dataset, PrivateDataset
import h5py
from policyengine_uk.data.datasets.was.raw_was import RawWAS
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER

RENAMES = {
    "R7xshhwgt": "household_weight",
    # Components for estimating land holdings.
    "DVLUKValR7_sum": "owned_land",  # In the UK.
    "DVPropertyR7": "property_wealth",
    "DVFESHARESR7_aggr": "emp_shares_options",
    "DVFShUKVR7_aggr": "uk_shares",
    "DVIISAVR7_aggr": "investment_isas",
    "DVFCollVR7_aggr": "unit_investment_trusts",
    "TotpenR7_aggr": "pensions",
    "DvvalDBTR7_aggr": "db_pensions",
    # Predictors for fusing to FRS.
    "dvtotgirR7": "gross_income",
    "NumAdultW7": "num_adults",
    "NumCh18W7": "num_children",
    # Household Gross Annual income from occupational or private pensions
    "DVGIPPENR7_AGGR": "pension_income",
    "DVGISER7_AGGR": "self_employment_income",
    # Household Gross annual income from investments
    "DVGIINVR7_aggr": "capital_income",
    # Household Total Annual Gross employee income
    "DVGIEMPR7_AGGR": "employment_income",
    "HBedrmW7": "num_bedrooms",
    "GORR7": "region",
    "DVPriRntW7": "is_renter",  # {1, 2} TODO: Get codebook values.
    "CTAmtW7": "council_tax",
    # Other columns for reference.
    "DVLOSValR7_sum": "non_uk_land",
    "HFINWNTR7_Sum": "net_financial_wealth",
    "DVLUKDebtR7_sum": "uk_land_debt",
    "HFINWR7_Sum": "gross_financial_wealth",
    "TotWlthR7": "wealth",
    "DVhvalueR7": "main_residence_value",
    "DVHseValR7_sum": "other_residential_property_value",
    "DVBlDValR7_sum": "non_residential_property_value",
    "DVTotinc_bhcR7": "household_net_income",
}

VARIABLES = [
    "household_net_income",
    "num_adults",
    "num_children",
    "pension_income",
    "employment_income",
    "self_employment_income",
    "capital_income",
    "num_bedrooms",
    "council_tax",
    "is_renting",
    "owned_land",
    "property_wealth",
    "corporate_wealth",
    "gross_financial_wealth",
    "net_financial_wealth",
    "main_residence_value",
    "other_residential_property_value",
    "non_residential_property_value",
]

RENAMES = {key.lower(): value for key, value in RENAMES.items()}


class WAS(PrivateDataset):
    name = "was"
    label = "WAS"
    data_format = Dataset.ARRAYS
    folder_path = policyengine_uk_MICRODATA_FOLDER

    is_openfisca_compatible = True

    def generate(self, year: int):
        if year in self.years:
            self.remove(year)
        # Load raw FRS tables
        year = int(year)

        if len(RawWAS.years) == 0:
            raise FileNotFoundError(
                "Raw WAS not found. Please run `openfisca-uk data was generate [year]` first."
            )

        if year > max(RawWAS.years):
            logging.warning("Uprating a previous version of the WAS.")
            if len(self.years) == 0:
                self.generate(max(RawWAS.years))
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

        assert (
            year == 2019
        ), "Currently, only the 2019 WAS is supported (table name changes not yet implemented)"
        # The 2019 year is actually over the two-year period from 2018 to 2020, but is usually referred to as 2019.

        # TODO: Handle different WAS releases

        was = RawWAS.load(year, "was_round_7_hhold_eul_jan_2022")

        was = was.rename(columns={col: col.lower() for col in was.columns})

        to_remove = []
        to_add = {}

        for key in RENAMES:
            old_key = str(key)
            if key not in was.columns:
                key = key.replace("r", "w")
            if key not in was.columns:
                key = key.replace("w", "r")
            if key not in was.columns:
                raise ValueError(f"Could not find column {key}")
            else:
                to_add[key] = RENAMES[old_key]
                to_remove.append(old_key)

        for key in to_remove:
            del RENAMES[key]

        for key in to_add:
            RENAMES[key] = to_add[key]

        was = was.rename(columns=RENAMES).fillna(0)[list(RENAMES.values())]

        was["is_renting"] = was["is_renter"] == 1

        was.household_net_income *= 52  # WAS uses monthly income

        was["non_db_pensions"] = was.pensions - was.db_pensions
        was["corporate_wealth"] = was[
            [
                "non_db_pensions",
                "emp_shares_options",
                "uk_shares",
                "investment_isas",
                "unit_investment_trusts",
            ]
        ].sum(axis=1)

        entity_index = (
            was.index.values
        )  # One-person households for simplicity for now

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

            for variable in VARIABLES + ["household_weight"]:
                f[variable] = was[variable].values


WAS = WAS()

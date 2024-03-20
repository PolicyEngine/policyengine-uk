from survey_enhance.impute import Imputation
import pandas as pd
from pathlib import Path
import numpy as np
import yaml

WAS_TAB_FOLDER = Path("/Users/nikhil/ukda/was_2006_20")


REGIONS = {
    1: "NORTH_EAST",
    2: "NORTH_WEST",
    4: "YORKSHIRE",
    5: "EAST_MIDLANDS",
    6: "WEST_MIDLANDS",
    7: "EAST_OF_ENGLAND",
    8: "LONDON",
    9: "SOUTH_EAST",
    10: "SOUTH_WEST",
    11: "WALES",
    12: "SCOTLAND",
}

PREDICTOR_VARIABLES = [
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
    "region",
]

IMPUTE_VARIABLES = [
    "owned_land",
    "property_wealth",
    "corporate_wealth",
    "gross_financial_wealth",
    "net_financial_wealth",
    "main_residence_value",
    "other_residential_property_value",
    "non_residential_property_value",
    "savings",
]


def generate_was_table(was: pd.DataFrame):
    was = was.rename(columns={col: col.lower() for col in was.columns})

    to_remove = []
    to_add = {}

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
        "DVSaValR7_aggr": "savings",
    }

    RENAMES = {x.lower(): y for x, y in RENAMES.items()}

    for key in RENAMES:
        key = key.lower()
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
    was["region"] = was["region"].map(REGIONS)
    return was


def save_imputation_models():
    was = pd.read_csv(
        WAS_TAB_FOLDER / "was_round_7_hhold_eul_march_2022.tab",
        sep="\t",
        low_memory=False,
    )
    was = generate_was_table(was)

    wealth = Imputation()

    wealth.train(
        was[PREDICTOR_VARIABLES],
        was[IMPUTE_VARIABLES],
    )
    wealth.save(
        Path(__file__).parents[3] / "storage" / "imputations" / "wealth.pkl"
    )

    # Generate a targets.yaml file with [variable]: [weighted sum]
    # for each variable in the imputation model.
    targets = {}
    for var in IMPUTE_VARIABLES:
        targets[var] = float((was[var] * was["household_weight"]).sum())

    with open(
        Path(__file__).parents[3]
        / "storage"
        / "imputations"
        / "wealth_targets.yaml",
        "w",
    ) as f:
        yaml.dump(targets, f)


if __name__ == "__main__":
    save_imputation_models()

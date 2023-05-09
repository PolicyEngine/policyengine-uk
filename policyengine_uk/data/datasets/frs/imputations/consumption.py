from survey_enhance.impute import Imputation
import pandas as pd
from pathlib import Path
import numpy as np
import yaml

LCFS_TAB_FOLDER = Path("/Users/nikhil/ukda/lcfs_2020_21")

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

HOUSEHOLD_LCF_RENAMES = {
    "G018": "is_adult",
    "G019": "is_child",
    "Gorx": "region",
    "P389p": "household_net_income",
    "weighta": "household_weight",
}
PERSON_LCF_RENAMES = {
    "B303p": "employment_income",
    "B3262p": "self_employment_income",
    "B3381": "state_pension",
    "P049p": "pension_income",
}

CONSUMPTION_VARIABLE_RENAMES = {
    "P601": "food_and_non_alcoholic_beverages_consumption",
    "P602": "alcohol_and_tobacco_consumption",
    "P603": "clothing_and_footwear_consumption",
    "P604": "housing_water_and_electricity_consumption",
    "P605": "household_furnishings_consumption",
    "P606": "health_consumption",
    "P607": "transport_consumption",
    "P608": "communication_consumption",
    "P609": "recreation_consumption",
    "P610": "education_consumption",
    "P611": "restaurants_and_hotels_consumption",
    "P612": "miscellaneous_consumption",
    "C72211": "petrol_spending",
    "C72212": "diesel_spending",
    "P537": "domestic_energy_consumption",
}


PREDICTOR_VARIABLES = [
    "is_adult",
    "is_child",
    "region",
    "employment_income",
    "self_employment_income",
    "pension_income",
    "household_net_income",
]

IMPUTATIONS = [
    "food_and_non_alcoholic_beverages_consumption",
    "alcohol_and_tobacco_consumption",
    "clothing_and_footwear_consumption",
    "housing_water_and_electricity_consumption",
    "household_furnishings_consumption",
    "health_consumption",
    "transport_consumption",
    "communication_consumption",
    "recreation_consumption",
    "education_consumption",
    "restaurants_and_hotels_consumption",
    "miscellaneous_consumption",
    "petrol_spending",
    "diesel_spending",
    "domestic_energy_consumption",
]


def generate_lcfs_table(
    lcfs_person: pd.DataFrame, lcfs_household: pd.DataFrame
):
    person = lcfs_person.rename(columns=PERSON_LCF_RENAMES)
    household = lcfs_household.rename(columns=HOUSEHOLD_LCF_RENAMES)
    household["region"] = household["region"].map(REGIONS)
    household = household.rename(columns=CONSUMPTION_VARIABLE_RENAMES)
    for variable in list(CONSUMPTION_VARIABLE_RENAMES.values()) + [
        "household_net_income"
    ]:
        household[variable] = household[variable] * 52
    for variable in PERSON_LCF_RENAMES.values():
        household[variable] = (
            person[variable].groupby(person.case).sum()[household.case] * 52
        )
    household.household_weight *= 1_000
    return household[
        PREDICTOR_VARIABLES + IMPUTATIONS + ["household_weight"]
    ].dropna()


def save_imputation_models():
    consumption = Imputation()
    lcfs_household = pd.read_csv(
        LCFS_TAB_FOLDER / "lcfs_2020_dvhh_ukanon.tab",
        delimiter="\t",
        low_memory=False,
    )
    lcfs_person = pd.read_csv(
        LCFS_TAB_FOLDER / "lcfs_2020_dvper_ukanon202021.tab", delimiter="\t"
    )
    household = generate_lcfs_table(lcfs_person, lcfs_household)
    consumption.train(
        household[PREDICTOR_VARIABLES],
        household[IMPUTATIONS],
    )
    consumption.save(
        Path(__file__).parents[3]
        / "storage"
        / "imputations"
        / "consumption.pkl"
    )

    # Generate a targets.yaml file with [variable]: [weighted sum]
    # for each variable in the imputation model.
    targets = {}
    for var in IMPUTATIONS:
        targets[var] = float(
            (household[var] * household["household_weight"]).sum()
        )

    with open(
        Path(__file__).parents[3]
        / "storage"
        / "imputations"
        / "consumption_targets.yaml",
        "w",
    ) as f:
        yaml.dump(targets, f)


if __name__ == "__main__":
    save_imputation_models()

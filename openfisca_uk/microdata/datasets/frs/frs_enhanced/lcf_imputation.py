from typing import Tuple
import pandas as pd
from pathlib import Path
from openfisca_uk.microdata.datasets.frs.frs import FRS
from openfisca_uk.microdata.datasets.lcf import RawLCF
from microdf import MicroDataFrame
import synthimpute as si

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


def impute_consumption(year: int, dataset: type = FRS) -> pd.Series:
    """Impute consumption by fitting a random forest model.

    Args:
        year (int): The year of LCFS to use.
        dataset (type): The dataset to use.

    Returns:
        pd.Series: The imputed consumption categories.
    """

    # Load the LCF data with carbon consumption
    lcf = load_lcfs(year)

    # Impute LCF consumption to FRS households
    return impute_consumption_to_FRS(lcf, year, dataset)


def impute_consumption_to_FRS(
    lcf: MicroDataFrame, year: int, dataset: type = FRS
) -> pd.Series:
    """Impute consumption to the FRS.

    Args:
        lcf (MicroDataFrame): The LCF data.
        year (int): The year of the FRS to use.
        dataset (type): The dataset to use.

    Returns:
        MicroDataFrame: The imputed consumption.
    """

    from openfisca_uk import Microsimulation

    sim = Microsimulation(
        dataset=dataset,
        year=year,
    )

    frs = sim.df(
        [
            "is_adult",
            "is_child",
            "region",
            "employment_income",
            "self_employment_income",
            "state_pension",
            "pension_income",
        ],
        map_to="household",
    )

    frs.region = frs.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )
    lcf.region = lcf.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )
    return si.rf_impute(
        x_train=lcf.drop(CATEGORY_VARIABLES, axis=1),
        y_train=lcf[CATEGORY_VARIABLES],
        x_new=frs,
        verbose=True,
        ignore_target=True,
    )


def load_lcfs(year: int) -> MicroDataFrame:
    """Load LCF data.

    Args:
        year (int): The year of LCFS to use.

    Returns:
        MicroDataFrame: The LCF data
    """
    households, people = load_and_process_lcf(year)
    spending = households[list(CATEGORY_NAMES.keys())].unstack().reset_index()
    spending.columns = "category", "household", "spending"
    spending["household"] = households.case[spending.household].values
    households = households.set_index("case")
    spending.category = spending.category.map(CATEGORY_NAMES).map(
        name_to_variable_name
    )
    spending.spending *= 52
    spending["weight"] = households.weighta[spending.household].values * 1000
    spending = MicroDataFrame(spending, weights=spending.weight)

    for category in spending.category.unique():
        spending[category] = (
            spending.category == category
        ) * spending.spending

    lcf_df = (
        pd.DataFrame(spending[["household", "weight"] + CATEGORY_VARIABLES])
        .groupby("household")
        .sum()
    )

    # Add in LCF variables that also appear in the FRS-based microsimulation model

    lcf_household_vars = households[list(HOUSEHOLD_LCF_RENAMES.keys())].rename(
        columns=HOUSEHOLD_LCF_RENAMES
    )
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

    # LCF incomes are weekly - convert to annual
    for variable in PERSON_LCF_RENAMES.values():
        lcf_with_demographics[variable] *= 52

    lcf_with_demographics.region = lcf_with_demographics.region.map(REGIONS)
    lcf = lcf_with_demographics.sort_index()

    # Return household-level LCF dataset with categorised consumption
    # and FRS-shared columns
    return MicroDataFrame(lcf, weights=households.weighta[lcf.index] * 1000)


def load_and_process_lcf(
    year: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and process the LCF and NCFS summary data.

    Args:
        year (int): The year of LCFS to use.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: The LCF household and person tables.
    """
    households = RawLCF.load(2019, "lcfs_2019_dvhh_ukanon")
    people = RawLCF.load(2019, "lcfs_2019_dvper_ukanon201920")

    return households, people

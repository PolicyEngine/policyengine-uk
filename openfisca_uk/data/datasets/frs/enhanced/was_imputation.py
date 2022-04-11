from microdf.generic import MicroDataFrame
from openfisca_uk.data.datasets.was.raw_was import RawWAS
from openfisca_uk.data.datasets.frs.frs import FRS
import pandas as pd
import microdf as mdf
import synthimpute as si


def impute_wealth(year: int, dataset: type = FRS) -> pd.Series:
    """Impute wealth by fitting a random forest model.

    Args:
        year (int): The year of simulation.
        dataset (type): The dataset to use.

    Returns:
        pd.Series: The predicted wealth values.
    """

    was = load_and_process_was()

    from openfisca_uk import Microsimulation

    sim = Microsimulation(
        dataset=dataset,
        year=year,
    )

    TRAIN_COLS = [
        "household_net_income",
        "num_adults",
        "num_children",
        "pension_income",
        "employment_income",
        "self_employment_income",
        "investment_income",
        "num_bedrooms",
        "council_tax",
        "is_renting",
    ]

    IMPUTE_COLS = [
        "owned_land",
        "property_wealth",
        "corporate_wealth",
        "gross_financial_wealth",
        "net_financial_wealth",
        "main_residence_value",
        "other_residential_property_value",
        "non_residential_property_value",
    ]

    # FRS has investment income split between dividend and savings interest.
    frs_cols = [i for i in TRAIN_COLS if i != "investment_income"]
    frs_cols += [
        "dividend_income",
        "savings_interest_income",
        "people",
        "household_net_income",
        "household_weight",
    ]

    frs = sim.df(frs_cols, map_to="household", period=year)
    frs["investment_income"] = (
        frs.savings_interest_income + frs.dividend_income
    )

    return si.rf_impute(
        x_train=was[TRAIN_COLS],
        y_train=was[IMPUTE_COLS],
        x_new=frs[TRAIN_COLS],
        verbose=True,
        n_estimators=3, # For debugging
    )


def load_and_process_was() -> pd.DataFrame:
    """Process the Wealth and Assets Survey household wealth file.

    Returns:
            pd.DataFrame: The processed dataframe.
    """
    RENAMES = {
        "R7xshhwgt": "weight",
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
        "DVGIINVR7_aggr": "investment_income",
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

    RENAMES = {key.lower(): value for key, value in RENAMES.items()}

    # TODO: Handle different WAS releases

    was = RawWAS.load(2019, "was_round_7_hhold_eul_jan_2022")

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
    return MicroDataFrame(was, weights=was.weight)

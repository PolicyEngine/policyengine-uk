from survey_enhance.impute import Imputation
import pandas as pd
from pathlib import Path
import numpy as np

SPI_TAB_FOLDER = Path("/Users/nikhil/ukda/spi_2019_20")
SPI_RENAMES = dict(
    pension_income="PENSION",
    self_employment_income="PROFITS",
    property_income="INCPROP",
    savings_interest_income="INCBBS",
    dividend_income="DIVIDENDS",
    blind_persons_allowance="BPADUE",
    married_couples_allowance="MCAS",
    gift_aid="GIFTAID",
    capital_allowances="CAPALL",
    deficiency_relief="DEFICIEN",
    covenanted_payments="COVNTS",
    charitable_investment_gifts="GIFTINV",
    employment_expenses="EPB",
    other_deductions="MOTHDED",
    pension_contributions="PENSRLF",
    person_weight="FACT",
    benunit_weight="FACT",
    household_weight="FACT",
    state_pension="SRP",
)


def generate_spi_table(spi: pd.DataFrame):
    LOWER = np.array([0, 16, 25, 35, 45, 55, 65, 75])
    UPPER = np.array([16, 25, 35, 45, 55, 65, 75, 80])
    age_range = spi.AGERANGE
    spi["age"] = LOWER[age_range] + np.random.rand(len(spi)) * (
        UPPER[age_range] - LOWER[age_range]
    )

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

    spi["region"] = np.array([REGIONS.get(x, "UNKNOWN") for x in spi.GORCODE])

    spi["gender"] = np.where(spi.SEX == 1, "MALE", "FEMALE")

    for rename in SPI_RENAMES:
        spi[rename] = spi[SPI_RENAMES[rename]]

    spi["employment_income"] = spi[["PAY", "EPB", "TAXTERM"]].sum(axis=1)

    return spi


PREDICTORS = [
    "age",
    "gender",
    "region",
]

IMPUTATIONS = [
    "employment_income",
    "self_employment_income",
    "savings_interest_income",
    "dividend_income",
    "pension_income",
    "employment_expenses",
    "property_income",
    "gift_aid",
    "pension_contributions",
]


def save_imputation_models():
    income = Imputation()
    spi = pd.read_csv(SPI_TAB_FOLDER / "put1920uk.tab", delimiter="\t")
    spi = generate_spi_table(spi)
    spi = spi[PREDICTORS + IMPUTATIONS]
    income.train(spi[PREDICTORS], spi[IMPUTATIONS])
    income.save(
        Path(__file__).parents[3] / "storage" / "imputations" / "income.pkl"
    )


if __name__ == "__main__":
    save_imputation_models()

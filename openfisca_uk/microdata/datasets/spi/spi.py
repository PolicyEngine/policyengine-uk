from openfisca_uk.microdata.datasets.spi.raw_spi import RawSPI
from openfisca_core.model_api import *
from openfisca_uk.microdata.utils import *
import pandas as pd
from pandas import DataFrame
import h5py

max_ = np.maximum
where = np.where


@dataset
class SPI:
    name = "spi"
    model = UK

    def generate(year: int) -> None:
        """Generates the SPI-based input dataset for OpenFisca-UK.

        Args:
                year (int): The year to generate for (uses the raw SPI from this year)
        """

        main = RawSPI.load(year, "main").fillna(0)
        spi = h5py.File(SPI.file(year), mode="w")

        main = extend_spi_main_table(main)

        add_id_variables(spi, main)
        add_demographics(spi, main)
        add_incomes(spi, main)

        # Generate OpenFisca-UK variables and save
        spi.close()


def extend_spi_main_table(main: DataFrame) -> DataFrame:
    """Extends the main SPI table to include adults and children with
    zero income, so that the total number of people is the UK population.

    Args:
        main (DataFrame): The main SPI table.

    Returns:
        DataFrame: The modified table.
    """

    from openfisca_uk import Microsimulation
    from openfisca_uk.microdata import FRS

    sim = Microsimulation(dataset=FRS)

    population_in_spi_percentage = main.FACT.sum() / sim.calc("people").sum()

    RENAMES = dict(
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
        employment_income="PAY",
        state_pension="SRP",
        miscellaneous_income="OTHERINC",
        pays_scottish_income_tax="SCOT_TXP",
        person_weight="FACT",
    )

    in_frs_and_not_spi = (
        sim.calc("total_income").rank(pct=True)
        < 1 - population_in_spi_percentage
    )

    missing_spi = sim.df(list(RENAMES))[in_frs_and_not_spi].rename(
        columns=RENAMES
    )

    LOWER = np.array([0, 16, 25, 35, 45, 55, 65, 75])
    UPPER = np.array([16, 25, 35, 45, 55, 65, 75, 80])
    CODE = np.array([1, 2, 3, 4, 5, 6, 7])
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
    age = sim.calc("age")[in_frs_and_not_spi]
    missing_spi["AGERANGE"] = 0
    for lower, upper, code in zip(LOWER, UPPER, CODE):
        missing_spi["AGERANGE"] += np.where(
            (age < upper) & (age >= lower), code, 0
        )

    missing_spi["GORCODE"] = sim.calc("region", map_to="person")[
        in_frs_and_not_spi
    ].map({y: x for x, y in REGIONS.items()})

    return pd.concat([main, missing_spi]).fillna(0)


def add_id_variables(spi: h5py.File, main: DataFrame):
    spi["person_id"] = main.index
    spi["person_benunit_id"] = main.index
    spi["person_household_id"] = main.index
    spi["benunit_id"] = main.index
    spi["household_id"] = main.index
    spi["role"] = np.array(["adult"] * len(main)).astype("S")
    spi["person_state_role"] = np.array(["citizen"] * len(main)).astype("S")
    spi["state_id"] = np.array([1])
    spi["person_state_id"] = np.array([1] * len(main))


def add_demographics(spi: h5py.File, main: DataFrame):
    LOWER = np.array([0, 16, 25, 35, 45, 55, 65, 75])
    UPPER = np.array([16, 25, 35, 45, 55, 65, 75, 80])
    age_range = main.AGERANGE
    spi["age"] = LOWER[age_range] + np.random.rand(len(main)) * (
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

    spi["region"] = np.array(
        [REGIONS.get(x, "UNKNOWN") for x in main.GORCODE]
    ).astype("S")


def add_incomes(spi: h5py.File, main: DataFrame):
    RENAMES = dict(
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
    )
    spi["pays_scottish_income_tax"] = main.SCOT_TXP == 1
    spi["employment_income"] = main[["PAY", "EPB", "TAXTERM"]].sum(axis=1)
    spi["social_security_income"] = main[
        ["SRP", "INCPBEN", "UBISJA", "OSSBEN"]
    ].sum(axis=1)
    spi["miscellaneous_income"] = main[
        ["OTHERINV", "OTHERINC", "MOTHINC"]
    ].sum(axis=1)
    for var, key in RENAMES.items():
        spi[var] = main[key]

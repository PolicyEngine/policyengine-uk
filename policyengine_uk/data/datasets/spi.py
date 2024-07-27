from policyengine_core.data import Dataset
from policyengine_uk.data.storage import STORAGE_FOLDER
import pandas as pd
import numpy as np


class SPI(Dataset):
    spi_data_file_path: str
    data_format = Dataset.TIME_PERIOD_ARRAYS

    def generate(self):
        df = pd.read_csv(self.spi_data_file_path, delimiter="\t")

        data = {}
        data["person_id"] = df.SREF
        for id_column in [
            "person_household_id",
            "person_benunit_id",
            "benunit_id",
            "household_id",
        ]:
            data[id_column] = data["person_id"]

        data["state_id"] = np.ones(len(df), dtype=int)
        data["person_state_id"] = data["state_id"]

        data["household_weight"] = df.FACT
        data["dividend_income"] = df.DIVIDENDS
        data["gift_aid"] = df.GIFTAID
        data["region"] = (
            df.GORCODE.map(
                {
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
            )
            .fillna("UNKNOWN")
            .astype("S")
        )
        data["savings_interest_income"] = df.INCBBS
        data["property_income"] = df.INCPROP
        data["employment_income"] = df.PAY + df.EPB
        data["employment_expenses"] = df.EXPS
        data["private_pension_income"] = df.PENSION
        # The below underestimates those with high amounts of excess pension
        # savings, as it does not include the Annual Allowance
        data["private_pension_contributions"] = df.PSAV_XS
        data["pension_contributions_relief"] = df.PENSRLF
        data["self_employment_income"] = df.PROFITS
        # HMRC seems to assume the trading and property allowance are already deducted
        # (per record inspection of SREF 15494988 in 2020-21)
        data["trading_allowance"] = np.zeros(len(df))
        data["property_allowance"] = np.zeros(len(df))
        data["savings_starter_rate_income"] = np.zeros(len(df))
        data["capital_allowances"] = df.CAPALL
        data["loss_relief"] = df.LOSSBF
        data["is_SP_age"] = df.SPA == 1
        data["state_pension"] = df.SRP
        data["other_tax_credits"] = df.TAX_CRED
        data["miscellaneous_income"] = (
            df.MOTHINC
            + df.INCPBEN
            + df.OSSBEN
            + df.TAXTERM
            + df.UBISJA
            + df.OTHERINC
        )
        data["gift_aid"] = df.GIFTAID + df.GIFTINV
        data["other_investment_income"] = df.OTHERINV
        data["covenanted_payments"] = df.COVNTS
        data["other_deductions"] = df.MOTHDED + df.DEFICIEN
        data["married_couples_allowance"] = df.MCAS
        data["blind_persons_allowance"] = df.BPADUE
        data["marriage_allowance"] = np.where(df.MAIND == 1, 1_250, 0)

        for field in data:
            data[field] = {self.time_period: data[field]}

        self.save_dataset(data)


class SPI_2020_21(SPI):
    spi_data_file_path = "~/Desktop/put2021uk.tab"
    file_path = STORAGE_FOLDER / "spi_2020_21.h5"
    label = "SPI 2020-21"
    name = "spi_2020_21"
    time_period = 2020

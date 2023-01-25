# Run this script to add VAT imputation to the enhanced FRS.

import pandas as pd
from microdf import MicroDataFrame
from synthimpute import rf_impute
from policyengine_uk import Microsimulation

CONSUMPTION_PCT_REDUCED_RATE = 0.03  # From OBR's VAT page
CURRENT_VAT_RATE = 0.2

etb = pd.read_csv(
    "~/Downloads/UKDA-8856-tab/tab/householdv2_1977-2021.tab", delimiter="\t"
)
etb_2020 = etb[etb.year == 2020].dropna()
for col in etb_2020:
    etb_2020[col] = pd.to_numeric(etb_2020[col], errors="coerce")

sim = Microsimulation()


INPUT_VARIABLES = ["is_adult", "is_child", "is_SP_age", "household_net_income"]

frs_df = sim.calculate_dataframe(
    INPUT_VARIABLES[::-1],
    map_to="household",
)

imputed_rates = rf_impute(
    x_train=etb_2020_df.drop("full_rate_vat_expenditure_rate", axis=1),
    y_train=etb_2020_df.full_rate_vat_expenditure_rate,
    x_new=frs_df[INPUT_VARIABLES],
)

etb_2020_df = pd.DataFrame()
etb_2020_df["is_adult"] = etb_2020.adults
etb_2020_df["is_child"] = etb_2020.childs
etb_2020_df["is_SP_age"] = etb_2020.noretd
etb_2020_df["household_net_income"] = etb_2020.disinc * 52
etb_2020_df["full_rate_vat_expenditure_rate"] = (
    etb_2020.totvat * (1 - CONSUMPTION_PCT_REDUCED_RATE) / CURRENT_VAT_RATE
) / (etb_2020.expdis - etb_2020.totvat)
etb_2020_df = etb_2020_df[~etb_2020_df.full_rate_vat_expenditure_rate.isna()]
etb_2020_df = MicroDataFrame(
    etb_2020_df, weights=etb_2020.HHold_unadj_weight * 1_000
)
non_reduced_rate_consumption = sim.calculate(
    "consumption", 2022
) - sim.calculate("reduced_rate_vat_consumption", 2022)
sim.set_input(
    "full_rate_vat_consumption",
    2022,
    imputed_rates * non_reduced_rate_consumption,
)

EnhancedFRS.save(
    2022,
    "full_rate_vat_consumption/2022",
    sim.calculate("full_rate_vat_consumption", 2022).values,
)

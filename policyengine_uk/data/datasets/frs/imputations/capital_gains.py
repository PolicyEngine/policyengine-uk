import pandas as pd
import numpy as np

# Fit a spline to each income band's percentiles
from scipy.interpolate import UnivariateSpline
from policyengine_uk import Microsimulation
from tqdm import tqdm
from policyengine_uk.system import system
from policyengine_uk.data.storage import STORAGE_FOLDER

capital_gains = pd.read_csv(
    STORAGE_FOLDER
    / "imputations"
    / "capital_gains_distribution_advani_summers.csv.gz"
)
capital_gains["maximum_total_income"] = (
    capital_gains.minimum_total_income.shift(-1).fillna(np.inf)
)


splines = {}

for i in range(len(capital_gains)):
    row = capital_gains.iloc[i]
    splines[row.minimum_total_income] = UnivariateSpline(
        [0.05, 0.1, 0.25, 0.5, 0.75, 0.90, 0.95],
        [row.p05, row.p10, row.p25, row.p50, row.p75, row.p90, row.p95],
        k=1,
    )


sim = Microsimulation()

total_income = sim.calculate("total_income", 2023)
cgt_revenue = system.parameters.calibration.programs.capital_gains.total

lower_income_bounds = list(splines)
uprating_from_2017 = cgt_revenue("2023-01-01") / cgt_revenue("2017-01-01")


def impute_capital_gains(total_income: float, age: float) -> float:
    if total_income < 0 or age < 18:
        return 0
    distribution_row = capital_gains[
        (capital_gains["minimum_total_income"] <= total_income)
        & (capital_gains["maximum_total_income"] > total_income)
    ]
    percent_with_gains = distribution_row["percent_with_gains"].values[0]
    has_gains = np.random.choice(
        [0, 1], p=[1 - percent_with_gains, percent_with_gains]
    )
    if not has_gains:
        return 0
    sample_percentile = np.random.random()
    for i in range(len(splines)):
        if lower_income_bounds[i] > total_income:
            continue
    i -= 1
    spline = splines[lower_income_bounds[i]]
    return spline(sample_percentile) * uprating_from_2017


if __name__ == "__main__":
    imputed_gains = []
    for income, age in tqdm(
        list(zip(total_income, sim.calculate("age", 2023)))
    ):
        imputed_gains.append(impute_capital_gains(income, age))

    pd.DataFrame({"imputed_gains": imputed_gains}).to_csv(
        STORAGE_FOLDER / "imputations" / "imputed_gains.csv.gz", index=False
    )

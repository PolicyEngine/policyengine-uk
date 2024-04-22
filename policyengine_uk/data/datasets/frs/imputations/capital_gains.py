import pandas as pd
import numpy as np

# Fit a spline to each income band's percentiles
from scipy.interpolate import UnivariateSpline
from policyengine_uk import Microsimulation
from tqdm import tqdm
from policyengine_uk.data.storage import STORAGE_FOLDER
from policyengine_core.data import Dataset

import torch
from torch.optim import Adam

capital_gains = pd.read_csv(
    STORAGE_FOLDER
    / "imputations"
    / "capital_gains_distribution_advani_summers.csv.gz"
)
capital_gains["maximum_total_income"] = (
    capital_gains.minimum_total_income.shift(-1).fillna(np.inf)
)

def impute_capital_gains(time_period: int):
    """Assumes that the capital gains distribution is the same for all years.
    """

    sim = Microsimulation(dataset="experimental_enhanced_frs")
    ti = sim.calculate("total_income", time_period)
    person_weight = sim.calculate("person_weight", time_period).values
    has_capital_gains = np.zeros_like(person_weight) > 0
    first_half = np.concatenate([np.ones(len(person_weight)//2), np.zeros(len(person_weight)//2)]) > 0
    pred_cg = np.ones_like(~first_half)
    blend_factor = torch.tensor(np.zeros(first_half.sum()), requires_grad=True)

    def loss(blend_factor):
        for i in range(len(capital_gains)):
            np.random.seed(i)
            lower = capital_gains.minimum_total_income.iloc[i]
            upper = capital_gains.maximum_total_income.iloc[i]
            selection = ti.between(lower, upper)
            first_half_of_selection = selection * first_half
            second_half_of_selection = selection * ~first_half
            fraction_with_capital_gains = capital_gains.percent_with_gains.iloc[i]
            person_weights_subset = person_weight[selection][:selection.sum()//2]
            person_weight[first_half_of_selection] = person_weights_subset * (1 - fraction_with_capital_gains)
            person_weight[second_half_of_selection] = person_weights_subset * fraction_with_capital_gains
            has_capital_gains[second_half_of_selection] = True
            row = capital_gains.iloc[i]
            spline = UnivariateSpline(
                [0.05, 0.1, 0.25, 0.5, 0.75, 0.90, 0.95],
                [row.p05, row.p10, row.p25, row.p50, row.p75, row.p90, row.p95],
                k=4,
            )
            quantiles = np.random.random(second_half_of_selection.sum())
            pred_capital_gains = spline(quantiles)
            pred_cg[second_half_of_selection] = pred_capital_gains

    new_household_weight = sim.map_result(person_weight, "person", "household", how="max")
    
    return pred_cg, new_household_weight

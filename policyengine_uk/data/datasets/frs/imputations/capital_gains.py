import pandas as pd
import numpy as np

# Fit a spline to each income band's percentiles
from scipy.interpolate import PchipInterpolator, UnivariateSpline
from policyengine_uk import Microsimulation
from tqdm import tqdm
from policyengine_uk.data.storage import STORAGE_FOLDER
from policyengine_core.data import Dataset
from policyengine_uk.system import system

import torch
from torch.optim import Adam
from tqdm import tqdm

capital_gains = pd.read_csv(
    STORAGE_FOLDER
    / "imputations"
    / "capital_gains_distribution_advani_summers.csv.gz"
)
capital_gains["maximum_total_income"] = (
    capital_gains.minimum_total_income.shift(-1).fillna(np.inf)
)


def impute_capital_gains(time_period: int):
    """Assumes that the capital gains distribution is the same for all years."""

    sim = Microsimulation(dataset="experimental_enhanced_frs")
    ti = sim.calculate("total_income", time_period)
    household_weight = sim.calculate("household_weight", time_period).values
    first_half = (
        np.concatenate(
            [
                np.ones(len(household_weight) // 2),
                np.zeros(len(household_weight) // 2),
            ]
        )
        > 0
    )
    # Give capital gains to one adult aged 15+ in each household
    adult_index = sim.calculate("adult_index", time_period)
    in_person_second_half = np.zeros(len(ti)) > 0
    in_person_second_half[len(ti) // 2 :] = True
    has_cg = np.zeros(len(ti)) > 0
    has_cg[adult_index & in_person_second_half] = True
    blend_factor = torch.tensor(
        np.zeros(first_half.sum()), requires_grad=True, dtype=torch.float32
    )
    household_weight = torch.tensor(household_weight, dtype=torch.float32)
    sigmoid = torch.nn.Sigmoid()

    def loss(blend_factor):
        loss = 0

        blended_household_weight = household_weight.clone()
        adjusted_blend_factor = sigmoid(blend_factor)
        blended_household_weight[first_half] = (
            adjusted_blend_factor * blended_household_weight[first_half]
        )
        blended_household_weight[~first_half] = (
            1 - adjusted_blend_factor
        ) * blended_household_weight[first_half]
        for i in range(len(capital_gains)):
            lower = capital_gains.minimum_total_income.iloc[i]
            upper = capital_gains.maximum_total_income.iloc[i]
            true_pct_with_gains = capital_gains.percent_with_gains.iloc[i]

            ti_in_range = (ti >= lower) * (ti < upper)
            cg_in_income_range = has_cg * ti_in_range
            household_ti_in_range_count = torch.tensor(
                sim.map_result(ti_in_range, "person", "household", how="sum")
            )
            household_cg_in_income_range_count = torch.tensor(
                sim.map_result(
                    cg_in_income_range, "person", "household", how="sum"
                )
            )
            pred_ti_in_range = (
                blended_household_weight * household_ti_in_range_count
            ).sum()
            pred_cg_in_income_range = (
                blended_household_weight * household_cg_in_income_range_count
            ).sum()
            pred_pct_with_gains = pred_cg_in_income_range / pred_ti_in_range
            loss += (pred_pct_with_gains - true_pct_with_gains) ** 2

        return loss

    optimiser = Adam([blend_factor], lr=1e-1)
    progress = tqdm(range(1000))
    for i in progress:
        optimiser.zero_grad()
        loss_value = loss(blend_factor)
        loss_value.backward()
        optimiser.step()
        progress.set_description(f"Loss: {loss_value.item()}")
        if loss_value.item() < 1e-5:
            break

    new_household_weight = household_weight.detach().numpy()
    original_household_weight = new_household_weight.copy()
    blend_factor = sigmoid(blend_factor).detach().numpy()
    new_household_weight[first_half] = (
        blend_factor * original_household_weight[first_half]
    )
    new_household_weight[~first_half] = (
        1 - blend_factor
    ) * original_household_weight[first_half]

    # Impute actual capital gains amounts given gains
    new_cg = np.zeros(len(ti))

    for i in range(len(capital_gains)):
        row = capital_gains.iloc[i]
        spline = UnivariateSpline(
            [0.05, 0.1, 0.25, 0.5, 0.75, 0.90, 0.95],
            [row.p05, row.p10, row.p25, row.p50, row.p75, row.p90, row.p95],
            k=1,
        )
        lower = row.minimum_total_income
        upper = row.maximum_total_income
        ti_in_range = (ti >= lower) * (ti < upper)
        in_target_range = has_cg * ti_in_range
        quantiles = np.random.random(int(in_target_range.sum()))
        pred_capital_gains = spline(quantiles)
        new_cg[in_target_range] = pred_capital_gains

    aggregate_cg = system.parameters.calibration.programs.capital_gains.total
    uprating = aggregate_cg(time_period) / aggregate_cg("2017-01-01")
    new_cg *= uprating

    return new_cg, new_household_weight

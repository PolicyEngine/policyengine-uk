import torch
import datetime
from torch.utils.tensorboard import SummaryWriter
import pandas as pd
import numpy as np
from policyengine_uk import Microsimulation
import plotly.express as px
from tqdm import tqdm
from policyengine_core.data import Dataset
import numpy as np
from policyengine_uk import Microsimulation
import pandas as pd
from typing import Tuple
import warnings
from pathlib import Path
from torch.optim import Adam, SGD
from policyengine_uk.data.datasets.frs.calibration.loss import (
    generate_model_variables,
)
from typing import Type

warnings.filterwarnings("ignore")


def aggregate(
    adjusted_weights: torch.Tensor, values: pd.DataFrame
) -> torch.Tensor:
    broadcasted_weights = adjusted_weights.reshape(-1, 1)
    weighted_values = torch.matmul(
        broadcasted_weights.T, torch.tensor(values.values, dtype=torch.float64)
    )
    return weighted_values


def calibrate(
    dataset: str,
    time_period: str = None,
    learning_rate: float = 1e1,
    epochs: int = 10_000,
    loss_threshold: float = None,
    iter_checkpoint_every: int = None,
    initial_weights: np.ndarray = None,
) -> np.ndarray:
    (
        household_weights,
        values_df,
        targets,
        targets_array,
    ) = generate_model_variables(dataset, time_period)

    writer = SummaryWriter()

    original_weight_bias = 1  # Adjust as needed
    weights = torch.tensor(
        household_weights * original_weight_bias
        + np.random.random(household_weights.shape)
        * (1 - original_weight_bias),
        dtype=torch.float64,
        requires_grad=True,
    )

    if initial_weights is not None:
        weights = torch.tensor(
            initial_weights, dtype=torch.float64, requires_grad=True
        )

    COUNT_HOUSEHOLDS = 28e6
    count_records = household_weights.shape[0]
    targets_array = torch.tensor(targets_array, dtype=torch.float64)

    progress_bar = tqdm(
        range(epochs if loss_threshold is None else 1_000_000),
        desc="Calibrating weights",
    )
    starting_loss = None
    optimizer = Adam([weights], lr=learning_rate)
    for i in progress_bar:
        adjusted_weights = torch.relu(weights)
        result = aggregate(adjusted_weights, values_df)
        target = targets_array
        loss = torch.max((result / target - 1) ** 2)
        if i == 0:
            starting_loss = loss.item()
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        if i % 5 == 0:
            current_loss = loss.item()
            rel_errors = (
                torch.abs(result / target - 1).squeeze().detach().numpy()
            )
            max_error_i = np.argmax(rel_errors)
            max_error_value = rel_errors[max_error_i]
            max_error_label = list(targets.keys())[max_error_i]
            max_error_result = result.squeeze().detach().numpy()[max_error_i]
            max_error_target = target.squeeze().detach().numpy()[max_error_i]
            progress_bar.set_description_str(
                f"Calibrating weights | Loss = {current_loss:,.5f} | Max error = {max_error_value:.1%} ({max_error_label}) | Result = {max_error_result:,.0f} | Target = {max_error_target:,.0f}"
            )

            writer.add_scalar("Model/Loss", current_loss, i)
            writer.add_scalar("Model/Max error", max_error_value, i)

        if i % 100 == 0:
            current_aggregates = (result).detach().numpy()[0]

            log_df = pd.DataFrame(
                {
                    "name": list(targets.keys()) + ["total"],
                    "epoch": [i] * len(targets) + [i],
                    "value": list(current_aggregates) + [current_loss],
                    "target": list(targets.values()) + [0],
                    "time_period": time_period,
                }
            )

            log_df["relative_error"] = (
                log_df["value"] / log_df["target"] - 1
            ).abs()

            for j in range(len(targets)):
                writer.add_scalar(
                    f"Estimate/{list(targets.keys())[j]}",
                    current_aggregates[j],
                    i,
                )
                writer.add_scalar(
                    f"Relative error/{list(targets.keys())[j]}",
                    log_df["relative_error"].values[j],
                    i,
                )

        if loss_threshold is not None and loss.item() < loss_threshold:
            break

        if (
            iter_checkpoint_every is not None
            and i % iter_checkpoint_every == 0
        ):
            yield adjusted_weights.detach().numpy()

    loss_reduction = loss.item() / starting_loss - 1

    print(f"Loss reduction: {loss_reduction:.3%}")

    yield adjusted_weights.detach().numpy()

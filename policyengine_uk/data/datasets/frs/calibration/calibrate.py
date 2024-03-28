import torch
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

warnings.filterwarnings("ignore")


def aggregate(
    adjusted_weights: torch.Tensor, values: pd.DataFrame
) -> torch.Tensor:
    broadcasted_weights = adjusted_weights.reshape(-1, 1)
    weighted_values = torch.matmul(
        broadcasted_weights.T, torch.tensor(values.values, dtype=torch.float32)
    )
    return weighted_values


def calibrate(
    dataset: str,
    time_period: str = None,
    training_log_path: str = None,
    overwrite_existing_log: bool = False,
    learning_rate: float = 1e4,
    epochs: int = 1_000,
    loss_threshold: float = 1e-3,
) -> np.ndarray:
    (
        household_weights,
        values_df,
        targets,
        targets_array,
    ) = generate_model_variables(dataset, time_period)
    ORIGINAL_WEIGHT_BIAS = 0
    weights = torch.tensor(
        household_weights * ORIGINAL_WEIGHT_BIAS
        + 1 * (1 - ORIGINAL_WEIGHT_BIAS),
        dtype=torch.float32,
        requires_grad=True,
    )
    targets_array = torch.tensor(targets_array, dtype=torch.float32)

    if training_log_path is not None:
        training_log_path = Path(training_log_path)
        if training_log_path.exists() and not overwrite_existing_log:
            training_log_df = pd.read_csv(
                training_log_path, compression="gzip"
            )
        else:
            training_log_df = pd.DataFrame()

    progress_bar = tqdm(
        range(epochs if loss_threshold is None else 100_000),
        desc="Calibrating weights",
    )
    starting_loss = None
    elu = torch.nn.ELU()
    for i in progress_bar:
        adjusted_weights = elu(weights) + 2
        result = aggregate(adjusted_weights, values_df)
        target = targets_array
        loss = torch.max((result / target - 1) ** 2)
        if i == 0:
            starting_loss = loss.item()
        loss.backward()
        # Apply gradient descent
        with torch.no_grad():
            weights -= learning_rate * weights.grad
            weights.grad.zero_()
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
            current_aggregates = (result).detach().numpy()[0]
            if training_log_path is not None:
                training_log_df = pd.concat(
                    [
                        training_log_df,
                        pd.DataFrame(
                            {
                                "name": list(targets.keys()) + ["total"],
                                "epoch": [i] * len(targets) + [i],
                                "value": list(current_aggregates)
                                + [current_loss],
                                "target": list(targets.values()) + [0],
                                "time_period": time_period,
                            }
                        ),
                    ]
                )
        if loss_threshold is not None and loss.item() < loss_threshold:
            break

    if training_log_path is not None:
        training_log_df.to_csv(training_log_path, compression="gzip")

    loss_reduction = loss.item() / starting_loss - 1

    print(f"Loss reduction: {loss_reduction:.3%}")

    return adjusted_weights.detach().numpy()

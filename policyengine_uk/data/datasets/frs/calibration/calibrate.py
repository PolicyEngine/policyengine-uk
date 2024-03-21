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
from torch.optim import Adam
from policyengine_uk.data.datasets.frs.calibration.loss import generate_model_variables

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
    learning_rate: float = 1e-0,
    epochs: int = 1_000,
    loss_threshold: float = None,
) -> np.ndarray:
    (
        household_weights,
        values_df,
        targets,
        targets_array,
    ) = generate_model_variables(dataset, time_period)
    household_weights = torch.tensor(household_weights + np.random.random() * 10, dtype=torch.float32, requires_grad=True)
    targets_array = torch.tensor(targets_array, dtype=torch.float32)

    if training_log_path is not None:
        training_log_path = Path(training_log_path)
        if training_log_path.exists() and not overwrite_existing_log:
            training_log_df = pd.read_csv(training_log_path, compression="gzip")
        else:
            training_log_df = pd.DataFrame()

    progress_bar = tqdm(
        range(epochs if loss_threshold is None else 100_000),
        desc="Calibrating weights",
    )
    starting_loss = None
    optimizer = Adam([household_weights], lr=learning_rate)
    elu = torch.nn.ELU()
    for i in progress_bar:
        adjusted_weights = elu(household_weights) + 1
        result = (
            aggregate(adjusted_weights, values_df)
        )
        target = targets_array
        loss = torch.mean(
            ((result + 1) / (target + 1) - 1) ** 2
            # Mean (squared error * log y)
        )
        if i == 0:
            starting_loss = loss.item()
        loss.backward()
        optimizer.step()
        if i % 5 == 0:
            current_loss = loss.item()
            progress_bar.set_description_str(
                f"Calibrating weights | Loss = {current_loss:,.5f}"
            )
            current_aggregates = (
                (result).detach().numpy()[0]
            )
            if training_log_path is not None:
                training_log_df = pd.concat(
                    [
                        training_log_df,
                        pd.DataFrame(
                            {
                                "name": list(targets.keys()) + ["total"],
                                "epoch": [i] * len(targets) + [i],
                                "value": list(current_aggregates) + [current_loss],
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

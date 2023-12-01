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

warnings.filterwarnings("ignore")


def generate_model_variables(dataset: str, time_period: str = "2023") -> Tuple:
    """Generates variables needed for the calibration process.

    Args:
        dataset (str): The name of the dataset to use.
        time_period (str, optional): The time period to use. Defaults to "2023".

    Returns:
        household_weights (torch.Tensor): The household weights.
        weight_adjustment (torch.Tensor): The weight adjustment.
        values_df (pd.DataFrame): A 2D array of values to transform household weights into statistical predictions.
        targets (dict): A dictionary of names and target values for the statistical predictions.
        targets_array (dict): A 1D array of target values for the statistical predictions.
        equivalisation_factors_array (dict): A 1D array of equivalisation factors for the statistical predictions to normalise the targets.
    """
    simulation = Microsimulation(dataset=dataset)
    frs_simulation = Microsimulation(dataset="frs_2021")
    simulation.default_calculation_period = time_period
    parameters = simulation.tax_benefit_system.parameters.calibration
    current_instant = f"{time_period}-01-01"

    household_weights = torch.tensor(
        simulation.calculate("household_weight").values, dtype=torch.float32
    )
    weight_adjustment = torch.tensor(
        np.random.random(household_weights.shape) * 1,
        requires_grad=True,
        dtype=torch.float32,
    )

    values_df = pd.DataFrame()
    targets = {}
    equivalisation = {}

    # We need to normalise the targets. Common regression targets are often 1e1 to 1e3 (this informs the scale of the learning rate).
    FINANCIAL_EQUIVALISATION = "finance"
    POPULATION_EQUIVALISATION = "population"

    # FIRST SET OF TARGETS
    # First, let's make sure the dataset can be fitted to the targets that the FRS uses to set its weights. We should be able to hit
    # these exactly (uprated by population growth)

    # These targets are: 
    # - 10-year-age/sex/region intersections (can hit exactly)
    # - Benefit unit counts
    # - Council tax band counts
    # - Tenure type counts
    # Source: https://assets.publishing.service.gov.uk/media/5a7dddcc40f0b65d88634e32/initial-review-family-resources-survey-weighting-scheme.pdf#page=21
    
    # We'll calculate directly from the FRS
    # - (motivation): the source doesn't specify exact data sources and we don't want to use different ones by mistake
    # - (justification): the FRS is already calibrated to hit all these so will be accurate on them

    age = simulation.calculate("age")
    ONS_AGE_GROUPS = [0, 15, 30, 45, 60, 75]
    for i in range(len(ONS_AGE_GROUPS)):
        lower_bound = ONS_AGE_GROUPS[i]
        upper_bound = ONS_AGE_GROUPS[i + 1] if i < len(ONS_AGE_GROUPS) - 1 else np.inf
        in_age_group = (age >= lower_bound) & (age < upper_bound)
        # between_0_and_14, between_15_and_29, ..., between_75_and_over
        upper_bound_label = upper_bound - 1 if upper_bound != np.inf else "over"
        label = f"People aged {lower_bound} to {upper_bound_label}"
        values_df[label] = simulation.map_result(
            in_age_group, "person", "household"
        )
        targets[label] = parameters(current_instant).demographics.people.by_age_group._children[f"between_{lower_bound}_and_{upper_bound_label}"]
        equivalisation[label] = POPULATION_EQUIVALISATION

    # SECOND SET OF TARGETS - programs
    # We've now reproduced the essence of the FRS weights- time to add program-specific targets, while keeping
    # the demographic 'elastic' constraints in place.

    # Child benefit
    
    programs = parameters.programs(current_instant)
    cb = simulation.calculate("child_benefit").values
    hh_child_benefit = simulation.map_result(cb, "benunit", "household")
    hh_receiving_child_benefit = simulation.map_result(cb > 0, "benunit", "household")
    label = "Child benefit budgetary impact"
    targets[label] = programs.child_benefit.budgetary_impact.UNITED_KINGDOM
    equivalisation[label] = FINANCIAL_EQUIVALISATION
    values_df[label] = hh_child_benefit

    label = "Children receiving child benefit"
    targets[label] = programs.child_benefit.participants.UNITED_KINGDOM
    equivalisation[label] = POPULATION_EQUIVALISATION
    values_df[label] = hh_receiving_child_benefit

    # Find equivalisation by dividing by the mean of each equivalisation group

    df = pd.DataFrame({
        "target": list(targets.values()),
        "equivalisation": list(equivalisation.values()),
    })
    equivalisation_name_to_mean = df.groupby("equivalisation").target.sum().to_dict()
    equivalisation = {
        k: equivalisation_name_to_mean[v]
        for k, v in equivalisation.items()
    }
    
    targets_array = torch.tensor(list(targets.values()), dtype=torch.float32)
    equivalisation_factors_array = torch.tensor(
        list(equivalisation.values()), dtype=torch.float32
    )

    return (
        household_weights,
        weight_adjustment,
        values_df,
        targets,
        targets_array,
        equivalisation_factors_array,
    )

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
    time_period: str = "2023",
    training_log_path: str = "training_log.csv.gz",
    overwrite_existing_log: bool = False,
    learning_rate: float = 5e3,
    epochs: int = 5_000,
    loss_threshold: float = None,
) -> np.ndarray:
    (
        household_weights,
        weight_adjustment,
        values_df,
        targets,
        targets_array,
        equivalisation_factors_array,
    ) = generate_model_variables(dataset, time_period)
    training_log_path = Path(training_log_path)
    if training_log_path.exists() and not overwrite_existing_log:
        training_log_df = pd.read_csv(training_log_path, compression="gzip")
    else:
        training_log_df = pd.DataFrame()

    progress_bar = tqdm(range(epochs if loss_threshold is None else 100_000), desc="Calibrating weights")
    starting_loss = None
    for i in progress_bar:
        adjusted_weights = torch.relu(household_weights + weight_adjustment)
        result = (
            aggregate(adjusted_weights, values_df)
            / equivalisation_factors_array
        )
        actual = targets_array / equivalisation_factors_array
        loss = torch.mean(
            (1e3 * result - 1e3 * actual) ** 2
        )
        if i == 0:
            starting_loss = loss.item()
        loss.backward()
        if i % 5 == 0:
            current_loss = loss.item()
            progress_bar.set_description_str(
                f"Calibrating weights | Loss = {current_loss:,.3f}"
            )
            current_aggregates = (
                (result * equivalisation_factors_array).detach().numpy()[0]
            )
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
        weight_adjustment.data -= learning_rate * weight_adjustment.grad
        weight_adjustment.grad.zero_()
        if loss_threshold is not None and loss.item() < loss_threshold:
            break

    training_log_df.to_csv(training_log_path, compression="gzip")

    loss_reduction = loss.item() / starting_loss - 1

    print(f"Loss reduction: {loss_reduction:.2%}")

    return adjusted_weights.detach().numpy()

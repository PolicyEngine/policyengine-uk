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
from policyengine_uk.data.storage import STORAGE_FOLDER

warnings.filterwarnings("ignore")

CALIBRATION_PARAMETER_FOLDER = STORAGE_FOLDER.parent.parent / "parameters" / "calibration"


def generate_model_variables(dataset: str, time_period: str = "2023", no_weight_adjustment=False) -> Tuple:
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
    obr = simulation.tax_benefit_system.parameters.gov.obr
    current_instant = f"{time_period}-01-01"

    household_weights = simulation.calculate("household_weight").values
    weight_adjustment = np.random.random(household_weights.shape) * 1 - 0.5

    if no_weight_adjustment:
        weight_adjustment = np.zeros_like(household_weights)

    household_weights += weight_adjustment

    values_df = pd.DataFrame()
    targets = {}
    
    
    # DEMOGRAPHICS
    # First: ONS population projections

    age_sex_df = pd.read_csv(CALIBRATION_PARAMETER_FOLDER / "ons" / "populations" / "population_age_sex.csv.gz")
    # Combine 79+ into 79
    age_sex_df["Age"] = age_sex_df.Age.apply(lambda x: round(min(79, x)))
    age_sex_df = age_sex_df.groupby(["Age", "Sex"]).sum().reset_index()
    for i, row in age_sex_df.iterrows():
        age = row["Age"]
        sex = "MALE" if row["Sex"] == 1 else "FEMALE"

        ages = simulation.calculate("age").apply(lambda x: round(min(79, x))).values
        sex_values = simulation.calculate("gender").values

        in_criteria = (ages == age) & (sex_values == sex)
        name = f"{sex.lower()} population aged {age}"

        values_df[name] = simulation.map_result(in_criteria, "person", "household")
        targets[name] = row[str(time_period)]

    # Second: ONS total household projections
    
    households = parameters(current_instant).ons.households

    values_df["households"] = np.ones_like(household_weights)
    targets["households"] = households.total

    # Third: ONS household by size projections

    capped_household_size = simulation.calculate("people", map_to="household").clip(1, 7)
    for size in range(1, 8):
        in_criteria = (capped_household_size == size).astype(float)
        name = f"{size}-person households"

        values_df[name] = in_criteria
        targets[name] = households.by_size[str(size)]

    # INCOMES
        
    total_income = simulation.calculate("total_income").values
        
    for variable in ["employment_income", "self_employment_income", "pension_income", "dividend_income", "property_income"]:
        income_parameter = parameters(current_instant).hmrc.income[variable]
        label = simulation.tax_benefit_system.variables[variable].label
        amounts = simulation.calculate(variable).values
        nonzero = amounts != 0

        for i in range(len(income_parameter.amount.thresholds)):
            threshold = income_parameter.amount.thresholds[i]
            upper_threshold = income_parameter.amount.thresholds[i + 1] if i + 1 < len(income_parameter.amount.thresholds) else np.inf
            name = f"total {label} ({threshold} to {upper_threshold})"
            in_criteria = ((total_income >= threshold) & (total_income < upper_threshold)).astype(float)
            values_df[name] = simulation.map_result(in_criteria * amounts, "person", "household")
            targets[name] = income_parameter.amount.amounts[i]
        
        for i in range(len(income_parameter.count.thresholds)):
            threshold = income_parameter.count.thresholds[i]
            upper_threshold = income_parameter.count.thresholds[i + 1] if i + 1 < len(income_parameter.count.thresholds) else np.inf
            name = f"individuals with {label} ({threshold} to {upper_threshold})"
            in_criteria = ((total_income >= threshold) & (total_income < upper_threshold)).astype(float)
            values_df[name] = simulation.map_result(in_criteria * nonzero, "person", "household")
            targets[name] = income_parameter.count.amounts[i]
        
    # PROGRAMS
    # OBR forecasts
            
    for program in parameters.obr.program_forecasts.children:
        obr_program = parameters.obr(current_instant).program_forecasts[program]
        label = simulation.tax_benefit_system.variables[program].label
        values = simulation.calculate(program, map_to="household").values

        values_df[label] = values
        targets[label] = obr_program
    
    targets_array = np.array(list(targets.values()))

    return (
        household_weights,
        values_df,
        targets,
        targets_array,
    )


def add_variable_metric(
    variable_name: str,
    simulation: Microsimulation,
    parameter_node,
    values_df: pd.DataFrame,
    targets: dict,
    equivalisation: dict,
    finance_equivalisation: float,
    population_equivalisation: float,
):
    variable = simulation.tax_benefit_system.variables[variable_name]
    entity = variable.entity.key
    values = simulation.calculate(variable_name).values
    country = simulation.calculate("country").values
    values_df, targets, equivalisation = add_country_level_metric(
        simulation.map_result(values, entity, "household"),
        finance_equivalisation,
        country,
        values_df,
        targets,
        equivalisation,
        variable.label + " budgetary impact",
        parameter_node.budgetary_impact,
    )

    if hasattr(parameter_node, "participants"):
        values_df, targets, equivalisation = add_country_level_metric(
            simulation.map_result(values > 0, entity, "household"),
            population_equivalisation,
            country,
            values_df,
            targets,
            equivalisation,
            variable.label + " participants",
            parameter_node.participants,
        )

    return values_df, targets, equivalisation


def add_country_level_metric(
    household_values,
    equivalisation_name,
    countries,
    values_df,
    targets,
    equivalisation,
    name,
    parameter,
):
    for child_key in parameter._children:
        child_value = parameter._children[child_key]
        if child_key == "GREAT_BRITAIN":
            region_filter = countries != "NORTHERN_IRELAND"
            values_df[name + " (GB)"] = household_values * region_filter
            targets[name + " (GB)"] = child_value
            equivalisation[name + " (GB)"] = equivalisation_name
        elif child_key == "NORTHERN_IRELAND":
            region_filter = countries == "NORTHERN_IRELAND"
            values_df[name + " (NI)"] = household_values * region_filter
            targets[name + " (NI)"] = child_value
            equivalisation[name + " (NI)"] = equivalisation_name
        elif child_key == "UNITED_KINGDOM":
            values_df[name + " (UK)"] = household_values
            targets[name + " (UK)"] = child_value
            equivalisation[name + " (UK)"] = equivalisation_name
        elif child_key == "ENGLAND":
            region_filter = countries == "ENGLAND"
            values_df[name + " (England)"] = household_values * region_filter
            targets[name + " (England)"] = child_value
            equivalisation[name + " (England)"] = equivalisation_name
        elif child_key == "WALES":
            region_filter = countries == "WALES"
            values_df[name + " (Wales)"] = household_values * region_filter
            targets[name + " (Wales)"] = child_value
            equivalisation[name + " (Wales)"] = equivalisation_name
        elif child_key == "SCOTLAND":
            region_filter = countries == "SCOTLAND"
            values_df[name + " (Scotland)"] = household_values * region_filter
            targets[name + " (Scotland)"] = child_value
            equivalisation[name + " (Scotland)"] = equivalisation_name
    return values_df, targets, equivalisation



def aggregate_np(
    adjusted_weights: np.ndarray, values: pd.DataFrame
) -> np.ndarray:
    broadcasted_weights = adjusted_weights.reshape(-1, 1)
    weighted_values = np.matmul(broadcasted_weights.T, values.values)
    return weighted_values


def get_snapshot(
    dataset: str,
    time_period: str = "2023",
) -> pd.DataFrame:
    """Returns a snapshot of the training metrics without training the model.

    Args:
        dataset (str): The name of the dataset to use.
        time_period (str, optional): The time period to use. Defaults to "2023".

    Returns:
        pd.DataFrame: A DataFrame containing the training metrics.
    """
    (
        household_weights,
        values_df,
        targets,
        targets_array,
    ) = generate_model_variables(
        dataset, time_period, no_weight_adjustment=True
    )
    adjusted_weights = np.maximum(household_weights, 0)
    result = (
        aggregate_np(adjusted_weights, values_df)
    )
    target = targets_array
    current_aggregates = (result)[0]
    loss = np.mean(((result / target - 1) ** 2) * np.log2(np.abs(target)))
    current_loss = loss.item()
    return pd.DataFrame(
        {
            "name": list(targets.keys()) + ["total"],
            "value": list(current_aggregates) + [current_loss],
            "target": list(targets.values()) + [0],
            "time_period": time_period,
        }
    )

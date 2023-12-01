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
    sex = simulation.calculate("gender")
    region = simulation.calculate("region", map_to="person")
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
    

    
    # Benefit unit counts
    # [one-vs-two adults]/[with-without children]/region
    # This is more granular than in the source above but encompasses the same information

    benunit_region = simulation.calculate("benunit_region").values
    benunit_count_adults = simulation.calculate("num_adults").values
    benunit_has_children = simulation.calculate("num_children").values > 0

    frs_benunit_region = frs_simulation.calculate("benunit_region").values
    frs_benunit_count_adults = frs_simulation.calculate("num_adults").values
    frs_benunit_has_children = frs_simulation.calculate("num_children").values > 0

    frs_weight = frs_simulation.calculate("household_weight").values
    for possible_count_adults in [1, 2]:
        for possible_has_children in [True, False]:
            meets_criteria = (
                (benunit_count_adults == possible_count_adults)
                & (benunit_has_children == possible_has_children)
            )

            frs_meets_criteria = (
                (frs_benunit_count_adults == possible_count_adults)
                & (frs_benunit_has_children == possible_has_children)
            )
            frs_population = (frs_simulation.map_result(
                frs_meets_criteria.astype(float),
                "benunit",
                "household",
            ) * frs_weight).sum()
            household_population_index = parameters.demographics.households.in_total
            household_population_growth = household_population_index(current_instant) / household_population_index("2021-01-01")

            actual_population = frs_population * household_population_growth

            label = f"Benefit units with {possible_count_adults} adults, {'with children' if possible_has_children else 'without children'}"
            targets[label] = actual_population
            equivalisation[label] = POPULATION_EQUIVALISATION
            values_df[label] = simulation.map_result(
                meets_criteria.astype(float), "benunit", "household"
            )

    # Council tax band counts

    council_tax_band = simulation.calculate("council_tax_band").values
    frs_council_tax_band = frs_simulation.calculate("council_tax_band")

    for possible_council_tax_band in frs_council_tax_band.sort_values().unique():
        meets_criteria = (council_tax_band == possible_council_tax_band)
        frs_meets_criteria = (frs_council_tax_band.values == possible_council_tax_band)
        frs_population = (frs_meets_criteria.astype(float) * frs_weight).sum()
        household_population_index = parameters.demographics.households.in_total
        household_population_growth = household_population_index(current_instant) / household_population_index("2021-01-01")

        actual_population = frs_population * household_population_growth

        label = f"Households in council tax band {possible_council_tax_band}"
        targets[label] = actual_population
        equivalisation[label] = POPULATION_EQUIVALISATION
        values_df[label] = meets_criteria.astype(float)

    # Tenure type counts

    tenure_type = simulation.calculate("tenure_type").values
    frs_tenure_type = frs_simulation.calculate("tenure_type")

    for possible_tenure_type in frs_tenure_type.sort_values().unique():
        meets_criteria = tenure_type == possible_tenure_type
        frs_meets_criteria = frs_tenure_type.values == possible_tenure_type
        frs_population = (frs_meets_criteria.astype(float) * frs_weight).sum()
        household_population_index = parameters.demographics.households.in_total
        household_population_growth = household_population_index(current_instant) / household_population_index("2021-01-01")

        actual_population = frs_population * household_population_growth

        label = f"Households with tenure type {possible_tenure_type}"
        targets[label] = actual_population
        equivalisation[label] = POPULATION_EQUIVALISATION
        values_df[label] = meets_criteria.astype(float)

    # SECOND SET OF TARGETS - programs
    # We've now reproduced the essence of the FRS weights- time to add program-specific targets, while keeping
    # the demographic 'elastic' constraints in place.

    # Child benefit
    
    programs = parameters.programs(current_instant)
    cb = simulation.calculate("child_benefit").values
    hh_cb = simulation.map_result(cb, "benunit", "household")
    is_child = simulation.calculate("is_child_or_QYP").values
    person_in_cb_receiving_family = simulation.calculate("child_benefit", map_to="person").values > 0
    child_receiving_cb = simulation.map_result(
        is_child * person_in_cb_receiving_family, "person", "household"
    )

    values_df, targets, equivalisation = add_country_level_metric(
        hh_cb,
        "Child benefit budgetary impact",
        simulation.calculate("country").values,
        values_df,
        targets,
        equivalisation,
        "Child benefit budgetary impact",
        programs.child_benefit.budgetary_impact,
    )

    values_df, targets, equivalisation = add_country_level_metric(
        child_receiving_cb,
        "Children receiving child benefit",
        simulation.calculate("country").values,
        values_df,
        targets,
        equivalisation,
        "Children receiving child benefit",
        programs.child_benefit.participants,
    )

    
    # Universal Credit

    uc = simulation.calculate("universal_credit").values
    uc_hh = simulation.map_result(uc, "benunit", "household")
    uc_recipient = simulation.map_result(uc > 0, "benunit", "household")
    country = simulation.calculate("country").values

    values_df, targets, equivalisation = add_country_level_metric(
        uc_hh,
        "Universal Credit budgetary impact",
        country,
        values_df,
        targets,
        equivalisation,
        "Universal Credit budgetary impact",
        programs.universal_credit.budgetary_impact,
    )

    values_df, targets, equivalisation = add_country_level_metric(
        uc_recipient,
        "Universal Credit recipients",
        country,
        values_df,
        targets,
        equivalisation,
        "Universal Credit recipients",
        programs.universal_credit.participants,
    )
    

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
    learning_rate: float = 5e4,
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

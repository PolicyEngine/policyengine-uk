from pathlib import Path
from typing import List
import yaml
import h5py
from tqdm import tqdm
from openfisca_uk import Microsimulation
import pandas as pd
import numpy as np
from numpy.typing import ArrayLike
import tensorflow as tf
import logging
from openfisca_core.parameters import ParameterAtInstant

LEARNING_RATE = 8e1
NUM_EPOCHS = 256

tf.get_logger().setLevel("INFO")
logging.basicConfig(level=logging.INFO)

sim = Microsimulation(adjust_weights=False, duplicate_records=2)
parameters = sim.simulation.tax_benefit_system.parameters
statistics = parameters.calibration

START_YEAR = 2019
END_YEAR = 2022

FORCE_ALL_METRIC_IMPROVEMENT = False  # Don't save weights unless all (program, year, aggregate/caseload) tests improve. If false, regressions will be logged.

household_population = sim.calc("people", map_to="household").values
household_region = sim.calc("region").values
regions = list(pd.Series(household_region).unique())
household_country = sim.calc("country").values
countries = list(pd.Series(household_country).unique())
survey_num_households = len(sim.calc("household_id"))

AGGREGATE_ERROR_PENALTY = 1e-4
PARTICIPATION_ERROR_PENALTY = 1e-0  # Person-deviations are 10,000 more loss-heavy than spending deviations per pound
MODIFICATION_PENALTY = 1e-7
AGE_DISTRIBUTION_PENALTY = 1e0
POPULATION_ERROR_PENALTY = 1e1


def squared_relative_deviation(
    pred: tf.Tensor, actual: ArrayLike
) -> tf.Tensor:
    return ((pred / actual) - 1) ** 2


VAL_PROGRAMS = {
    2019: [
        "council_tax_less_benefit",
        "housing_benefit",
    ],
    2020: [
        "income_support",
        "ESA_income",
    ],
    2021: [
        "total_NI",
        "JSA_income",
    ],
    2022: [],
}

VAL_PROGRAMS = {year: [] for year in range(2019, 2023)}


def uk_wide_population_loss(
    original_weights: ArrayLike, modified_weights: tf.Tensor
) -> tf.Tensor:
    total_population = original_weights.sum()
    new_population = tf.reduce_sum(modified_weights)

    return (
        POPULATION_ERROR_PENALTY
        * PARTICIPATION_ERROR_PENALTY
        * total_population
        * squared_relative_deviation(new_population, total_population)
    )


def uk_wide_program_statistic_loss(
    variables: List[str],
    statistic_set: ParameterAtInstant,
    year: int,
    modified_weights: tf.Tensor,
    validation: bool = False,
) -> tf.Tensor:
    l = 0
    for variable in variables:
        if variable in statistic_set.aggregate._children:
            val_program = variable in VAL_PROGRAMS[year]
            values = sim.calc(variable, period=year).values
            entity = sim.simulation.tax_benefit_system.variables[
                variable
            ].entity.key
            household_totals = sim.map_to(values, entity, "household")
            household_participants = sim.map_to(
                (values > 0) * 1, entity, "household"
            )
            # Calculate aggregate error
            agg = tf.reduce_sum(modified_weights * household_totals)
            target = getattr(statistic_set.aggregate, variable)
            if (val_program and validation) or (
                not val_program and not validation
            ):
                l += (
                    AGGREGATE_ERROR_PENALTY
                    * target
                    * squared_relative_deviation(agg, target)
                )
        if variable in statistic_set.count._children:
            # Calculate caseload error
            count = tf.reduce_sum(modified_weights * household_participants)
            target = getattr(statistic_set.count, variable)
            if (val_program and validation) or (
                not val_program and not validation
            ):
                l += (
                    PARTICIPATION_ERROR_PENALTY
                    * target
                    * squared_relative_deviation(count, target)
                )
    return l


def regional_population_loss(
    statistic_set: ParameterAtInstant, modified_weights: tf.Tensor
) -> tf.Tensor:
    l = 0
    for region in regions:
        in_region = household_region == region
        people_in_region = household_population * in_region
        population = tf.reduce_sum(people_in_region * modified_weights)
        target = getattr(statistic_set.populations, region)
        l += (
            POPULATION_ERROR_PENALTY
            * PARTICIPATION_ERROR_PENALTY
            * target
            * squared_relative_deviation(population, target)
        )
    return l


def country_level_program_statistic_loss(
    statistic_set: ParameterAtInstant,
    year: int,
    modified_weights: tf.Tensor,
    validation: bool = False,
) -> tf.Tensor:
    l = 0
    for country in countries:
        for variable in statistic_set.aggregate_by_country._children:
            val_program = variable in VAL_PROGRAMS[year]
            in_country = household_country == country
            values = sim.calc(variable, period=year).values
            entity = sim.simulation.tax_benefit_system.variables[
                variable
            ].entity.key
            household_totals = sim.map_to(values, entity, "household")
            aggregate = tf.reduce_sum(
                modified_weights * in_country * household_totals
            )
            target = getattr(
                getattr(statistic_set.aggregate_by_country, variable),
                country,
            )
            if (val_program and validation) or (
                not val_program and not validation
            ):
                l += (
                    AGGREGATE_ERROR_PENALTY
                    * target
                    * squared_relative_deviation(aggregate, target)
                )
    return l


def taxpayers_by_band_loss(
    statistic_set: ParameterAtInstant, year: int, modified_weights: tf.Tensor
) -> tf.Tensor:
    l = 0
    tax_band = sim.calc("tax_band", period=year).values
    pays_basic_rate = (
        (tax_band == "BASIC")
        | (tax_band == "INTERMEDIATE")
        | (tax_band == "STARTER")
    )
    pays_higher_rate = tax_band == "HIGHER"
    pays_add_rate = tax_band == "ADDITIONAL"

    basic_rate_payers = sim.map_to(pays_basic_rate, "person", "household")
    higher_rate_payers = sim.map_to(pays_higher_rate, "person", "household")
    add_rate_payers = sim.map_to(pays_add_rate, "person", "household")

    for value, target in zip(
        [
            basic_rate_payers,
            higher_rate_payers,
            add_rate_payers,
        ],
        [
            statistic_set.income_tax_payers_by_band.BASIC,
            statistic_set.income_tax_payers_by_band.HIGHER,
            statistic_set.income_tax_payers_by_band.ADDITIONAL,
        ],
    ):
        population = tf.reduce_sum(modified_weights * value)
        l += (
            POPULATION_ERROR_PENALTY
            * PARTICIPATION_ERROR_PENALTY
            * target
            * squared_relative_deviation(population, target)
        )
    return l


def tax_revenue_by_income_band_loss(
    year: int, modified_weights: tf.Tensor
) -> tf.Tensor:
    l = 0
    brackets = statistics.income_tax_by_income_range.brackets
    num_thresholds = len(brackets)
    instant_str = f"{year}-01-01"
    for i in range(num_thresholds):
        lower_threshold = brackets[i].threshold(instant_str)
        upper_threshold = (
            brackets[i + 1].threshold(instant_str)
            if i < num_thresholds - 1
            else np.inf
        )
        income = sim.calc("total_income", period=year)
        person_in_range = (income >= lower_threshold) & (
            income < upper_threshold
        )
        income_tax_in_range = (
            sim.calc("income_tax", period=year) * person_in_range
        )
        household_income_tax = sim.map_to(
            income_tax_in_range, "person", "household"
        )
        aggregate = tf.reduce_sum(modified_weights * household_income_tax)
        target = brackets[i].amount(instant_str)
        l += (
            AGGREGATE_ERROR_PENALTY
            * target
            * squared_relative_deviation(aggregate, target)
            / num_thresholds
        )
    return l


def population_age_distribution_loss(
    statistic_set: ParameterAtInstant, year: int, modified_weights: tf.Tensor
) -> tf.Tensor:
    l = 0
    brackets = statistics.population_by_age.brackets
    instant_str = f"{year}-01-01"
    num_thresholds = len(brackets)
    for i in range(num_thresholds):
        lower_threshold = brackets[i].threshold(instant_str)
        upper_threshold = (
            brackets[i + 1].threshold(instant_str)
            if i < num_thresholds - 1
            else np.inf
        )
        age = sim.calc("age", period=year)
        person_in_range = (age >= lower_threshold) & (age < upper_threshold)
        household_count = sim.map_to(person_in_range, "person", "household")
        population = tf.reduce_sum(modified_weights * household_count)
        if year > 2019:
            current_population = sum(
                [
                    getattr(statistic_set.populations, region)
                    for region in regions
                ]
            )
            last_year_population = sum(
                [
                    getattr(statistics(f"{year-1}-01-01").populations, region)
                    for region in regions
                ]
            )
            population_increase_ratio = (
                current_population / last_year_population
            )
        else:
            population_increase_ratio = 1
        target = brackets[i].amount(instant_str) * population_increase_ratio
        l += (
            POPULATION_ERROR_PENALTY
            * AGE_DISTRIBUTION_PENALTY
            * target
            * ((population / target) - 1) ** 2
            / num_thresholds
        )
    return l


losses_over_time = {}


def loss(
    weight_modification: np.array, include_modification_penalty: float = True
) -> float:
    l = 0
    for year in range(START_YEAR, END_YEAR + 1):
        instant_str = f"{year}-01-01"
        statistic_set = statistics(instant_str)
        variables = list(statistic_set.aggregate._children)
        weights = sim.calc("household_weight", period=year).values
        modified_weights = tf.nn.relu(
            weight_modification[year - START_YEAR] + weights
        )

        loss_types = {}

        loss_types[
            "UK-wide program statistics"
        ] = uk_wide_program_statistic_loss(
            variables, statistic_set, year, modified_weights
        )

        loss_types[
            "Country-level program statistics"
        ] = country_level_program_statistic_loss(
            statistic_set, year, modified_weights
        )

        loss_types["Regional populations"] = regional_population_loss(
            statistic_set, modified_weights
        )

        loss_types["Taxpayer counts by tax band"] = taxpayers_by_band_loss(
            statistic_set, year, modified_weights
        )

        loss_types[
            "Tax revenues by income range"
        ] = tax_revenue_by_income_band_loss(year, modified_weights)

        loss_types[
            "UK population age distribution"
        ] = population_age_distribution_loss(
            statistic_set, year, modified_weights
        )

        loss_types["UK household population"] = uk_wide_population_loss(
            weights, modified_weights
        )

        loss_types["Modification penalty"] = tf.reduce_sum(
            MODIFICATION_PENALTY * weight_modification**2
        )

        for loss_type, loss_value in loss_types.items():
            if loss_type not in losses_over_time:
                losses_over_time[loss_type] = [float(loss_value.numpy())]
            else:
                losses_over_time[loss_type] += [float(loss_value.numpy())]
            l += loss_value

    # Add penalty for weight changes
    if not include_modification_penalty:
        l -= loss_types["Modification penalty"]
    return l


def val_loss(weight_modification: np.array) -> float:
    # Out-of-scope metrics go here
    l = tf.constant(0, dtype=tf.float32)
    for year in range(START_YEAR, END_YEAR + 1):
        instant_str = f"{year}-01-01"
        statistic_set = statistics(instant_str)
        variables = list(statistic_set.aggregate._children)
        weights = sim.calc("household_weight", period=year).values
        modified_weights = tf.nn.relu(
            weight_modification[year - START_YEAR] + weights
        )

        l += uk_wide_program_statistic_loss(
            variables, statistic_set, year, modified_weights, True
        )

        l += country_level_program_statistic_loss(
            statistic_set, year, modified_weights, True
        )

    return l


def train_weights() -> ArrayLike:
    opt = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    weight_changes = tf.Variable(
        np.zeros((END_YEAR + 1 - START_YEAR, survey_num_households)),
        dtype=tf.float32,
    )
    task = tqdm(range(NUM_EPOCHS), desc="Training")
    start_loss = loss(weight_changes, include_modification_penalty=False)
    start_val_loss = val_loss(weight_changes)
    for i in task:
        with tf.GradientTape() as tape:
            l = loss(weight_changes)
            l_acc = loss(weight_changes, include_modification_penalty=False)
            v_loss = val_loss(weight_changes)
            if "Total training loss" not in losses_over_time:
                losses_over_time["Total training loss"] = []
            losses_over_time["Total training loss"] += [float(l.numpy())]
            if "Total validation loss" not in losses_over_time:
                losses_over_time["Total validation loss"] = []
            losses_over_time["Total validation loss"] += [
                float(v_loss.numpy())
            ]
            task.set_description(
                f"Training loss: {(l_acc.numpy() / start_loss.numpy())-1:.4%} | Validation loss: {(v_loss.numpy() / start_val_loss.numpy())-1:.4%}"
            )
            gradients = tape.gradient(l, weight_changes)
        opt.apply_gradients(zip([gradients], [weight_changes]))

    return weight_changes.numpy()


def get_microsimulation(weights: ArrayLike) -> Microsimulation:
    sim_reweighted = Microsimulation(adjust_weights=False, duplicate_records=2)
    for year in range(START_YEAR, END_YEAR + 1):
        new_weights = np.maximum(
            0,
            sim.calc("household_weight", period=year).values
            + weights[year - START_YEAR],
        )
        sim_reweighted.set_input(
            "household_weight",
            year,
            new_weights,
        )
    return sim_reweighted


def get_validation_df(sim_reweighted: Microsimulation) -> pd.DataFrame:
    variables = list(statistics.aggregate.children)

    programs = []
    years = []
    metrics = []
    frs = []
    reweight = []
    official_stats = []

    for year in range(START_YEAR, END_YEAR + 1):
        for program in variables:
            values = sim.calc(program, period=year).values
            frs_weights = sim.calc("household_weight", period=year).values
            new_weights = sim_reweighted.calc(
                "household_weight", period=year
            ).values
            entity = sim.simulation.tax_benefit_system.variables[
                program
            ].entity.key
            if program in statistics.aggregate.children:
                # Aggregate
                household_values = sim.map_to(values, entity, "household")
                frs_weighted = (household_values * frs_weights).sum()
                reweighted = (household_values * new_weights).sum()
                official = getattr(
                    statistics.aggregate(f"{year}-01-01"), program
                )
                program_name = sim.simulation.tax_benefit_system.variables[
                    program
                ].label

                programs += [program_name]
                years += [year]
                metrics += ["Aggregate"]
                frs += [frs_weighted]
                reweight += [reweighted]
                official_stats += [official]
            if program in statistics.count.children:
                # Caseload
                household_values = sim.map_to(values > 0, entity, "household")
                frs_weighted = (household_values * frs_weights).sum()
                reweighted = (household_values * new_weights).sum()
                official = getattr(statistics.count(f"{year}-01-01"), program)

                programs += [program_name]
                years += [year]
                metrics += ["Count"]
                frs += [frs_weighted]
                reweight += [reweighted]
                official_stats += [official]

    return pd.DataFrame(
        {
            "Program": programs,
            "Year": years,
            "Metric": metrics,
            "FRS-weighted": frs,
            "Re-weighted": reweight,
            "Official": official_stats,
        }
    )


def check_validation_performance_regression(df: pd.DataFrame):
    for year in df.Year.unique():
        for metric in df.Metric.unique():
            for program in df.Program.unique():
                subset = df[
                    (df.Year == year)
                    & (df.Metric == metric)
                    & (df.Program == program)
                ]
                if len(subset) == 0:
                    continue
                else:
                    subset = subset.iloc[0]
                original_error = subset["FRS-weighted"] - subset.Official
                new_error = subset["Re-weighted"] - subset.Official
                message = f"{program} {year} {metric} error changes from {original_error:,.0f} to {new_error:,.0f}."
                if FORCE_ALL_METRIC_IMPROVEMENT:
                    raise ValueError(message)
                else:
                    logging.info(message)


def save_weights(sim_reweighted: Microsimulation):
    folder = Path(__file__).parent
    with h5py.File(folder / "frs_weights.h5", "w") as f:
        for year in range(START_YEAR, END_YEAR + 1):
            f.create_dataset(
                f"{year}",
                data=sim_reweighted.calc(
                    "household_weight", period=year
                ).values,
            )

    with open(folder / "losses.yaml", "w+") as f:
        yaml.safe_dump(losses_over_time, f)


new_weights = train_weights()
sim_reweighted = get_microsimulation(new_weights)
df = get_validation_df(sim_reweighted)
check_validation_performance_regression(df)
save_weights(sim_reweighted)

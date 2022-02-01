from pathlib import Path
import h5py
from tqdm import tqdm
from openfisca_uk import Microsimulation
import pandas as pd
import numpy as np
import tensorflow as tf
import logging

tf.get_logger().setLevel("INFO")
logging.basicConfig(level=logging.INFO)

sim = Microsimulation(adjust_weights=False)
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

AGGREGATE_ERROR_PENALTY = 1e-5
PARTICIPATION_ERROR_PENALTY = 1e-1  # Person-deviations are 10,000 more loss-heavy than spending deviations per pound
MODIFICATION_PENALTY = 1e-11
AGE_DISTRIBUTION_PENALTY = 1e-1
POPULATION_ERROR_PENALTY = 5


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
        for variable in variables:
            if variable in statistic_set.aggregate._children:
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
                l += (
                    AGGREGATE_ERROR_PENALTY
                    * target
                    * ((agg / target) - 1) ** 2
                )
            if variable in statistic_set.count._children:
                # Calculate caseload error
                count = tf.reduce_sum(
                    modified_weights * household_participants
                )
                target = getattr(statistic_set.count, variable)
                l += (
                    PARTICIPATION_ERROR_PENALTY
                    * target
                    * ((count / target) - 1) ** 2
                )
        for region in regions:
            in_region = household_region == region
            people_in_region = household_population * in_region
            population = tf.reduce_sum(people_in_region * modified_weights)
            target = getattr(statistic_set.populations, region)
            l += (
                POPULATION_ERROR_PENALTY
                * PARTICIPATION_ERROR_PENALTY
                * target
                * ((population / target) - 1) ** 2
            )


        for country in countries:
            for variable in statistic_set.aggregate_by_country._children:
                in_country = household_country == country
                values = sim.calc(variable, period=year).values
                entity = sim.simulation.tax_benefit_system.variables[
                    variable
                ].entity.key
                household_totals = sim.map_to(values, entity, "household")
                aggregate = tf.reduce_sum(
                    modified_weights * in_country * household_totals
                )
                target = getattr(getattr(statistic_set.aggregate_by_country, variable), country)
                l += (
                    AGGREGATE_ERROR_PENALTY
                    * target
                    * ((aggregate / target) - 1) ** 2
                )
        # Income tax payers by tax band

        tax_band = sim.calc("tax_band", period=year).values
        pays_basic_rate = (
            (tax_band == "BASIC")
            | (tax_band == "INTERMEDIATE")
            | (tax_band == "STARTER")
        )
        pays_higher_rate = tax_band == "HIGHER"
        pays_add_rate = tax_band == "ADDITIONAL"

        basic_rate_payers = sim.map_to(pays_basic_rate, "person", "household")
        higher_rate_payers = sim.map_to(
            pays_higher_rate, "person", "household"
        )
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
                * ((population / target) - 1) ** 2
            )
        
        # Income tax aggregate by income band

        brackets = statistics.income_tax_by_income_range.brackets
        num_thresholds = len(brackets)
        instant_str = f"{year}-01-01"
        for i in range(num_thresholds):
            lower_threshold = brackets[i].threshold(instant_str)
            upper_threshold = (
                brackets[i + 1].threshold(instant_str) if i < num_thresholds - 1 else np.inf
            )
            income = sim.calc("total_income", period=year)
            person_in_range = (income >= lower_threshold) & (
                income < upper_threshold
            )
            income_tax_in_range = sim.calc("income_tax", period=year) * person_in_range
            household_income_tax = sim.map_to(
                income_tax_in_range, "person", "household"
            )
            aggregate = tf.reduce_sum(modified_weights * household_income_tax)
            target = brackets[i].amount(instant_str)
            l += (
                AGGREGATE_ERROR_PENALTY
                * target
                * ((aggregate / target) - 1) ** 2
                / num_thresholds
            )

        # Population by age

        brackets = statistics.population_by_age.brackets
        num_thresholds = len(brackets)
        for i in range(num_thresholds):
            lower_threshold = brackets[i].threshold(instant_str)
            upper_threshold = (
                brackets[i + 1].threshold(instant_str) if i < num_thresholds - 1 else np.inf
            )
            age = sim.calc("age", period=year)
            person_in_range = (age >= lower_threshold) & (
                age < upper_threshold
            )
            household_count = sim.map_to(
                person_in_range, "person", "household"
            )
            population = tf.reduce_sum(modified_weights * household_count)
            if year > 2019:
                current_population = sum([getattr(statistic_set.populations, region) for region in regions])
                last_year_population = sum([getattr(statistics(f"{year-1}-01-01").populations, region) for region in regions])
                population_increase_ratio = current_population / last_year_population
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

        l += (
            POPULATION_ERROR_PENALTY
            * PARTICIPATION_ERROR_PENALTY
            * weights.sum()
            * ((tf.reduce_sum(modified_weights) / weights.sum()) - 1) ** 2
        )

    # Add penalty for weight changes
    if include_modification_penalty:
        l += tf.reduce_sum(MODIFICATION_PENALTY * weight_modification ** 2)
    return l


opt = tf.keras.optimizers.Adam(learning_rate=4e+1)
# Run training
weight_changes = tf.Variable(
    np.zeros((4, survey_num_households)), dtype=tf.float32
)
task = tqdm(range(512), desc="Training")
start_loss = loss(weight_changes, include_modification_penalty=False)
for i in task:
    with tf.GradientTape() as tape:
        l = loss(weight_changes)
        l_acc = loss(weight_changes, include_modification_penalty=False)
        task.set_description(f"Loss reduction: {(l_acc.numpy() / start_loss.numpy())-1:.2%}")
        gradients = tape.gradient(l, weight_changes)
    opt.apply_gradients(zip([gradients], [weight_changes]))

x = weight_changes.numpy()

sim_reweighted = Microsimulation()
for year in range(START_YEAR, END_YEAR + 1):
    added_households = x[year - START_YEAR].sum()
    new_weights = np.maximum(
        0,
        sim.calc("household_weight", period=year).values
        + x[year - START_YEAR],
    )
    sim_reweighted.set_input(
        "household_weight",
        year,
        new_weights,
    )
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
        new_weights = sim_reweighted.calc("household_weight", period=year).values
        entity = sim.simulation.tax_benefit_system.variables[
            program
        ].entity.key
        if program in statistics.aggregate.children:
            # Aggregate
            household_values = sim.map_to(values, entity, "household")
            frs_weighted = (household_values * frs_weights).sum()
            reweighted = (household_values * new_weights).sum()
            official = getattr(statistics.aggregate(f"{year}-01-01"), program)
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

df = pd.DataFrame(
    {
        "Program": programs,
        "Year": years,
        "Metric": metrics,
        "FRS-weighted": frs,
        "Re-weighted": reweight,
        "Official": official_stats,
    }
)

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
            if abs(new_error) > abs(original_error):
                message = f"{program} {year} {metric} error increases to {new_error:,.2f} from {original_error:,.2f}"
                if FORCE_ALL_METRIC_IMPROVEMENT:
                    raise ValueError(message)
                else:
                    logging.info(message)

with h5py.File(Path(__file__).parent / "frs_weights.h5", "w") as f:
    for year in range(START_YEAR, END_YEAR + 1):
        f.create_dataset(
            f"{year}",
            data=sim_reweighted.calc("household_weight", period=year).values,
        )

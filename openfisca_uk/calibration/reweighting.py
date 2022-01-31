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
statistics = parameters.statistics

START_YEAR = 2019
END_YEAR = 2022

FORCE_ALL_METRIC_IMPROVEMENT = False  # Don't save weights unless all (program, year, aggregate/caseload) tests improve. If false, regressions will be logged.
MODIFICATION_PENALTY = 1e-10

household_population = sim.calc("people", map_to="household").values
household_region = sim.calc("region").values
regions = list(pd.Series(household_region).unique())
survey_num_households = len(sim.calc("household_id"))


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
                values = sim.calc(
                    variable, period=year
                ).values
                entity = sim.simulation.tax_benefit_system.variables[variable].entity.key
                household_totals = sim.map_to(values, entity, "household")
                household_participants = sim.map_to((values > 0) * 1, entity, "household")
                # Calculate aggregate error
                agg = tf.reduce_sum(modified_weights * household_totals)
                target = getattr(statistic_set.aggregate, variable)
                l += ((agg / target) - 1) ** 2
            if variable in statistic_set.count._children:
                # Calculate caseload error
                count = tf.reduce_sum(modified_weights * household_participants)
                target = getattr(statistic_set.count, variable)
                l += ((count - target) / 1e6) ** 2
        for region in regions:
            in_region = household_region == region
            people_in_region = household_population * in_region
            population = tf.reduce_sum(people_in_region * modified_weights)
            target = getattr(statistic_set.populations, region)
            l += ((population - target) / 1e6) ** 2
        
        l += 10 * ((tf.reduce_sum(modified_weights) - weights.sum()) / 1e6) ** 2


    # Add penalty for weight changes
    if include_modification_penalty:
        l += tf.reduce_sum(MODIFICATION_PENALTY * weight_modification ** 2)
    return l


opt = tf.keras.optimizers.Adam(learning_rate=1e3)
# Run training
weight_changes = tf.Variable(
    np.zeros((4, survey_num_households)), dtype=tf.float32
)
task = tqdm(range(1024), desc="Training")
for i in task:
    with tf.GradientTape() as tape:
        l = loss(weight_changes)
        l_acc = loss(weight_changes, include_modification_penalty=False)
        task.set_description(f"Loss: {l_acc.numpy():.4f}")
        gradients = tape.gradient(l, weight_changes)
    opt.apply_gradients(zip([gradients], [weight_changes]))

x = weight_changes.numpy()

sim_reweighted = Microsimulation()
for year in range(START_YEAR, END_YEAR + 1):
    added_households = x[year - START_YEAR].sum()
    new_weights = np.maximum(
        0, sim.calc("household_weight", period=year).values + x[year - START_YEAR]
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
        if program in statistics.aggregate.children:
            # Aggregate
            frs_weighted = sim.calc(
                program, period=year, map_to="household"
            ).sum()
            reweighted = sim_reweighted.calc(
                program, period=year, map_to="household"
            ).sum()
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
            frs_weighted = (
                sim.calc(program, period=year, map_to="household") > 0
            ).sum()
            reweighted = (
                sim_reweighted.calc(program, period=year, map_to="household")
                > 0
            ).sum()
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

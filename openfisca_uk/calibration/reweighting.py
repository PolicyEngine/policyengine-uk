from pathlib import Path
import h5py
from tqdm import tqdm
from openfisca_uk import Microsimulation
import pandas as pd
import numpy as np
import tensorflow as tf

tf.get_logger().setLevel("INFO")

sim = Microsimulation(adjust_weights=False)
parameters = sim.simulation.tax_benefit_system.parameters
statistics = parameters.statistics

START_YEAR = 2019
END_YEAR = 2022

MODIFICATION_PENALTY = 1e-11

household_population = sim.calc("people", map_to="household").values
household_region = sim.calc("region").values
regions = list(pd.Series(household_region).unique())
survey_num_households = len(sim.calc("household_id"))


def loss(weight_modification: np.array) -> float:
    # Ensure the weight modification doesn't increase the total number of UK households
    weight_modification = (
        weight_modification
        - tf.reduce_sum(weight_modification, axis=0) / survey_num_households
    )
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
            values = sim.calc(variable, period=year, map_to="household").values
            # Calculate aggregate error
            agg = tf.reduce_sum(modified_weights * values)
            target = getattr(statistic_set.aggregate, variable)
            l += ((agg - target) / 1e9) ** 2
            # Calculate caseload error
            if variable in ("income_tax", "total_NI"):
                continue
            values = (values > 0) * 1
            count = tf.reduce_sum(modified_weights * values)
            target = getattr(statistic_set.count, variable)
            l += ((count - target) / 1e6) ** 2
        for region in regions:
            people_in_region = household_population * (
                household_region == region
            )
            population = tf.reduce_sum(people_in_region * modified_weights)
            target = getattr(statistic_set.populations, region)
            l += ((population - target) / 1e6) ** 2

    # Add penalty for weight changes
    l += tf.reduce_sum(MODIFICATION_PENALTY * weight_modification ** 2)
    return l


opt = tf.keras.optimizers.Adam(learning_rate=1e2)
# Run training
weight_changes = tf.Variable(
    np.zeros((4, survey_num_households)), dtype=tf.float32
)
task = tqdm(range(1024), desc="Training")
for i in task:
    with tf.GradientTape() as tape:
        l = loss(weight_changes)
        task.set_description(f"Loss: {l.numpy():.4f}")
        gradients = tape.gradient(l, weight_changes)
    opt.apply_gradients(zip([gradients], [weight_changes]))

x = weight_changes.numpy()
# Apply normalisation step from loss function
x -= x.sum(axis=0) / survey_num_households

sim_reweighted = Microsimulation()
for year in range(2019, 2023):
    sim_reweighted.set_input(
        "household_weight",
        year,
        np.maximum(
            0, sim.calc("household_weight", year).values + x[year - 2019]
        ),
    )
variables = list(statistics.aggregate.children)


programs = []
years = []
metrics = []
frs = []
reweight = []
official_stats = []

for year in range(2019, 2023):
    for program in variables:
        # Aggregate
        frs_weighted = sim.calc(program, period=year, map_to="household").sum()
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

        if program in ("income_tax", "total_NI"):
            continue
        # Caseload
        frs_weighted = (
            sim.calc(program, period=year, map_to="household") > 0
        ).sum()
        reweighted = (
            sim_reweighted.calc(program, period=year, map_to="household") > 0
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
                raise ValueError(
                    f"{program} {year} {metric} error increases to {new_error:,.1f}k from {original_error:,.1f}"
                )

with h5py.File(Path(__file__).parent / "frs_weights.h5", "w") as f:
    for year in range(START_YEAR, END_YEAR + 1):
        f.create_dataset(
            f"{year}",
            data=sim_reweighted.calc("household_weight", period=year).values,
        )

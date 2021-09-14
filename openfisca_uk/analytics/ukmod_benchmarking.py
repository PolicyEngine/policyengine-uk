"""
This module tests the microsimulation outputs produced by openfisca-uk-data against UKMOD - checking that the distributions are similar.
"""

import numpy as np
from openfisca_uk_data import BaseFRS, FRS, UKMODOutput, RawFRS
from openfisca_uk import Microsimulation, REPO
from microdf import MicroDataFrame
from itertools import product
from functools import partial
import pandas as pd
import yaml

# Run the dataset generation and load test data


def benchmark_against_UKMOD(
    dataset=FRS, year=2018, reform=(), reform_label="baseline"
):
    with open(REPO / "analytics" / "variable_metadata.yml") as f:
        METADATA = yaml.load(f)
    baseline = Microsimulation(reform, dataset=dataset)
    ukmod = UKMODOutput.load(year, "person")
    ukmod = MicroDataFrame(ukmod, weights=ukmod.person_weight)

    # Prepare the metrics and their calculating functions

    metrics = [
        "sum",
        "nonzero",
    ]
    calc_functions = [
        lambda values: values.sum(),
        lambda values: (values > 0).sum(),
    ]
    metric_to_func = {m: f for m, f in zip(metrics, calc_functions)}

    # For each variable pair and metric, compute relative and absolute error

    results = []

    for variable, metric in product(METADATA.keys(), metrics):
        metadata = METADATA[variable]
        result = metric_to_func[metric](baseline.calc(variable, period=year))
        target = metric_to_func[metric](ukmod[metadata["ukmod"]])
        rel_err = abs(result / target - 1)
        abs_err = abs(result - target)
        passed = (abs_err < 10) or (rel_err < metadata["max_rel_err"])
        results += [
            [
                dataset.name,
                reform_label,
                year,
                variable,
                metadata["ukmod"],
                metric,
                result,
                target,
                rel_err,
                abs_err,
                metadata["max_rel_err"],
                passed,
            ]
        ]

    return pd.DataFrame(
        results,
        columns=(
            "dataset",
            "reform",
            "year",
            "variable",
            "UKMOD_variable",
            "metric",
            "openfisca_uk",
            "UKMOD",
            "rel_err",
            "abs_err",
            "max_rel_err",
            "passed",
        ),
    )

from openfisca_uk.api import *
from openfisca_uk.graphs import waterfall_chart


def test_single_reform_waterfall_chart_runs():
    reform = reforms.structural.abolish(
        "personal_allowance"
    ), reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.benefit.child_benefit.amount.eldest, 50
    )
    waterfall_chart(reform, ["Abolish PA", "Increase CB"])


def test_multiple_reform_waterfall_chart_runs():
    reform_1 = reforms.structural.abolish(
        "personal_allowance"
    ), reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.benefit.child_benefit.amount.eldest, 50
    )
    reform_2 = reforms.structural.abolish(
        "personal_allowance"
    ), reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.benefit.child_benefit.amount.eldest, 300
    )
    waterfall_chart(
        [reform_1, reform_2],
        ["Abolish PA", "Increase CB"],
        reform_labels=["CB=£50", "CB=£300"],
    )

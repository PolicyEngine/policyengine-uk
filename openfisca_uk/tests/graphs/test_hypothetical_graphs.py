from openfisca_uk.graphs import mtr_chart, budget_chart
from openfisca_uk import BASELINE_PARAMETERS
from openfisca_uk.api import reforms, graphs, BASELINE_PARAMETERS


def test_wide_form_individual_data_with_one_reform():
    abolish_PA = reforms.structural.abolish("personal_allowance")
    graphs.data.get_wide_reform_individual_data(
        [abolish_PA], ["Abolish PA"], ["net_income", "tax"]
    )


def test_wide_form_individual_data_with_two_reforms():
    abolish_PA = reforms.structural.abolish("personal_allowance")
    halve_PA = reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.tax.income_tax.allowances.personal_allowance.amount,
        6250,
    )
    graphs.data.get_wide_reform_individual_data(
        [halve_PA, abolish_PA],
        ["Halve PA", "Abolish PA"],
        ["net_income", "tax"],
    )


def test_single_reform_MTR_and_budget_plot():
    reform = reforms.structural.abolish(
        "personal_allowance"
    ), reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.benefit.universal_credit.means_test.reduction_rate,
        0.4,
    )
    budget_chart(reform)
    mtr_chart(reform)


def test_multiple_reform_MTR_and_budget_plot():
    reform_1 = reforms.structural.abolish(
        "personal_allowance"
    ), reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.benefit.universal_credit.means_test.reduction_rate,
        0.4,
    )
    reform_2 = reforms.structural.abolish(
        "personal_allowance"
    ), reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.benefit.universal_credit.means_test.reduction_rate,
        0.1,
    )
    budget_chart([reform_1, reform_2], names=["CB=£50", "CB=£300"])
    mtr_chart([reform_1, reform_2], names=["CB=£50", "CB=£300"])

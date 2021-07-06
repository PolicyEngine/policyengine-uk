from openfisca_uk import BASELINE_PARAMETERS
from openfisca_uk.api import reforms, graphs, BASELINE_PARAMETERS


def test_wide_form_individual_data_with_one_reform():
    abolish_PA = reforms.structural.abolish("personal_allowance")
    df = graphs.data.get_wide_reform_individual_data(
        [abolish_PA], ["Abolish PA"], ["net_income", "tax"]
    )


def test_wide_form_individual_data_with_two_reforms():
    abolish_PA = reforms.structural.abolish("personal_allowance")
    halve_PA = reforms.parametric.set_parameter(
        BASELINE_PARAMETERS.tax.income_tax.allowances.personal_allowance.amount,
        6250,
    )
    df = graphs.data.get_wide_reform_individual_data(
        [halve_PA, abolish_PA],
        ["Halve PA", "Abolish PA"],
        ["net_income", "tax"],
    )

from policyengine_core.model_api import *


def create_budget_adjustment(change_by_year: dict, budget_variable: str):
    """
    Create a reform that adjusts a specific budget variable.

    Args:
        change_by_year: Dict mapping year to budget change amount
        budget_variable: Name of the budget variable to adjust
    """

    class adjust_budget_reform(Reform):
        def apply(self):
            simulation = self.simulation

            for time_period, budget_change in change_by_year.items():
                spending = simulation.calculate(budget_variable, time_period)
                relative_increase = budget_change / (spending.sum() / 1e9)

                simulation.set_input(
                    budget_variable,
                    time_period,
                    spending * (1 + relative_increase),
                )

    return adjust_budget_reform


def adjust_budget(
    baseline_parameter, parameter, budget_variable, bypass: bool = False
):
    """
    Create a budget adjustment reform by comparing baseline to reformed values.

    Args:
        baseline_parameter: The baseline parameter tree
        parameter: The reformed parameter tree
        budget_variable: Name of the budget variable to adjust
        bypass: If True, skip the parameter comparison check
    """
    change_by_year = {}

    for time_period in range(2023, 2030):
        baseline_budget = baseline_parameter(time_period)
        reformed_budget = parameter(time_period)

        if baseline_budget == reformed_budget:
            continue

        budget_change = reformed_budget - baseline_budget

        change_by_year[time_period] = budget_change

    if len(change_by_year) == 0:
        return None

    return create_budget_adjustment(change_by_year, budget_variable)


def adjust_budgets(parameters, period, bypass: bool = False):
    """
    Reform that adjusts government department budgets.

    Policy: Adjust education, NHS, and transport spending based on
    parameter differences from baseline.
    """
    budgets = [
        (
            parameters.baseline.gov.dfe.education_spending,
            parameters.gov.dfe.education_spending,
            "dfe_education_spending",
        ),
        (
            parameters.baseline.gov.dhsc.spending,
            parameters.gov.dhsc.spending,
            "nhs_spending",
        ),
        (
            parameters.baseline.gov.dft.spending,
            parameters.gov.dft.spending,
            "dft_subsidy_spending",
        ),
    ]

    reforms = []

    for baseline_parameter, parameter, budget_variable in budgets:
        budget_reform = adjust_budget(
            baseline_parameter, parameter, budget_variable
        )
        if budget_reform is not None:
            reforms.append(budget_reform)

    if len(reforms) == 0:
        return None

    class adjust_budgets_reform(Reform):
        def apply(self):
            for reform in reforms:
                reform.apply(self)

    return adjust_budgets_reform

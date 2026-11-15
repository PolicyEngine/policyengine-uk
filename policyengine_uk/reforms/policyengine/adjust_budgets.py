from policyengine_core.model_api import *


def adjust_budgets(parameters, period):
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
        budget_reform = adjust_budget(baseline_parameter, parameter, budget_variable)
        if budget_reform is not None:
            reforms.append(budget_reform)

    if len(reforms) == 0:
        return None

    class adjust_budgets_reform(Reform):
        def apply(self):
            for reform in reforms:
                reform.apply(self)

    return adjust_budgets_reform


def adjust_budget(baseline_parameter, parameter, budget_variable):
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

    class adjust_budget_reform(Reform):
        def apply(self):
            simulation = self.simulation

            # Read every year's allocation before writing any. Each write is
            # an input that carries over to later years without their own
            # input, so reading a later year after writing an earlier one
            # would stack the earlier year's change on top of its own.
            spending_by_year = {
                time_period: simulation.calculate(budget_variable, time_period)
                for time_period in change_by_year
            }

            for time_period, budget_change in change_by_year.items():
                spending = spending_by_year[time_period]
                total_spending = spending.sum() / 1e9
                if total_spending == 0:
                    # Nothing is allocated in this year, so there is no
                    # allocation to scale. Dividing by zero would write NaN
                    # (rejected by set_input) or infinite spending.
                    continue
                relative_increase = budget_change / total_spending

                simulation.set_input(
                    budget_variable,
                    time_period,
                    spending * (1 + relative_increase),
                )

    return adjust_budget_reform

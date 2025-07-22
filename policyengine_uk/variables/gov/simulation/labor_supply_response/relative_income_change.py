from policyengine_uk.model_api import *


class relative_income_change(Variable):
    value_type = float
    entity = Person
    label = "relative income change"
    unit = "/1"
    definition_period = YEAR
    requires_computation_after = "employment_income_behavioral_response"

    def formula(person, period, parameters):
        simulation = person.simulation
        measurement_branch = simulation.get_branch("lsr_measurement")
        baseline_branch = simulation.get_branch("baseline").get_branch(
            "baseline_lsr_measurement"
        )
        baseline_branch.set_input(
            "capital_gains_before_response",
            period,
            person("capital_gains_before_response", period),
        )
        measurement_person = measurement_branch.populations["person"]
        baseline_person = baseline_branch.populations["person"]
        baseline_net_income = baseline_person.household(
            "household_net_income", period
        )
        net_income = measurement_person.household(
            "household_net_income", period
        )
        income_change_bound = parameters(
            period
        ).gov.simulation.labor_supply_responses.bounds.income_change
        # _c suffix for "clipped"
        baseline_net_income_c = np.clip(baseline_net_income, 1, None)
        net_income_c = np.clip(net_income, 1, None)
        relative_change = (
            net_income_c - baseline_net_income_c
        ) / baseline_net_income_c
        return np.clip(
            relative_change, -income_change_bound, income_change_bound
        )

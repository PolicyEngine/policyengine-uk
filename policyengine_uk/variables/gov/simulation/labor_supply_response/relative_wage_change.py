from policyengine_uk.model_api import *


class relative_wage_change(Variable):
    value_type = float
    entity = Person
    label = "relative wage change"
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
        baseline_mtr = baseline_person("marginal_tax_rate", period)
        baseline_wage = 1 - baseline_mtr
        mtr = measurement_person("marginal_tax_rate", period)
        wage_rate = 1 - mtr
        # _c suffix for "clipped"
        baseline_wage_c = np.where(baseline_wage == 0, 0.01, baseline_wage)
        wage_rate_c = np.where(wage_rate == 0, 0.01, wage_rate)
        relative_change = (wage_rate_c - baseline_wage_c) / baseline_wage_c
        wage_change_bound = parameters(
            period
        ).gov.simulation.labor_supply_responses.bounds.effective_wage_rate_change
        return np.clip(relative_change, -wage_change_bound, wage_change_bound)

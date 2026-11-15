from policyengine_uk.model_api import *
from policyengine_uk.utils.labour_supply_responses import measurement_branches


class relative_wage_change(Variable):
    value_type = float
    entity = Person
    label = "relative wage change"
    unit = "/1"
    definition_period = YEAR
    requires_computation_after = "employment_income_behavioral_response"

    def formula(person, period, parameters):
        if person.simulation.baseline is None:
            return 0  # No reform, no change
        with measurement_branches(person, period) as (
            measurement_branch,
            baseline_branch,
        ):
            measurement_person = measurement_branch.populations["person"]
            baseline_person = baseline_branch.populations["person"]
            baseline_mtr = baseline_person("marginal_tax_rate", period)
            mtr = measurement_person("marginal_tax_rate", period)
        baseline_wage = 1 - baseline_mtr
        wage_rate = 1 - mtr
        # _c suffix for "clipped"
        baseline_wage_c = np.where(baseline_wage == 0, 0.01, baseline_wage)
        wage_rate_c = np.where(wage_rate == 0, 0.01, wage_rate)
        relative_change = (wage_rate_c - baseline_wage_c) / baseline_wage_c
        wage_change_bound = parameters(
            period
        ).gov.simulation.labour_supply_responses.bounds.effective_wage_rate_change
        return np.clip(relative_change, -wage_change_bound, wage_change_bound)

from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.capital_gains import measure_capital_gains_mtrs


class relative_capital_gains_mtr_change(Variable):
    value_type = float
    entity = Person
    label = "relative change in capital gains tax rate"
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        reform_mtr, baseline_mtr = measure_capital_gains_mtrs(person, period)

        # Handle zeros in tax rates to prevent log(0)
        min_rate = 0.001
        baseline_mtr_adj = np.maximum(baseline_mtr, min_rate)
        reform_mtr_adj = np.maximum(reform_mtr, min_rate)

        # Calculate log difference
        return np.log(reform_mtr_adj) - np.log(baseline_mtr_adj)

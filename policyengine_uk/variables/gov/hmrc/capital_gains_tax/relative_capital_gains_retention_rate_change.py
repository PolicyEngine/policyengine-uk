from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.capital_gains import measure_capital_gains_mtrs


class relative_capital_gains_retention_rate_change(Variable):
    value_type = float
    entity = Person
    label = "relative change in the capital gains retention rate"
    documentation = (
        "Log change in the share of a marginal pound of gains kept after tax. "
        "The empirical literature estimates realisation elasticities against "
        "this retention rate rather than against the tax rate."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        reform_mtr, baseline_mtr = measure_capital_gains_mtrs(person, period)

        # Floor the retention rate to keep the log defined where a marginal
        # pound of gains is taxed away in full.
        min_retention_rate = 0.001
        baseline_retention = np.maximum(1 - baseline_mtr, min_retention_rate)
        reform_retention = np.maximum(1 - reform_mtr, min_retention_rate)

        return np.log(reform_retention) - np.log(baseline_retention)

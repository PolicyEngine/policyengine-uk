from policyengine_uk.model_api import *


class uc_deduction_rate(Variable):
    label = "UC deduction rate"
    documentation = (
        "Cash deduction demand divided by the current standard allowance. "
        "This reporting ratio changes when a reform changes the allowance while "
        "fixed cash demand stays the same. uc_deduction_demand supplies the "
        "award calculation directly, including when the allowance is zero."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float

    def formula(benunit, period, parameters):
        allowance = benunit("uc_standard_allowance", period)
        demand = benunit("uc_deduction_demand", period)
        return np.divide(
            demand, allowance, out=np.zeros_like(demand), where=allowance > 0
        )

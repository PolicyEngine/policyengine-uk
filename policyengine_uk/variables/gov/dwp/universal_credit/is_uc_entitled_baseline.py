from policyengine_uk.model_api import *


class is_uc_entitled_baseline(Variable):
    label = "meets the means test for Universal Credit under baseline law"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        if benunit.simulation.baseline is None:
            return True
        baseline = benunit.simulation.baseline.populations["benunit"]
        uc = baseline("universal_credit_pre_benefit_cap", period)
        return uc > 0

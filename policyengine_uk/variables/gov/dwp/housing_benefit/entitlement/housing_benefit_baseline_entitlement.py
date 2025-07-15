from policyengine_uk.model_api import *


class housing_benefit_baseline_entitlement(Variable):
    label = "basleine Housing Benefit entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        if benunit.simulation.baseline is None:
            return 1
        baseline = benunit.simulation.baseline.populations["benunit"]
        return baseline("housing_benefit_entitlement", period)

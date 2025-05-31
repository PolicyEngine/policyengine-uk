from policyengine_uk.model_api import *


class baseline_ctc_entitlement(Variable):
    label = "Receives Child Tax Credit (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float

    def formula(benunit, period, parameters):
        if benunit.simulation.baseline is None:
            return 1
        baseline = benunit.simulation.baseline.populations["benunit"]
        return baseline("wtc_entitlement", period)

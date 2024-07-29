from policyengine_uk.model_api import *


class uc_standard_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit standard allowance"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.standard_allowance
        claimant_type = benunit("uc_standard_allowance_claimant_type", period)
        return p.amount[claimant_type] * MONTHS_IN_YEAR

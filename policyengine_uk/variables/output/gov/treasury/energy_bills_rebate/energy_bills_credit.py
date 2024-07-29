from policyengine_uk.model_api import *


class ebr_energy_bills_credit(Variable):
    label = "Energy bills credit (EBR)"
    documentation = "Credit on energy bills under the Energy Bills Rebate scheme. Modeled as a flat transfer."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ebr = parameters(period).gov.treasury.energy_bills_rebate
        return ebr.energy_bills_credit

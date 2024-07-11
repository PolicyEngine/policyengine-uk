from policyengine_uk.model_api import *


class uc_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    definition_period = YEAR
    unit = GBP
    defined_for = "benunit_has_carer"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.carer
        return p.amount * MONTHS_IN_YEAR

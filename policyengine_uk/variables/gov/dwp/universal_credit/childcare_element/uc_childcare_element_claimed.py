from policyengine_uk.model_api import *


class uc_childcare_element_claimed(Variable):
    value_type = bool
    entity = BenUnit
    label = "claims the Universal Credit childcare element"
    documentation = "Meets the childcare work condition and would claim the element."
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("uc_childcare_work_condition", period) & benunit(
            "would_claim_uc_childcare", period
        )

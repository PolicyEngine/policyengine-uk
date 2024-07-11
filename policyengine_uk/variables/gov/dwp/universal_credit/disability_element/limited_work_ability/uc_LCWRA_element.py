from policyengine_uk.model_api import *


class uc_LCWRA_element(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Universal Credit limited capability for work-related-activity element"
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.disabled
        limited_capability = benunit.members(
            "uc_limited_capability_for_WRA", period
        )
        person_amounts = limited_capability * p.amount
        return benunit.sum(person_amounts) * MONTHS_IN_YEAR

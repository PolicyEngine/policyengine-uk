from policyengine_uk.model_api import *


class universal_childcare_entitlement_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "universal childcare entitlement hours per year"
    documentation = "Number of free childcare hours per year the benefit unit is entitled to"
    definition_period = YEAR
    unit = "hour"

    def formula(benunit, period, parameters):
        is_eligible = benunit(
            "universal_childcare_entitlement_eligibility", period
        )
        hours = parameters(
            period
        ).gov.dwp.universal_childcare_entitlement.hours_per_year
        return where(is_eligible, hours, 0)

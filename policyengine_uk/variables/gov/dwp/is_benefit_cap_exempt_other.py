from policyengine_uk.model_api import *


class is_benefit_cap_exempt_other(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap for non-health/disability reasons"
    definition_period = YEAR
    reference = "https://www.gov.uk/benefit-cap/when-youre-not-affected"

    def formula(benunit, period, parameters):
        # Anyone in the benefit unit over state pension age
        person = benunit.members
        has_pensioner = benunit.any(person("is_SP_age", period))

        # Armed Forces Compensation Scheme payments
        afcs = benunit("afcs", period) > 0

        # ESA contribution-based with support component
        esa_support_component = benunit("esa_contrib", period) > 0

        return has_pensioner | afcs | esa_support_component

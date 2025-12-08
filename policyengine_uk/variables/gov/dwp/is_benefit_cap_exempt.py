from policyengine_uk.model_api import *


class is_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether exempt from the benefits cap because of health or disability"
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/benefit-cap/when-youre-not-affected"

    def formula(benunit, period, parameters):
        exempt_health = benunit(
            "is_benefit_cap_exempt_health_disability", period
        )
        exempt_other = benunit("is_benefit_cap_exempt_other", period)
        exempt_earnings = benunit("is_benefit_cap_exempt_earnings", period)
        return exempt_health | exempt_earnings | exempt_other

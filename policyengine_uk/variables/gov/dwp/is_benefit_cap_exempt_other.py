from policyengine_uk.model_api import *


class is_benefit_cap_exempt_other(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the benefit cap because of age"
    documentation = (
        "Whether anyone in the benefit unit has reached State Pension age. "
        "The armed forces compensation and support-component ESA exceptions "
        "are in is_benefit_cap_exempt_health_disability, which limits them "
        "to the claimant and partner."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/benefit-cap/when-youre-not-affected"

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("is_SP_age", period))

from policyengine_uk.model_api import *


class housing_benefit_has_main_phase_esa(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit claimant entitled to main-phase ESA"
    definition_period = YEAR
    default_value = False
    documentation = (
        "Pre-assessed main-phase ESA entitlement of the Housing Benefit "
        "claimant personally, as defined in GB Schedule 3 paragraph 1A "
        "or NI Schedule 4 paragraph 1A. A partner's entitlement alone does "
        "not establish this personal-allowance exception. Includes the "
        "specified converted-ESA/time-limit cases, not just current payment. "
        "Existing ESA variables report amounts and apply capital screens; "
        "they do not identify award phase. No dataset mapping is verified. "
        "Missing input defaults to false, preserving the age-based "
        "approximation and potentially understating qualifying allowances. "
        "This is not a new ESA entitlement calculation."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/part/I",
    )

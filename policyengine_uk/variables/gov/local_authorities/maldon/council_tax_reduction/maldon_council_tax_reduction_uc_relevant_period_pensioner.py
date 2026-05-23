from policyengine_uk.model_api import *


class maldon_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Maldon's Universal Credit relevant-period pensioner exception applies"
    )
    definition_period = YEAR
    reference = "https://democracy.maldon.gov.uk/documents/s40932/Appendix%203.pdf"
    default_value = False

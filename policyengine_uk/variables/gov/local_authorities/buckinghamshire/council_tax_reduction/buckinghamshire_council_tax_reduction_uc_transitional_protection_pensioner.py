from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_uc_transitional_protection_pensioner(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = "Whether a Buckinghamshire UC claimant remains in the pensioner scheme because the source disregards the UC award"
    documentation = "Covers the source rule disregarding a UC award for pensioner-status classification where Universal Credit Transitional Provisions regulation 60A applies."
    definition_period = YEAR
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"
    default_value = False

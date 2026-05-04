from policyengine_uk.model_api import *


class thurrock_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Thurrock disregards UC during the pension-age relevant period"
    definition_period = YEAR
    reference = "https://thurrock.moderngov.co.uk/documents/s51034/Enc.%201%20for%20Local%20Council%20Tax%20Support%20Scheme%202026-27.pdf"
    default_value = False

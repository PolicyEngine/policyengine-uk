from policyengine_uk.model_api import *


class east_hampshire_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether East Hampshire's Universal Credit regulation 60A pensioner "
        "exception applies"
    )
    definition_period = YEAR
    reference = "https://www.easthants.gov.uk/sites/default/files/2026-03/Council%20tax%20support%20scheme%202026-27.pdf"
    default_value = False

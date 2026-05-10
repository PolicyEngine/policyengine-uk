from policyengine_uk.model_api import *


class rushmoor_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Rushmoor's Universal Credit regulation 60A pensioner exception applies"
    )
    definition_period = YEAR
    reference = "https://www.rushmoor.gov.uk/media/qvmlpekv/rushmoor-s13a-scheme-202627-final.pdf"
    default_value = False

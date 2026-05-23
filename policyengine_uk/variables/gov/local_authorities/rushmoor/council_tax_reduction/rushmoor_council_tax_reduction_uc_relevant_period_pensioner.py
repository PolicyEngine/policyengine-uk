from policyengine_uk.model_api import *


class rushmoor_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Rushmoor's Universal Credit relevant-period pensioner exception applies"
    definition_period = YEAR
    reference = "https://www.rushmoor.gov.uk/media/qvmlpekv/rushmoor-s13a-scheme-202627-final.pdf"
    default_value = False

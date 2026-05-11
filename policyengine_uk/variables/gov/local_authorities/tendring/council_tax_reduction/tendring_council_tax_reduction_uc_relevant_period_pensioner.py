from policyengine_uk.model_api import *


class tendring_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Tendring's Universal Credit relevant-period pensioner exception applies"
    definition_period = YEAR
    reference = "https://legacy.tendringdc.gov.uk/sites/default/files/documents/Council_Tax/Tendring%20S13A%20202627%20Scheme%20Final.pdf"
    default_value = False

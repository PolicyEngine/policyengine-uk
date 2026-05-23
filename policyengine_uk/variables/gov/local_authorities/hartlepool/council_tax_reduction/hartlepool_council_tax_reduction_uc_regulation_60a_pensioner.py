from policyengine_uk.model_api import *


class hartlepool_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Hartlepool's Universal Credit regulation 60A pensioner exception applies"
    definition_period = YEAR
    reference = "https://www.hartlepool.gov.uk/downloads/file/1484/hbc-council-tax-reduction-scheme-2026-27"
    default_value = False

from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether a Southend-on-Sea pension-age Universal Credit award remains in the prescribed pensioner CTR scheme during the source relevant period"
    documentation = "Covers the source transitional protection where a Universal Credit award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://www.southend.gov.uk/downloads/file/3527/southend-on-sea-borough-council-ctax-reduction-s13a-scheme"
    default_value = False

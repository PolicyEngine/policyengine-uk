from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction_source_disregarded_uc_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Southend-on-Sea CTR source-disregarded Universal Credit elements"
    documentation = "Universal Credit elements disregarded by the source but not otherwise separately exposed in PolicyEngine UK."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southend.gov.uk/downloads/file/3527/southend-on-sea-borough-council-ctax-reduction-s13a-scheme"
    default_value = 0

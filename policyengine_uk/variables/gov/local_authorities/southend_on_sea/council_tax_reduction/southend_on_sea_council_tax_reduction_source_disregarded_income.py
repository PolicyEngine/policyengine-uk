from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Southend-on-Sea CTR source-disregarded annual income"
    documentation = "Source-listed income disregards not otherwise separately exposed in PolicyEngine UK, such as compensation payments, mobility supplements, or local welfare payments."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southend.gov.uk/downloads/file/3527/southend-on-sea-borough-council-ctax-reduction-s13a-scheme"
    default_value = 0

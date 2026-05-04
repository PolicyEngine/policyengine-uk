from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction_childcare_disabled_child(Variable):
    value_type = bool
    entity = Person
    label = "Southend-on-Sea CTR source-defined disabled child for childcare deduction"
    documentation = "Covers source disabled-child status for childcare age-limit rules not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.southend.gov.uk/downloads/file/3527/southend-on-sea-borough-council-ctax-reduction-s13a-scheme"
    default_value = False

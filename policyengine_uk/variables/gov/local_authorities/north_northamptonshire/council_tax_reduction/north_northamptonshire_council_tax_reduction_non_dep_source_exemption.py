from policyengine_uk.model_api import *


class north_northamptonshire_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a North Northamptonshire CTR non-dependant has a section 30.7 or 30.8 deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, youth-training allowance, long-term patient status, or Schedule 1 discount-disregarded cases."
    definition_period = YEAR
    reference = "https://cms.northnorthants.gov.uk/media/4157/download"
    default_value = False

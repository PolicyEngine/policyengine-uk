from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a West Northamptonshire CTR non-dependant has a source-defined deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, youth-training allowance, long-term patient status, or Schedule 1 discount-disregarded cases."
    definition_period = YEAR
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"
    default_value = False

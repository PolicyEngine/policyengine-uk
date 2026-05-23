from policyengine_uk.model_api import *


class arun_council_tax_reduction_childcare_disabled_child(Variable):
    value_type = bool
    entity = Person
    label = "Whether Arun treats this child as disabled for childcare deductions"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for Arun childcare disabled-child statuses not otherwise fully represented in PolicyEngine UK, including suspended or abated qualifying disability benefits and blind registration."
    default_value = False

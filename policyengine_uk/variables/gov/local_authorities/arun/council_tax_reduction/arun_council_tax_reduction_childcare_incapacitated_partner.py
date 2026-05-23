from policyengine_uk.model_api import *


class arun_council_tax_reduction_childcare_incapacitated_partner(Variable):
    value_type = bool
    entity = Person
    label = "Whether Arun treats this partner as incapacitated for childcare deductions"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for childcare partner incapacity, hospital in-patient, prison, temporary sickness, and related statuses not otherwise fully represented in PolicyEngine UK."
    default_value = False

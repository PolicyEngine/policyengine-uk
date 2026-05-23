from policyengine_uk.model_api import *


class arun_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether Arun source rules exempt this non-dependant from deductions"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for non-dependant exemptions not otherwise separately exposed in PolicyEngine UK."
    default_value = False

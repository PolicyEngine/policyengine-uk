from policyengine_uk.model_api import *


class arun_council_tax_reduction_non_dep_guarantee_credit(Variable):
    value_type = bool
    entity = Person
    label = "Whether this Arun non-dependant receives Pension Credit Guarantee Credit"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for the Arun non-dependant exemption that applies to Pension Credit Guarantee Credit, not Savings Credit alone."
    default_value = False

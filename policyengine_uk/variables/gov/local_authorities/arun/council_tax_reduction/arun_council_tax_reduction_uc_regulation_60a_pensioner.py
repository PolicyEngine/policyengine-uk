from policyengine_uk.model_api import *


class arun_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Arun disregards Universal Credit for pensioner status under regulation 60A"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for pension-age Universal Credit awards disregarded under regulation 60A of the Universal Credit Transitional Provisions Regulations 2014."
    default_value = False

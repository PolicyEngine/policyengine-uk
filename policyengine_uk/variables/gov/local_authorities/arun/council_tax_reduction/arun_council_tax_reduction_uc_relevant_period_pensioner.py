from policyengine_uk.model_api import *


class arun_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Arun disregards Universal Credit for pensioner status during the relevant period"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for pension-age Universal Credit awards whose final assessment period is disregarded when deciding whether the person remains in the pensioner scheme."
    default_value = False

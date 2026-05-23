from policyengine_uk.model_api import *


class arun_council_tax_reduction_source_uc_disregarded_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Arun Council Tax Reduction source-disregarded Universal Credit elements not otherwise modeled"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )

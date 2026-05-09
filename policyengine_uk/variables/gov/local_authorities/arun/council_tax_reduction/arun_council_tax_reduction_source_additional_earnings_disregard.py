from policyengine_uk.model_api import *


class arun_council_tax_reduction_source_additional_earnings_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Arun's source additional working earnings disregard applies"
    definition_period = YEAR
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )
    documentation = "Source input for Schedule 5 paragraph 18 conditions not otherwise exposed, such as Working Tax Credit disability or 50-plus element status."
    default_value = False

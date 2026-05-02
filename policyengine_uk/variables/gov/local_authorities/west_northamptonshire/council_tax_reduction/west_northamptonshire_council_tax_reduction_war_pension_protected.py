from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_war_pension_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "West Northamptonshire CTR claimant or partner receives a protected war pension"
    )
    documentation = "Whether the source 100 percent maximum support applies because the claimant or partner receives a war widows or war disablement pension."
    definition_period = YEAR
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"
    default_value = False

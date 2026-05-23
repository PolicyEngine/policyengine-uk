from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_care_leaver(Variable):
    value_type = bool
    entity = Person
    label = "West Northamptonshire CTR care leaver"
    documentation = (
        "Whether the person is a care leaver for the source full-support class."
    )
    definition_period = YEAR
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"
    default_value = False

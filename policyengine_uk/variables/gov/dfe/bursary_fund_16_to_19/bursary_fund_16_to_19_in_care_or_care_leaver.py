from policyengine_uk.model_api import *


class bursary_fund_16_to_19_in_care_or_care_leaver(Variable):
    value_type = bool
    entity = Person
    label = "In care or a care leaver for 16 to 19 Bursary Fund"
    documentation = "Whether the student is in care or is a care leaver for 16 to 19 Bursary Fund purposes."
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

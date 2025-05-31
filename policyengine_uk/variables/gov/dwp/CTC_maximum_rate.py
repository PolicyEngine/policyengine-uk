from policyengine_uk.model_api import *


class CTC_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum Child Tax Credit"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP

    adds = [
        "CTC_family_element",
        "CTC_child_element",
        "CTC_disabled_child_element",
        "CTC_severely_disabled_child_element",
    ]

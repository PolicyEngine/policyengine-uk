from policyengine_uk.model_api import *


class WTC_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit maximum rate"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP

    adds = [
        "WTC_basic_element",
        "WTC_couple_element",
        "WTC_lone_parent_element",
        "WTC_disabled_element",
        "WTC_severely_disabled_element",
        "WTC_worker_element",
        "WTC_childcare_element",
    ]

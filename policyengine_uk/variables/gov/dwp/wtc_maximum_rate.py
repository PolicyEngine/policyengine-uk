from policyengine_uk.model_api import *


class wtc_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit maximum rate"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP

    adds = [
        "wtc_basic_element",
        "wtc_couple_element",
        "wtc_lone_parent_element",
        "wtc_disabled_element",
        "wtc_severely_disabled_element",
        "wtc_worker_element",
        "wtc_childcare_element",
    ]

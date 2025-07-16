from policyengine_uk.model_api import *


class ctc_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum Child Tax Credit"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP

    adds = [
        "ctc_family_element",
        "ctc_child_element",
        "ctc_disabled_child_element",
        "ctc_severely_disabled_child_element",
    ]

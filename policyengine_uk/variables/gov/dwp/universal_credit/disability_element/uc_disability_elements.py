from policyengine_uk.model_api import *


class uc_disability_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit disability elements"
    definition_period = YEAR
    unit = GBP

    adds = [
        "uc_individual_disabled_child_element",
        "uc_individual_severely_disabled_child_element",
        "uc_LCWRA_element",
    ]

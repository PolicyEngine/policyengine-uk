from policyengine_uk.model_api import *


class uc_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit child element"
    definition_period = YEAR
    unit = GBP

    adds = ["uc_individual_child_element"]

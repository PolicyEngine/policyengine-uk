from policyengine_uk.model_api import *


class family_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Gross rent for the family"
    definition_period = YEAR
    unit = GBP

    adds = ["personal_rent"]

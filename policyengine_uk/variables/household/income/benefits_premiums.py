from policyengine_uk.model_api import *


class benefits_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Value of premiums for disability and carer status"
    definition_period = YEAR
    unit = GBP

    adds = [
        "disability_premium",
        "enhanced_disability_premium",
        "severe_disability_premium",
        "carer_premium",
    ]

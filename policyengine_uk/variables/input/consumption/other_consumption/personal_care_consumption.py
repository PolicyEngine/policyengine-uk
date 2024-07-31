from policyengine_uk.model_api import *


class personal_care_consumption(Variable):
    label = "personal care consumption"
    documentation = (
        "Consumption on personal care. Excludes childcare spending."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

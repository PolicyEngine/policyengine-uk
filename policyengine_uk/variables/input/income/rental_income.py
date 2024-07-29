from policyengine_uk.model_api import *


class rental_income(Variable):
    label = "rental income"
    documentation = "Income from rents and royalties of property."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

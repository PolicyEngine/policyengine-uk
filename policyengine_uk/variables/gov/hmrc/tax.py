from policyengine_uk.model_api import *


class tax(Variable):
    value_type = float
    entity = Person
    label = "Taxes"
    definition_period = YEAR
    unit = GBP

    adds = ["income_tax", "national_insurance"]

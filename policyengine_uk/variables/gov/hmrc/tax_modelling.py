from policyengine_uk.model_api import *


class tax_modelling(Variable):
    value_type = float
    entity = Person
    label = "Difference between reported and imputed tax liabilities"
    definition_period = YEAR
    unit = GBP

    adds = ["tax"]
    subtracts = ["tax_reported"]

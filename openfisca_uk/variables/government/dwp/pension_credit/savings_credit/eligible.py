from openfisca_uk.model_api import *

class savings_credit_eligible(Variable):
    label = "Eligible for Savings Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = "currency-GBP"


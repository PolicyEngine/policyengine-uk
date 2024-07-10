from policyengine_uk.model_api import *


class ISA_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount received in interest from Individual Savings Accounts"
    definition_period = YEAR
    unit = GBP

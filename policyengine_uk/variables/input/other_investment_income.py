from policyengine_uk.model_api import *


class other_investment_income(Variable):
    value_type = float
    entity = Person
    label = "other investment income"
    documentation = "Investment income from sources other than dividends, property, and net interest on UK bank accounts; may include National Savings interest products, securities interest, interest from trusts or settlements, etc."
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.per_capita.non_labour_income"

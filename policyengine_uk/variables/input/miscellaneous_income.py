from policyengine_uk.model_api import *


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "miscellaneous income"
    documentation = "Income from any other source"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.per_capita.non_labour_income"

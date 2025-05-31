from policyengine_uk.model_api import *


class private_transfer_income(Variable):
    value_type = float
    entity = Person
    label = "private transfer income"
    documentation = "Income from private transfers"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.per_capita.non_labour_income"

from policyengine_uk.model_api import *


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = "sublet income"
    documentation = "Income from subletting properties"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.per_capita.non_labour_income"

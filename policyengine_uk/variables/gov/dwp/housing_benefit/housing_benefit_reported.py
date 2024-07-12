from policyengine_uk.model_api import *


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported Housing Benefit amount"
    definition_period = YEAR
    unit = GBP

from policyengine_uk.model_api import *


class married_couples_allowance(Variable):
    value_type = float
    entity = Person
    label = "Married Couples' allowance for the year"
    definition_period = YEAR
    unit = GBP

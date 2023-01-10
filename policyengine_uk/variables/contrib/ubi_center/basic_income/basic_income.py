from policyengine_uk.model_api import *


class basic_income(Variable):
    label = "Basic income"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["bi_maximum"]
    subtracts = ["bi_phaseout"]

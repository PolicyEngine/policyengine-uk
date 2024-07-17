from policyengine_uk.model_api import *


class employment_benefits(Variable):
    value_type = float
    entity = Person
    label = "Employment benefits"
    definition_period = YEAR
    unit = GBP

    adds = ["statutory_sick_pay", "statutory_maternity_pay"]

from policyengine_uk.model_api import *


class pension_wealth(Variable):
    label = "pension wealth"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = [
        "defined_contribution_pensions",
        "defined_benefit_pensions",
    ]

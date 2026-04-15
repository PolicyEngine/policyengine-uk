from policyengine_uk.model_api import *


class adult_dependants_grant_other_adult_income(Variable):
    value_type = float
    entity = Person
    label = "Other adult dependant income for Adult Dependants' Grant"
    documentation = (
        "Income of a non-partner adult dependant for Adult Dependants' Grant purposes. "
        "This currently has to be set explicitly in simulations."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    set_input = set_input_dispatch_by_period

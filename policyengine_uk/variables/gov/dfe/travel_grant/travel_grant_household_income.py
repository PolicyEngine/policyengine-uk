from policyengine_uk.model_api import *


class travel_grant_household_income(Variable):
    value_type = float
    entity = Person
    label = "Travel Grant household income"
    documentation = (
        "Household income used for Travel Grant assessment. This can be set explicitly in simulations. "
        "By default, the model uses the maintenance-loan assessed household-income proxy."
    )
    definition_period = YEAR
    unit = GBP
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_household_income", period)

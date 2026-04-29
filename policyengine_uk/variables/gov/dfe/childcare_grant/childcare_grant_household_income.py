from policyengine_uk.model_api import *


class childcare_grant_household_income(Variable):
    value_type = float
    entity = Person
    label = "Childcare Grant household income"
    documentation = (
        "Household income used for Childcare Grant assessment. This can be set explicitly in simulations. "
        "By default it uses the maintenance loan household income proxy."
    )
    definition_period = YEAR
    unit = GBP
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_household_income", period)

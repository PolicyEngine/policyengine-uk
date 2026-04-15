from policyengine_uk.model_api import *


class travel_grant_income_assessed_support(Variable):
    value_type = bool
    entity = Person
    label = "Receives income-assessed student support for Travel Grant"
    documentation = (
        "Whether the student receives income-assessed student support for Travel Grant purposes. "
        "This can be set explicitly in simulations. By default, the model uses maintenance-loan eligibility as a proxy."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_eligible", period)

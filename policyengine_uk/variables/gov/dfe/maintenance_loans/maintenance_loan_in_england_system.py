from policyengine_uk.model_api import *


class maintenance_loan_in_england_system(Variable):
    value_type = bool
    entity = Person
    label = "In Student Finance England maintenance loan system"
    documentation = (
        "Whether the person should be treated as falling under the England maintenance-loan system. "
        "This can be set explicitly in simulations. By default, the model proxies this from current household country."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        country = person.household("country", period)
        return country == country.possible_values.ENGLAND

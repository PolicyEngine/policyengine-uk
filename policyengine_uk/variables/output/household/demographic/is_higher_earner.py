from policyengine_uk.model_api import *


class is_higher_earner(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the highest earner in a family"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)
        # Add noise to incomes in order to avoid ties
        return (
            person.get_rank(person.benunit, -income + random(person) * 1e-2)
            == 0
        )

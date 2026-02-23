from policyengine_uk.model_api import *


class is_higher_earner(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the highest earner in a family"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)
        # Use age as deterministic tie-breaker (older person wins ties)
        age = person("age", period)
        # Scale age to be tiny relative to income differences
        tie_breaker = age * 1e-6
        return person.get_rank(person.benunit, -income - tie_breaker) == 0

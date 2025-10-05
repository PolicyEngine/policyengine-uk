from policyengine_uk.model_api import *


class is_higher_earner(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the highest earner in a family"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)

        # Use random draw from dataset to break ties (only exists in microsimulation)
        # For policy calculator, this will be 0 and ties go to first person
        random_draw = person("higher_earner_tie_break", period)
        return (
            person.get_rank(person.benunit, -income + random_draw * 1e-2) == 0
        )

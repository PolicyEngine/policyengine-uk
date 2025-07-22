from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class adult_index_cg(Variable):
    value_type = int
    entity = Person
    label = "index of adult in household, ranked by capital gains"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person.get_rank(
                person.household,
                -person("capital_gains_before_response", period),
                condition=person("is_adult", period),
            )
            + 1
        )

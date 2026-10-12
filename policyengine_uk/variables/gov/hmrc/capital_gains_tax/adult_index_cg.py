from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class adult_index_cg(Variable):
    value_type = int
    entity = Person
    label = "rank by capital gains among household members aged 18 or over"
    documentation = (
        "Ranks household members aged 18 or over by capital gains, largest "
        "first, starting at 1; 0 for everyone under 18. It picks whose "
        "marginal capital gains tax rate is simulated (two branch simulations "
        "per household). A modelling choice, not law: capital gains tax has "
        "no age condition."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person.get_rank(
                person.household,
                -person("capital_gains_before_response", period),
                condition=~person("age_under_18", period),
            )
            + 1
        )

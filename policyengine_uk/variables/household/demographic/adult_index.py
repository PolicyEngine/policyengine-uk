from policyengine_uk.model_api import *
import pandas as pd


class adult_index(Variable):
    value_type = int
    entity = Person
    label = "Rank among household members aged 18 or over"
    documentation = (
        "Rank by age, eldest first and starting at 1, among household "
        "members aged 18 or over; 0 for everyone under 18. A modelling "
        "index (for example, whose marginal tax rate is simulated), not a "
        "legal definition of an adult."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person.get_rank(
                person.household,
                -person("age", period),
                condition=~person("age_under_18", period),
            )
            + 1
        )

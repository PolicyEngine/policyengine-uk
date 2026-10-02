from policyengine_uk.model_api import *
import pandas as pd


class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the head-of-household"
    documentation = (
        "Input flag for the household reference person; in the Family "
        "Resources Survey data, the HRP. Without an input, the eldest "
        "member is the head. Input can flag several members, or none. "
        "Programmes read is_resolved_household_head instead, which settles "
        "on exactly one head per household."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.get_rank(person.household, -person("age", period)) == 0

from policyengine_uk.model_api import *


class ni_liable(Variable):
    label = "NI liable"
    documentation = (
        "Whether this person is liable for NI contributions by their age."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        return person("over_16", period) & ~person("is_SP_age", period)

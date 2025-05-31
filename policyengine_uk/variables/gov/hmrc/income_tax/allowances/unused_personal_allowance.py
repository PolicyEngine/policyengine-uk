from policyengine_uk.model_api import *
from numpy import ceil


class unused_personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Unused personal allowance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            person("personal_allowance", period)
            - person("adjusted_net_income", period),
            0,
        )

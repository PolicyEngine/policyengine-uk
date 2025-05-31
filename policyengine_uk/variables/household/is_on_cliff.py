from policyengine_uk.model_api import *


class is_on_cliff(Variable):
    value_type = bool
    entity = Person
    label = "is on a tax-benefit cliff"
    documentation = "Whether this person would be worse off if their employment income were higher by delta amount."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("cliff_gap", period) > 0

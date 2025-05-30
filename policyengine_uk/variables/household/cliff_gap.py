from policyengine_uk.model_api import *


class cliff_gap(Variable):
    value_type = float
    entity = Person
    label = "cliff gap"
    unit = GBP
    documentation = "Amount of income lost if this person's employment income increased by delta amount."
    definition_period = YEAR

    def formula(person, period, parameters):
        delta = parameters(period).gov.simulation.marginal_tax_rate_delta
        mtr = person("marginal_tax_rate", period)
        return max_(0, (mtr - 1) * delta)

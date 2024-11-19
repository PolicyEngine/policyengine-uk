from policyengine_uk.model_api import *


class cliff_evaluated(Variable):
    value_type = bool
    entity = Person
    label = "cliff evaluated"
    unit = GBP
    documentation = "Whether this person's cliff has been simulated. If not, then the cliff gap is assumed to be zero."
    definition_period = YEAR

    def formula(person, period, parameters):
        adult_index_values = person("adult_index", period)
        cliff_adult_count = parameters(
            period
        ).gov.simulation.marginal_tax_rate_adults
        return adult_index_values <= cliff_adult_count


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


class is_on_cliff(Variable):
    value_type = bool
    entity = Person
    label = "is on a tax-benefit cliff"
    documentation = "Whether this person would be worse off if their employment income were higher by delta amount."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("cliff_gap", period) > 0

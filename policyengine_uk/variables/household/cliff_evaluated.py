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

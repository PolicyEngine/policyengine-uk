from policyengine_uk.model_api import *


class cliff_evaluated(Variable):
    value_type = bool
    entity = Person
    label = "cliff evaluated"
    documentation = "Whether this person's cliff has been simulated. If not, then the cliff gap is assumed to be zero."
    definition_period = YEAR

    def formula(person, period, parameters):
        adult_index_values = person("adult_index", period)
        cliff_adult_count = parameters(period).gov.simulation.marginal_tax_rate_adults
        # marginal_tax_rate perturbs adults 1 to cliff_adult_count only;
        # people under 18 have adult_index 0 and are never simulated.
        return (adult_index_values >= 1) & (adult_index_values <= cliff_adult_count)

from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_behavioural_response(Variable):
    value_type = float
    entity = Person
    label = "capital gains behavioral response"
    documentation = (
        "Change in realised gains under a reform to the taxation of gains, "
        "given the assumed elasticity of realisations with respect to the "
        "retention rate."
    )
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        simulation = person.simulation
        if simulation.baseline is None:
            return 0

        if parameters(period).gov.simulation.capital_gains_responses.elasticity == 0:
            return 0

        capital_gains = person("capital_gains_before_response", period)
        retention_rate_change = person(
            "relative_capital_gains_retention_rate_change", period
        )
        elasticity = person("capital_gains_elasticity", period)

        # Calculate response using log differences
        response_factor = np.exp(elasticity * retention_rate_change) - 1
        response = capital_gains * response_factor

        return response

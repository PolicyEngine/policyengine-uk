from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.capital_gains import (
    badr_gains_before_response,
    realisation_factors,
)


class capital_gains_behavioural_response(Variable):
    value_type = float
    entity = Person
    label = "capital gains behavioral response"
    documentation = (
        "Change in realised gains under a reform to the taxation of gains, "
        "given an elasticity of realisations with respect to either the "
        "retention rate or the marginal tax rate. Gains qualifying for "
        "Business Asset Disposal Relief respond at their own elasticity "
        "(capital_gains_badr_behavioural_response); the rest at the main one."
    )
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        factors = realisation_factors(person, period, parameters)
        if factors is None:
            return 0
        main_factor, _ = factors

        capital_gains = person("capital_gains_before_response", period)
        other_gains = capital_gains - badr_gains_before_response(person, period)
        return other_gains * (main_factor - 1) + person(
            "capital_gains_badr_behavioural_response", period
        )

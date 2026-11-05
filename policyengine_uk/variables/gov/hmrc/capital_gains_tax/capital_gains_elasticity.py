from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.capital_gains import capital_gains_response_assumption


class capital_gains_elasticity(Variable):
    value_type = float
    entity = Person
    label = "elasticity of capital gains realizations"
    documentation = (
        "Elasticity of realisations with respect to the capital gains "
        "retention rate, for gains other than those qualifying for Business "
        "Asset Disposal Relief (see capital_gains_badr_elasticity): "
        "gov.simulation.capital_gains_responses.elasticity, or 0 in a period "
        "where an MTR elasticity applies alone."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        return capital_gains_response_assumption(person.simulation, period).elasticity

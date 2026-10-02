from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_elasticity(Variable):
    value_type = float
    entity = Person
    label = "elasticity of capital gains realizations"
    documentation = (
        "Elasticity of realisations with respect to the capital gains "
        "retention rate, for gains other than those qualifying for Business "
        "Asset Disposal Relief (see capital_gains_badr_elasticity)."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        gov = parameters(period).gov
        return gov.simulation.capital_gains_responses.elasticity

from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_badr_elasticity(Variable):
    value_type = float
    entity = Person
    label = "elasticity of realisations of gains qualifying for Business Asset Disposal Relief"
    documentation = (
        "Elasticity of realisations with respect to the capital gains "
        "retention rate, for gains qualifying for Business Asset Disposal "
        "Relief: gov.simulation.capital_gains_responses.badr_elasticity while "
        "separate_badr_elasticity is on, otherwise the main elasticity."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.simulation.capital_gains_responses
        return where(
            p.separate_badr_elasticity,
            p.badr_elasticity,
            person("capital_gains_elasticity", period),
        )

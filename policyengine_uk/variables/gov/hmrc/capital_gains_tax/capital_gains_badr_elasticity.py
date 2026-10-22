from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.capital_gains import capital_gains_response_assumption


class capital_gains_badr_elasticity(Variable):
    value_type = float
    entity = Person
    label = "elasticity of realisations of gains qualifying for Business Asset Disposal Relief"
    documentation = (
        "Elasticity of realisations with respect to the capital gains "
        "retention rate, for gains qualifying for Business Asset Disposal "
        "Relief: gov.simulation.capital_gains_responses.badr_elasticity while "
        "separate_badr_elasticity is on, otherwise the main elasticity; 0 in "
        "a period where an MTR elasticity applies alone."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        assumption = capital_gains_response_assumption(person.simulation, period)
        return where(
            assumption.separate_badr_elasticity,
            assumption.badr_elasticity,
            person("capital_gains_elasticity", period),
        )

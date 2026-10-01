from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_elasticity(Variable):
    value_type = float
    entity = Person
    label = "elasticity of capital gains realizations"
    documentation = (
        "Elasticity of the person's realisations with respect to the capital "
        "gains retention rate, applied to all of their gains. People with gains "
        "qualifying for Business Asset Disposal Relief take "
        "gov.simulation.capital_gains_responses.badr_elasticity while "
        "separate_badr_elasticity is on, whatever share of their gains "
        "qualifies; everyone else takes elasticity."
    )
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.simulation.capital_gains_responses
        badr_elasticity = where(
            p.separate_badr_elasticity, p.badr_elasticity, p.elasticity
        )
        has_badr_gains = person("capital_gains_badr", period) > 0
        return where(has_badr_gains, badr_elasticity, p.elasticity)

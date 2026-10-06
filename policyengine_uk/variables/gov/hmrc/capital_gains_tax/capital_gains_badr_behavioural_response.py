from policyengine_uk.model_api import *
from policyengine_core.simulations import *
from policyengine_uk.utils.capital_gains import (
    badr_gains_before_response,
    realisation_factors,
)


class capital_gains_badr_behavioural_response(Variable):
    value_type = float
    entity = Person
    label = (
        "behavioural response of gains qualifying for Business Asset Disposal Relief"
    )
    documentation = (
        "The part of capital_gains_behavioural_response on gains qualifying "
        "for Business Asset Disposal Relief (capital_gains_badr, up to the "
        "person's total gains), which respond at "
        "capital_gains_badr_elasticity. capital_gains_tax moves these gains by "
        "this response and the person's other gains by the rest."
    )
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        factors = realisation_factors(person, period, parameters)
        if factors is None:
            return 0
        _, badr_factor = factors
        return badr_gains_before_response(person, period) * (badr_factor - 1)

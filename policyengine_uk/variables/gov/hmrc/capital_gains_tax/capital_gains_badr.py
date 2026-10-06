from policyengine_uk.model_api import *


class capital_gains_badr(Variable):
    label = "capital gains qualifying for Business Asset Disposal Relief"
    documentation = (
        "Gains qualifying for Business Asset Disposal Relief or Investors' "
        "Relief. A component of capital_gains, measured before any behavioural "
        "response, not an addition to it: a value entered without a matching "
        "capital_gains total is ignored. capital_gains_tax charges these gains "
        "at the relief rate up to the lifetime limit, applied to the year's gains "
        "as if none of the limit had been used before, and charges the excess at "
        "the main rates."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    reference = "Taxation of Chargeable Gains Act 1992 Part 5 Ch. 3, s. 169N"
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

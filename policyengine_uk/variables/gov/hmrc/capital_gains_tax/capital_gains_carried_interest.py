from policyengine_uk.model_api import *


class capital_gains_carried_interest(Variable):
    label = "capital gains from carried interest"
    documentation = (
        "Carried interest gains chargeable to capital gains tax. A component of "
        "capital_gains, measured before any behavioural response, not an "
        "addition to it: a value entered without a matching capital_gains total "
        "is ignored. capital_gains_tax charges these gains at the carried "
        "interest rates, a flat 32% from 6 April 2025."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    reference = "Taxation of Chargeable Gains Act 1992 ss. 1H, 103KA"
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

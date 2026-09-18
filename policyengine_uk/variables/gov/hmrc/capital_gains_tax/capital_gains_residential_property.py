from policyengine_uk.model_api import *


class capital_gains_residential_property(Variable):
    label = "capital gains on residential property"
    documentation = (
        "Net gains on disposals of UK residential property. A component of "
        "capital_gains, measured before any behavioural response, not an "
        "addition to it: a value entered without a matching capital_gains total "
        "is ignored. capital_gains_tax charges these gains at the residential "
        "property rates."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    reference = "Taxation of Chargeable Gains Act 1992 ss. 1H-1I"
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

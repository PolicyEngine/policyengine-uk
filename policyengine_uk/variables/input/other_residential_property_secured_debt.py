from policyengine_uk.model_api import *


class other_residential_property_secured_debt(Variable):
    label = "debt secured on other residential property"
    documentation = (
        "Amount owed on mortgages and other charges secured on residential "
        "property the household owns other than the main residence, such as a "
        "buy-to-let mortgage. Means tests deduct it from that property's value "
        "(UC Regs 2013 reg. 49(1)(b) and its legacy equivalents)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

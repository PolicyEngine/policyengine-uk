from policyengine_uk.model_api import *


class non_residential_property_secured_debt(Variable):
    label = "debt secured on non-residential property"
    documentation = (
        "Amount owed on mortgages and other charges secured on non-residential "
        "property the household owns. Means tests deduct it from that "
        "property's value after the 10% for sale expenses, flooring the "
        "property at nil (UC Regs 2013 reg. 49(1)(b) and its legacy "
        "equivalents). The value and the debt are household totals across all "
        "such properties, so debt on one property offsets equity in another."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

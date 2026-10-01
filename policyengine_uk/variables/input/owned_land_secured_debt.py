from policyengine_uk.model_api import *


class owned_land_secured_debt(Variable):
    label = "debt secured on owned land"
    documentation = (
        "Amount owed on mortgages and other charges secured on land-only plots "
        "the household owns. Means tests deduct it from that land's value after "
        "the 10% for sale expenses, flooring the land at nil (UC Regs 2013 reg. "
        "49(1)(b) and its legacy equivalents). The value and the debt are "
        "household totals across all plots, so debt on one plot offsets equity "
        "in another."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

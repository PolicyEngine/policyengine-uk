from policyengine_uk.model_api import *


class would_receive_warm_home_discount(Variable):
    label = "Would receive the Warm Home Discount if eligible"
    documentation = (
        "Whether a household receiving a qualifying benefit would receive the "
        "Warm Home Discount rebate. The rebate is paid without a claim after "
        "DWP data is matched with supplier records, but not every recipient "
        "is matched or named on the electricity bill. Households where any "
        "benefit unit receives Pension Credit use the Pension Credit receipt "
        "rate; other households use the rate for other qualifying benefits."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        p = parameters(period).gov.ofgem.warm_home_discount.receipt_rate
        receives_pension_credit = add(household, period, ["pension_credit"]) > 0
        rate = where(receives_pension_credit, p.pension_credit, p.other_benefits)
        draw = household("warm_home_discount_random_draw", period)
        return draw < rate

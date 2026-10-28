from policyengine_uk.model_api import *


class winter_fuel_allowance(Variable):
    label = "Winter Fuel Allowance"
    documentation = (
        "Winter Fuel Payments made to the members of this household "
        "(winter_fuel_payment). Payments in Scotland from the 2024 "
        "qualifying week are the Pension Age Winter Heating Payment (pawhp). "
        "The payments are counted in full: from 2025-26 the winter fuel "
        "payment charge recovers them from some members through income tax "
        "(winter_fuel_payment_charge)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["winter_fuel_payment"]

from policyengine_uk.model_api import *


class pawhp(Variable):
    label = "Pension Age Winter Heating Payment"
    documentation = (
        "Pension Age Winter Heating Payments made to the members of this "
        "household (pension_age_winter_heating_payment). The payments are "
        "counted in full: from 2025-26 the winter fuel payment charge "
        "recovers them from some members through income tax "
        "(winter_fuel_payment_charge)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["pension_age_winter_heating_payment"]

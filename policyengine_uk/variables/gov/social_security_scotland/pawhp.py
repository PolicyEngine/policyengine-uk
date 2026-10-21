from policyengine_uk.model_api import *


class pawhp(Variable):
    label = "Pension Age Winter Heating Payment"
    documentation = (
        "Pension Age Winter Heating Payments made to the members of this "
        "household (pension_age_winter_heating_payment)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["pension_age_winter_heating_payment"]

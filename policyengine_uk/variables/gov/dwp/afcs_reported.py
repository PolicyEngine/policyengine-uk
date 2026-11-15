from policyengine_uk.model_api import *


class afcs_reported(Variable):
    value_type = float
    entity = Person
    label = "Armed Forces Compensation Scheme (reported)"
    documentation = (
        "Reported Armed Forces Compensation Scheme and war disablement pension "
        "payments. In the Family Resources Survey this is benefit code 8, asked "
        "as the Armed Forces Compensation Scheme (formerly War Disablement "
        "Pension), including Guaranteed Income Payments. Armed forces "
        "independence payment is the separate armed_forces_independence_payment "
        "variable."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

from policyengine_uk.model_api import *


class structural_insurance_payments(Variable):
    label = "structural insurance payments"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

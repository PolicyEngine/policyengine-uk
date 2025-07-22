from policyengine_uk.model_api import *


class external_child_payments(Variable):
    label = "external child payments"
    documentation = "Payments to children living away from home."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

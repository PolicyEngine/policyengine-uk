from policyengine_uk.model_api import *


class mortgage_interest(Variable):
    label = "mortgage interest repayments"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

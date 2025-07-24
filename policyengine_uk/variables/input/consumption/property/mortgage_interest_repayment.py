from policyengine_uk.model_api import *


class mortgage_interest_repayment(Variable):
    value_type = float
    entity = Household
    label = "mortgage interest repayments"
    documentation = "Total amount spent on mortgage interest repayments"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.mortgage_interest"

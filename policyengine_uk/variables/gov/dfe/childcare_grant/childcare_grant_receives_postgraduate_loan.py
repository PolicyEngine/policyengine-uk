from policyengine_uk.model_api import *


class childcare_grant_receives_postgraduate_loan(Variable):
    value_type = bool
    entity = Person
    label = "Receives Postgraduate Loan for Childcare Grant purposes"
    documentation = "Whether the person is receiving a Postgraduate Loan, which makes them ineligible for Childcare Grant."
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

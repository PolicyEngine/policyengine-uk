from policyengine_uk.model_api import *


class adult_dependants_grant_receives_postgraduate_loan(Variable):
    value_type = bool
    entity = Person
    label = "Receives Postgraduate Loan for Adult Dependants' Grant purposes"
    documentation = "Whether the person is receiving a Postgraduate Loan, which makes them ineligible for Adult Dependants' Grant."
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

from policyengine_uk.model_api import *


class hours_providing_care(Variable):
    label = "hours providing care"
    documentation = "Hours spent per week providing care to person in receipt of disability benefits who cannot look after themselves."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


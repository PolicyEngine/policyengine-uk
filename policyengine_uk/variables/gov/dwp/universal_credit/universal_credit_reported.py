from policyengine_uk.model_api import *


class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit (reported)"
    documentation = "Reported amount of Universal Credit"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.benefit_uprating_cpi"

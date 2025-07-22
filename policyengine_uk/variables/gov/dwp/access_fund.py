from policyengine_uk.model_api import *


class access_fund(Variable):
    label = "Access Fund"
    documentation = "Access Fund for educational assistance"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

from policyengine_uk.model_api import *


class gift_aid(Variable):
    value_type = float
    entity = Person
    label = "Expenditure under Gift Aid"
    definition_period = YEAR
    unit = GBP

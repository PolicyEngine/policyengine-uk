from policyengine_uk.model_api import *


class trading_loss(Variable):
    value_type = float
    entity = Person
    label = "Loss from trading in the current year."
    definition_period = YEAR
    unit = GBP

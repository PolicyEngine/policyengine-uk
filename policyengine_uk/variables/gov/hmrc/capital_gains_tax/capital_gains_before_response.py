from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class capital_gains_before_response(Variable):
    label = "capital gains before responses"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.obr.non_labour_income"

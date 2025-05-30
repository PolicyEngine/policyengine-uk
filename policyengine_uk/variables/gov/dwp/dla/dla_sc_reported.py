from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (

class dla_sc_reported(Variable):
    value_type = float
    entity = Person
    label = "DLA (self-care) (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"

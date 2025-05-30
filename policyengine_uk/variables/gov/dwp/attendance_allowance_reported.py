from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_or_higher import (

class attendance_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Attendance Allowance (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"

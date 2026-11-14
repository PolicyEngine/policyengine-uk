from policyengine_uk.model_api import *


class electricity_consumption_kwh(Variable):
    label = "Monthly domestic electricity use in kWh"
    documentation = (
        "Eligible domestic electricity used in the calendar month. The default "
        "of -1 represents unknown use; an explicitly supplied zero represents "
        "no use. Current microsimulation data do not populate this input."
    )
    entity = Household
    definition_period = MONTH
    value_type = float
    default_value = -1
    unit = "kWh"

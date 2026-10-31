from policyengine_uk.model_api import *


class gas_consumption_kwh(Variable):
    label = "Monthly domestic mains-gas use in kWh"
    documentation = (
        "Eligible domestic mains gas used in the calendar month, excluding "
        "heating oil, LPG and road fuel. The default of -1 represents unknown "
        "use; an explicitly supplied zero represents no use. Current "
        "microsimulation data do not populate this input."
    )
    entity = Household
    definition_period = MONTH
    value_type = float
    default_value = -1
    unit = "kWh"

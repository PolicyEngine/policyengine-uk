from policyengine_uk.model_api import *


class in_rural_fuel_duty_relief_area(Variable):
    label = "In Rural Fuel Duty Relief scheme area"
    documentation = (
        "Whether the household is located in a postcode eligible for the Rural "
        "Fuel Duty Relief Scheme, which provides a flat per-litre reduction on "
        "petrol and diesel purchased from registered retailers."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    default_value = False
    reference = "https://www.gov.uk/guidance/rural-duty-relief-scheme-notice-2001"

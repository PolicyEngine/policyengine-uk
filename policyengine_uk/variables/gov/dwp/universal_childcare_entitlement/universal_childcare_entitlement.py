from policyengine_uk.model_api import *


class universal_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    label = "Universal childcare entitlement amount per year"
    documentation = "Annual amount of universal childcare entitlement funding calculated by multiplying hours by hourly rate"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        # Get the hours entitled for this child
        hours = person("universal_childcare_entitlement_hours", period)

        # Get the funding rate from parameters
        p = parameters(period).gov.dwp.universal_childcare_entitlement

        # Calculate total funding amount (hours * rate)
        return hours * p.fund_rate

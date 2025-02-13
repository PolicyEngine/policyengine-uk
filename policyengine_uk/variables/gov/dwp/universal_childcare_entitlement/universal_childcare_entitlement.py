from policyengine_uk.model_api import *


class universal_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    label = "universal childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        # Get the hours entitled for this child
        hours = person("universal_childcare_entitlement_hours", period)

        # Get the funding rate from parameters
        p = parameters(period).gov.dwp.universal_childcare_entitlement
        rate = p.funding_rate

        # Calculate total funding amount
        total_entitlement = hours * rate
        return total_entitlement

from policyengine_uk.model_api import *


class targeted_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    label = "targeted childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        # Get the hours entitled for this child
        hours = person("targeted_childcare_entitlement_hours", period)

        # Get the funding rate from parameters
        p = parameters(period).gov.dwp.targeted_childcare_entitlement
        return hours * p.funding_rate

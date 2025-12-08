from policyengine_uk.model_api import *


class plan_5_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 5 student loan interest rate"
    documentation = (
        "Interest rate for Plan 5 student loans (from September 2023). "
        "Set at RPI only - no additional percentage based on income."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/2023/207/made"

    def formula(person, period, parameters):
        p = parameters(period).gov
        return p.economic_assumptions.yoy_growth.obr.rpi

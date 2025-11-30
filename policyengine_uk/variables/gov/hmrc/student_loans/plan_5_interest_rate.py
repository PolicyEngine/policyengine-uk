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

    def formula(person, period, parameters):
        return parameters(period).gov.hmrc.student_loans.interest_rates.rpi

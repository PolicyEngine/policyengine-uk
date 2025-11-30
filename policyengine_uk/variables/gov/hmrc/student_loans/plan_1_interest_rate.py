from policyengine_uk.model_api import *


class plan_1_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 1 student loan interest rate"
    documentation = (
        "Interest rate for Plan 1 student loans (pre-2012 England/Wales). "
        "Set at the lower of RPI or Bank of England base rate + 1%."
    )
    definition_period = YEAR
    unit = "/1"

    def formula(person, period, parameters):
        rpi = parameters(period).gov.hmrc.student_loans.interest_rates.rpi
        boe_rate = parameters(period).gov.boe.base_rate
        return min_(rpi, boe_rate + 0.01)

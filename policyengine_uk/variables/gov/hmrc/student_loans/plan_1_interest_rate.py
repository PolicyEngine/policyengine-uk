from policyengine_uk.model_api import *


class plan_1_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 1 student loan interest rate"
    documentation = (
        "Interest rate for Plan 1 student loans (pre-2012 England/Wales). "
        "Set at the lower of RPI or Bank of England base rate + 1%. "
        "Note: Actual rates are set annually in September using March RPI."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/2009/470/regulation/21"

    def formula(person, period, parameters):
        p = parameters(period).gov
        return min_(
            p.economic_assumptions.yoy_growth.obr.rpi,
            p.boe.base_rate
            + p.hmrc.student_loans.interest_rates.plan_1.boe_margin,
        )

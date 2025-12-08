from policyengine_uk.model_api import *
import numpy as np


class plan_2_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 2 student loan interest rate"
    documentation = (
        "Income-contingent interest rate for Plan 2 student loans. "
        "RPI only below lower threshold, tapered to RPI+3% at upper threshold. "
        "Note: Actual rates are set annually in September using March RPI."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/2012/1309/regulation/10"

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)
        p = parameters(period).gov.hmrc.student_loans
        rpi = parameters(period).gov.economic_assumptions.yoy_growth.obr.rpi

        # Per Regulation 21AB, lower interest threshold = repayment threshold
        # Below lower: RPI only; above upper: RPI + 3%; between: linear taper
        taper_fraction = np.clip(
            (income - p.thresholds.plan_2)
            / (p.interest_rates.plan_2.upper_threshold - p.thresholds.plan_2),
            0,
            1,
        )
        return rpi + p.interest_rates.plan_2.additional_rate * taper_fraction

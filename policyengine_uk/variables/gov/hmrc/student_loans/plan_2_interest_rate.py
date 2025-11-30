from policyengine_uk.model_api import *
import numpy as np


class plan_2_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 2 student loan interest rate"
    documentation = (
        "Income-contingent interest rate for Plan 2 student loans. "
        "RPI only below lower threshold, tapered to RPI+3% at upper threshold."
    )
    definition_period = YEAR
    unit = "/1"

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)
        p = parameters(period).gov.hmrc.student_loans.interest_rates

        # Below lower threshold: RPI only
        # Above upper threshold: RPI + 3%
        # Between: linear taper
        taper_fraction = np.clip(
            (income - p.plan_2.lower_threshold)
            / (p.plan_2.upper_threshold - p.plan_2.lower_threshold),
            0,
            1,
        )
        return p.rpi + (p.plan_2.additional_rate * taper_fraction)

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
        p = parameters(period).gov.hmrc.student_loans.interest_rates.plan_2

        # Below lower threshold: base rate only (RPI)
        # Above upper threshold: base + full additional (RPI + 3%)
        # Between: linear taper
        taper_fraction = np.clip(
            (income - p.lower_threshold)
            / (p.upper_threshold - p.lower_threshold),
            0,
            1,
        )
        return p.base_rate + (p.additional_rate * taper_fraction)

from policyengine_uk.model_api import *


class carers_allowance_weekly_earnings_above_limit(Variable):
    value_type = float
    entity = Person
    label = "weekly earnings above the Carer's Allowance earnings limit"
    documentation = (
        "How far the person's weekly net earnings exceed the Carer's Allowance "
        "earnings limit, or zero at or below it. The regulation tests the "
        "earnings of the preceding week; annual earnings are spread evenly "
        "over 52 weeks. The model disregards a fraction of a penny, as regulation 5 "
        "of the Computation of Earnings Regulations requires when that favours "
        "the claimant. Any excess means the person is gainfully employed; "
        "where the Budget 2026 earnings taper applies, the allowance tapers "
        "away on it instead of stopping."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="The Social Security (Invalid Care Allowance) Regulations 1976 reg. 8(1)",
            href="https://www.legislation.gov.uk/uksi/1976/409/regulation/8",
        ),
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 5",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/5",
        ),
    ]

    def formula(person, period, parameters):
        limit = parameters(period).gov.dwp.carers_allowance.earnings_limit
        weekly = person("carers_allowance_earnings", period) / WEEKS_IN_YEAR
        # Disregard a fraction of a penny; the tolerance keeps an exact
        # number of pence safe from floating-point error.
        weekly_in_pence = np.floor(weekly * 100 + 1e-6) / 100
        return max_(0, weekly_in_pence - limit)

from policyengine_uk.model_api import *


class is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap because of earnings"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75E",
    ]

    def formula(benunit, period, parameters):
        # Regulation 82 of the Universal Credit Regulations 2013 excepts a
        # claimant (or couple, on their combined income) from the benefit cap
        # where their earned income reaches 16 hours a week at the National
        # Living Wage. Earned income here is employed and self-employed
        # earnings net of the income tax, National Insurance and relievable
        # pension contributions attributable to those earnings (reg. 55(5),
        # reg. 57), not net of total tax on all income
        # (benefit_cap_earned_income). Each claimant's own deductions come off
        # their own earnings only: tax on pensions, property, savings and
        # dividends is not deducted, nor are voluntary Class 3 contributions,
        # nor contributions paid after 75, which are not relievable. Income
        # treated as earned under the minimum income floor does not count
        # (reg. 82(4)).
        #
        # Reg. 82(1)(a) tests "the claimant's earned income or, if the
        # claimant is a member of a couple, the couple's combined earned
        # income": a dependant's earnings do not count.
        net_earnings = benunit("benefit_cap_earned_income", period)

        monthly_threshold = parameters(period).gov.dwp.benefit_cap_earnings_exemption
        meets_earnings_test = net_earnings >= monthly_threshold * MONTHS_IN_YEAR

        # Reg. 82(1) excepts "an award of universal credit". It does not
        # except a Housing Benefit award, whose cap has its own exception for
        # work: entitlement to Working Tax Credit (Housing Benefit Regulations
        # 2006 reg. 75E, in is_benefit_cap_exempt_health_disability). The
        # model caps both awards with one reduction, so where the benefit
        # unit has Housing Benefit and no Universal Credit award this
        # exception does not apply. Both awards are read before the cap, to
        # avoid a circular dependency with it.
        uc_award = benunit("is_uc_entitled", period)
        housing_benefit_award = benunit("housing_benefit_pre_benefit_cap", period) > 0
        return meets_earnings_test & (uc_award | ~housing_benefit_award)

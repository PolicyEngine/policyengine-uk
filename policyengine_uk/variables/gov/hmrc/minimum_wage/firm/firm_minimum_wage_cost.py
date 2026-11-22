from policyengine_uk.model_api import *


class firm_minimum_wage_cost(Variable):
    value_type = float
    entity = Firm
    label = "Firm cost of meeting the minimum wage"
    documentation = (
        "The extra pay the firm needs to bring its low-paid workers up to the "
        "adult minimum wage (the national living wage): the hourly rate times "
        "firm_low_paid_hours, less firm_low_paid_paybill, floored at zero. "
        "It is a cost to the firm, not a tax. It raises the paybill in "
        "firm_paybill_after_minimum_wage, through which the apprenticeship "
        "levy and the default employer National Insurance and auto-enrolment "
        "approximations rise. The rate is the top age band of "
        "gov.hmrc.minimum_wage.non_apprentice read at 30 April, the rate for "
        "the fiscal year that starts that April. The block is treated as "
        "paid its average hourly wage, so the cost is understated where pay "
        "within it varies: hours paid above the rate offset hours paid "
        "below it. Negative inputs count as 0. The rates in the model start "
        "in October 2010, so the cost is 0 for 2010 and earlier. The "
        "younger-worker and apprentice rates are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="National Minimum Wage Act 1998 s.1",
            href="https://www.legislation.gov.uk/ukpga/1998/39/section/1",
        ),
        dict(
            title="National Minimum Wage Regulations 2015 reg. 4",
            href="https://www.legislation.gov.uk/uksi/2015/621/regulation/4",
        ),
    ]

    def formula(firm, period, parameters):
        # The compiled scale orders brackets by age, so its last amount is
        # the adult rate, as in esa_exempt_work_higher_earnings_limit.
        # The rates start in October 2010, so at 30 April of 2010 and
        # earlier the scale is empty and the floor does not apply.
        amounts = parameters(period).gov.hmrc.minimum_wage.non_apprentice.amounts
        adult_rate = amounts[-1] if len(amounts) else 0
        hours = max_(firm("firm_low_paid_hours", period), 0)
        paybill = max_(firm("firm_low_paid_paybill", period), 0)
        return max_(adult_rate * hours - paybill, 0)

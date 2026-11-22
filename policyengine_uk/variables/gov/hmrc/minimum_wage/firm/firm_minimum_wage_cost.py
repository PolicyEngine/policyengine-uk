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
        "below it. The younger-worker and apprentice rates are not modelled."
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
        adult_rate = parameters(period).gov.hmrc.minimum_wage.non_apprentice.amounts[-1]
        hours = firm("firm_low_paid_hours", period)
        paybill = firm("firm_low_paid_paybill", period)
        return max_(adult_rate * hours - paybill, 0)

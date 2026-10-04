from policyengine_uk.model_api import *


class benefit_cap_earnings_threshold(Variable):
    value_type = float
    entity = BenUnit
    label = "Benefit cap earnings exception threshold"
    documentation = (
        "The earned income, over a year, at or above which a Universal Credit "
        "award is excepted from the benefit cap: twelve times the monthly "
        "amount in the regulations. Since 1 April 2017 the monthly amount is "
        "16 hours a week at the national living wage rate, times 52 and "
        "divided by 12, with any fraction of a pound disregarded. Before "
        "then it was 430 a month."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 82(1)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 6(1A)(za)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/6",
        ),
        dict(
            title="National Minimum Wage Regulations 2015 reg. 4",
            href="https://www.legislation.gov.uk/uksi/2015/621/regulation/4",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov
        exception = p.dwp.universal_credit.benefit_cap.earnings_exception
        # Reg. 82(1)(a) uses "the hourly rate set out in regulation 4 of the
        # National Minimum Wage Regulations": the single national living wage
        # rate, whatever the claimant's age. It is the top age band of the
        # model's schedule.
        hourly_rate = p.hmrc.minimum_wage.non_apprentice.amounts[-1]
        monthly_pay = (
            hourly_rate * exception.weekly_hours * WEEKS_IN_YEAR / MONTHS_IN_YEAR
        )
        # Reg. 6(1A)(za) disregards a fraction of a pound in the amount
        # calculated for reg. 82(1)(a): 12.21 x 16 x 52 / 12 = 846.56 is 846.
        monthly_amount = exception.monthly_amount + np.floor(monthly_pay)
        # Each monthly assessment period is tested against the monthly
        # amount; over a year of level earnings that is twelve times it.
        return np.ones(benunit.count) * monthly_amount * MONTHS_IN_YEAR

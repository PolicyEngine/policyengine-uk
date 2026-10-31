from policyengine_uk.model_api import *


class uc_benefit_cap_earnings_exception_threshold(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit benefit cap earnings exception threshold"
    documentation = (
        "The earned income over the year at or above which the Universal "
        "Credit benefit cap does not apply (UC Regs 2013 reg. 82(1)(a)): "
        "twelve times the monthly threshold. From 1 April 2017 the monthly "
        "threshold is the pay for 16 hours a week at the national living "
        "wage, the hourly rate in regulation 4 of the National Minimum Wage "
        "Regulations, multiplied by 52 and divided by 12, with any fraction "
        "of a pound disregarded (reg. 6(1A)(za)). Before then it was a fixed "
        "£430 a month. In years after the last rate set, the threshold "
        "follows gov.hmrc.minimum_wage.non_apprentice's projection (the "
        "OBR's national living wage forecast), as the minimum income floor "
        "does."
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
            title="Universal Credit (Benefit Cap Earnings Exception) Amendment Regulations 2017",
            href="https://www.legislation.gov.uk/uksi/2017/138/made",
        ),
    ]

    def formula(benunit, period, parameters):
        exception = parameters(
            period
        ).gov.dwp.universal_credit.benefit_cap.earnings_exception
        return exception.fixed_monthly_amount * MONTHS_IN_YEAR

    def formula_2017(benunit, period, parameters):
        p = parameters(period)
        exception = p.gov.dwp.universal_credit.benefit_cap.earnings_exception
        # "The hourly rate set out in regulation 4" is the national living
        # wage, the scale's top rate, as in uc_minimum_income_floor_gross.
        national_living_wage = p.gov.hmrc.minimum_wage.non_apprentice.calc(
            np.full(benunit.count, 200.0)
        )
        monthly = np.floor(
            national_living_wage * exception.hours * WEEKS_IN_YEAR / MONTHS_IN_YEAR
        )
        return monthly * MONTHS_IN_YEAR

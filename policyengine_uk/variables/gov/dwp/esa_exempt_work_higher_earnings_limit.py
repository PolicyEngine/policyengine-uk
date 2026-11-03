from policyengine_uk.model_api import *


class esa_exempt_work_higher_earnings_limit(Variable):
    value_type = float
    entity = Person
    label = "ESA exempt work higher earnings limit"
    documentation = (
        "The weekly earnings limit of ESA permitted work (ESA Regs 2008 reg "
        "45(4)): work done for less than 16 hours a week, for which earnings "
        "in any week do not exceed this amount, is exempt work. It was a "
        "fixed amount until 10 April 2011. From 11 April 2011 (SI 2011/674 "
        "reg 16(5)) it is 16 x National Minimum Wage, rounded up to the next "
        "50p (reg 45(9A)). Reg 2(1) defines the National Minimum Wage as the "
        "rate in reg 11 of the National Minimum Wage Regulations 1999, now "
        "the national living wage, the adult rate (DMG 41190), so the "
        "limit moves with gov.hmrc.minimum_wage.non_apprentice. That "
        "parameter holds its April 2026 rate in later years, so the limit "
        "stays at £203.50 from 2026-27 until the national living wage is "
        "projected, as the Universal Credit benefit cap earnings exception "
        "does."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/2",
        "https://www.legislation.gov.uk/uksi/2011/674/regulation/16",
        "https://assets.publishing.service.gov.uk/media/689db34d1fedc616bb13399c/dmg-ch-41.pdf",
    )

    def formula(person, period, parameters):
        return parameters(period).gov.dwp.ESA.exempt_work.fixed_higher_earnings_limit

    def formula_2011_04_11(person, period, parameters):
        p = parameters(period)
        exempt_work = p.gov.dwp.ESA.exempt_work
        # Reg 2(1) specifies the adult rate in reg 11 of the 1999
        # Regulations, now the national living wage (DMG 41190). The
        # compiled scale orders brackets by age, so its last amount is
        # that adult rate, even if a reform raises a younger age band.
        national_living_wage = p.gov.hmrc.minimum_wage.non_apprentice.amounts[-1]
        limit = (
            national_living_wage * exempt_work.higher_earnings_limit_minimum_wage_hours
        )
        # Reg 45(9A): part of a pound under 50p rounds up to 50p, and over
        # 50p up to the next pound. Rounding to six places first keeps an
        # exact amount such as 16 x £6.50 = £104 from rounding up.
        return np.ceil(np.round(limit * 2, 6)) / 2

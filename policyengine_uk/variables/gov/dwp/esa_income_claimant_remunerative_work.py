from policyengine_uk.model_api import *


class esa_income_claimant_remunerative_work(Variable):
    value_type = bool
    entity = Person
    label = "Engaged in remunerative work as an income-related ESA claimant"
    documentation = (
        "Whether the person, as the claimant of income-related ESA, is "
        "engaged in remunerative work (Welfare Reform Act 2007 Sch 1 para "
        "6(1)(e)). For a claimant that is any work done for payment or in "
        "expectation of payment, whatever the hours, other than the work reg "
        "40(2) lists (ESA Regs 2008 reg 41(1)). The model applies the exempt "
        "work in reg 40(2)(f) that its inputs can identify: work with "
        "earnings of no more than the lower limit in any week, whatever the "
        "hours (reg 45(2)), and work of less than 16 hours a week with "
        "earnings of no more than the higher limit (reg 45(4)). Before 3 "
        "April 2017, reg 45(4) also limited such work to a 52-week period "
        "unless the claimant had limited capability for work-related "
        "activity; that limit is not modelled. The other reg 40(2) work is "
        "not identified: a councillor's work, tribunal duties, domestic tasks "
        "at home or caring for a relative, placement care, emergency duties, "
        "and the other exempt work (supervised work within the higher limit "
        "whatever the hours, test trading, voluntary work and work "
        "placements, reg 45(3), (5) to (7)). Nor are the reg 41(2) periods "
        "after work ends for which final earnings are taken into account. "
        "Enter this variable directly for those cases. Unlike Income Support "
        "and the partner's test, being a carer does not take a claimant out "
        "of remunerative work."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2007/5/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/40",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/41",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
    )

    def formula(person, period, parameters):
        exempt_work = parameters(period).gov.dwp.ESA.exempt_work
        earnings = person("esa_exempt_work_earnings", period)
        hours = person("esa_income_remunerative_work_hours", period)
        # Reg 45(2): earnings of no more than the lower limit (with no
        # earnings, any hours are unpaid or within it).
        within_lower_limit = earnings <= exempt_work.lower_earnings_limit
        # Reg 45(4): permitted work.
        permitted_work = (hours < exempt_work.hours_limit) & (
            earnings <= exempt_work.higher_earnings_limit
        )
        return ~(within_lower_limit | permitted_work)

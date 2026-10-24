from policyengine_uk.model_api import *


class widowed_parents_allowance(Variable):
    value_type = float
    entity = Person
    label = "Widowed Parent's Allowance"
    documentation = (
        "Widowed Parent's Allowance under SSCBA 1992 s.39A, paid to a "
        "surviving spouse or civil partner with a dependent child whose "
        "partner died before 6 April 2017. Unlike Bereavement Support "
        "Payment, it is taxable (ITEPA 2003 s.577; any increase for a child, "
        "exempt under s.645, is not separated), it is Universal Credit "
        "unearned income (UC Regs 2013 reg. 66(1)(b)(vi)), it counts towards "
        "the benefit cap (Welfare Reform Act 2012 s.96(10)(n)) and it "
        "overlaps with Carer's Allowance and Carer Support Payment. Housing "
        "Benefit counts it less £15 a week. It is not payable from State "
        "Pension age or while the recipient lives with a partner (s.39A(4) "
        "and (5)), so a lawful award never reaches a Pension Credit or "
        "pension-age Housing Benefit assessment. A reported one counts in "
        "full for Pension Credit (SPC Regs 2002 reg. 15(1)) and less £15 a "
        "week for pension-age Housing Benefit (HB (SPC) Regs 2006 Sch. 5 "
        "para. 7)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/39A",
        "https://www.legislation.gov.uk/ukpga/2003/1/section/577",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/96",
    )

    adds = ["widowed_parents_allowance_reported"]

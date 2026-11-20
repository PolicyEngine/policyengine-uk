from policyengine_uk.model_api import *


class esa_income_remunerative_work_hours(Variable):
    value_type = float
    entity = Person
    label = "Weekly hours of paid work for the income-related ESA work tests"
    documentation = (
        "Hours a week of work for which payment is made or which is done in "
        "expectation of payment, averaged where they fluctuate. For a "
        "claimant they decide whether work is permitted work (ESA Regs 2008 "
        "reg 45(4), less than 16 hours); for a partner, whether the partner "
        "is engaged in remunerative work (reg 42(1), 24 hours or more). Reg "
        "45(8) and (9), which reg 42(2) applies to a partner, take the hours "
        "expected in a week or, where they fluctuate, the average over a "
        "complete recognisable cycle or the five weeks before the claim (or "
        "another period that gives a more accurate average), and count paid "
        "meal breaks. The model takes them to be weekly_hours, a usual week's "
        "hours in paid jobs (the Enhanced FRS records usual weekly hours "
        "across current jobs); for such work enter this variable directly. "
        "A partner's hours in the employments reg 43(1) lists do not count "
        "(reg 42(6)): child minding at home, charitable or voluntary work "
        "paid only expenses, a training allowance scheme, the self-employment "
        "route, part-time firefighting, coastguard, lifeboat and reserve "
        "forces duties, a councillor's work, foster and other placement care, "
        "and sports award activity; nor does a day of maternity, paternity, "
        "shared parental, parental bereavement, adoption or neonatal care "
        "leave or illness (reg 43(3)). The model's inputs do not identify "
        "those employments or days, so enter the hours directly to apply "
        "them. Reg 43(2)(c), which takes a carer partner out of remunerative "
        "work, is applied in esa_income_eligible."
    )
    definition_period = YEAR
    unit = "hour"
    reference = (
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/42",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/43",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
    )

    def formula(person, period, parameters):
        return person("weekly_hours", period)

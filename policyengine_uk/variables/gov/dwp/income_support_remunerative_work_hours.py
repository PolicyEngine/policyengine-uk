from policyengine_uk.model_api import *


class income_support_remunerative_work_hours(Variable):
    value_type = float
    entity = Person
    label = "Weekly hours of paid work for the Income Support remunerative work test"
    documentation = (
        "Hours a week of work for which payment is made or which is done in "
        "expectation of payment, averaged where they fluctuate (IS Regs 1987 "
        "reg 5(1) and (2)). The model takes them to be weekly_hours, a usual "
        "week's hours in paid jobs (the Enhanced FRS records usual weekly "
        "hours across current jobs). Reg 5(2) instead takes the hours "
        "expected in a week or, where they fluctuate, the average over a "
        "complete recognisable cycle or the five weeks before the claim or a "
        "superseding decision (or another period that gives a more accurate "
        "average). A school-year cycle leaves out school holidays and other "
        "periods the person is not required to work (reg 5(3B)), and paid "
        "meal and refreshment time counts (reg 5(7)). For such work enter "
        "this variable directly. Hours in the employments reg 6(1) lists do not count "
        "(reg 5(6)): child minding at home, charitable or voluntary work, a "
        "training allowance scheme, the self-employment route, retained "
        "firefighting and the other duties in Sch 8 para 7(1), a councillor's "
        "duties, foster and other placement care, and sports award activity. "
        "The model's inputs do not identify those employments either, nor "
        "days of leave or illness (reg 5(3A)); enter the hours directly to "
        "apply them. Reg 6(4)(c), which takes a carer out of remunerative "
        "work, is applied in income_support_eligible."
    )
    definition_period = YEAR
    unit = "hour"
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/5",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/6",
    )

    def formula(person, period, parameters):
        return person("weekly_hours", period)

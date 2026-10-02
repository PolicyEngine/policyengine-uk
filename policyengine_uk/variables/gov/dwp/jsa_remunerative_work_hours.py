from policyengine_uk.model_api import *


class jsa_remunerative_work_hours(Variable):
    value_type = float
    entity = Person
    label = "Weekly hours of paid work for the JSA remunerative work test"
    documentation = (
        "Hours a week of work for which payment is made or which is done in "
        "expectation of payment, averaged where they fluctuate (JSA Regs "
        "1996 reg 51(1) and (2)). The model takes them to be weekly_hours, a "
        "usual week's hours in paid jobs (the Enhanced FRS records usual "
        "weekly hours across current jobs). Reg 51(2) instead takes the "
        "hours expected in a week or, where they fluctuate, the average over "
        "a complete recognisable cycle or the five weeks before the claim "
        "(or another period that gives a more accurate average), and reg "
        "51(3)(a) counts paid meal breaks; for such work enter this variable "
        "directly. Hours in the employments and schemes reg 53(a) to (h) "
        "lists do not count (reg 51(3)(b)): charitable or voluntary work "
        "paid only expenses, a training allowance scheme, the self-employment "
        "route, employment while living in a care home and needing personal "
        "care, part-time firefighting, coastguard, lifeboat and reserve "
        "forces duties, a councillor's duties, foster and other placement "
        "care, a partner's trade dispute, and work in which a disability "
        "cuts earnings or hours to 75 per cent or less of a comparable "
        "worker's. Reg 53 also takes sports award activity and the Work "
        "Experience and other employment schemes out of remunerative work, "
        "and reg 52(1) keeps a person absent without good reason or on "
        "holiday in it. The model's inputs identify none of these, so enter "
        "the hours directly to apply them. Hours of unpaid caring "
        "(reg 51(3)(c)) are not paid work and are not in weekly_hours."
    )
    definition_period = YEAR
    unit = "hour"
    reference = (
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/51",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/52",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/53",
    )

    def formula(person, period, parameters):
        return person("weekly_hours", period)

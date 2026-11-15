from policyengine_uk.model_api import *


class receives_severe_disability_addition_qualifying_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Receives a benefit qualifying for the Pension Credit severe disability addition"
    documentation = (
        "Receives Attendance Allowance, the care component of Disability "
        "Living Allowance at the middle or highest rate, the daily living "
        "component of Personal Independence Payment, or Armed Forces "
        "Independence Payment. The same list qualifies a claimant or partner "
        "and makes another resident's presence ignored. The Scottish "
        "equivalents (Pension Age Disability Payment, Adult Disability "
        "Payment, Scottish Adult DLA) are not modelled separately."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit
        return add(person, period, p.severe_disability.relevant_benefits) > 0

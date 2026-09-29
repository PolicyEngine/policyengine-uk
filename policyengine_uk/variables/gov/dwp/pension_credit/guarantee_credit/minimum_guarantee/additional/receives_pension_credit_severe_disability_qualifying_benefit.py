from policyengine_uk.model_api import *


class receives_pension_credit_severe_disability_qualifying_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Receives a benefit qualifying for the Pension Credit severe disability addition"
    documentation = (
        "Whether this person is in receipt of one of the disability benefits "
        "listed in SPC Regs 2002 Sch. I para. 1(1)(a)(i): Attendance "
        "Allowance, the Disability Living Allowance care component at the "
        "highest or middle rate, the Personal Independence Payment daily "
        "living component, or Armed Forces Independence Payment. The same "
        "list decides whether a person residing with the claimant is ignored "
        "under Sch. I para. 2(2)(a)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.severe_disability
        return add(person, period, p.relevant_benefits) > 0

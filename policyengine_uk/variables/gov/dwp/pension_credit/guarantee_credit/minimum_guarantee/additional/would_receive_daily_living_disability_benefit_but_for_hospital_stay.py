from policyengine_uk.model_api import *


class would_receive_daily_living_disability_benefit_but_for_hospital_stay(Variable):
    value_type = bool
    entity = Person
    label = "Would receive a daily living disability benefit but for a hospital stay"
    documentation = (
        "Whether this person would be in receipt of the Personal Independence "
        "Payment or Adult Disability Payment daily living component at the "
        "standard or enhanced rate, Pension Age Disability Payment, or the "
        "Scottish adult Disability Living Allowance care component at the "
        "highest or middle rate, but for those benefits' hospital in-patient "
        "rules. SPC Regs 2002 Sch. I para. 1(2)(ba) to (bd) treat such a "
        "partner as in receipt for the couple test in para. 1(1)(b). Unlike "
        "para. 1(2)(b), these heads are not excluded from the reg. 6(5)(b) "
        "double rate."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

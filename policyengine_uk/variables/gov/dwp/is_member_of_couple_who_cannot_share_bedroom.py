from policyengine_uk.model_api import *


class is_member_of_couple_who_cannot_share_bedroom(Variable):
    value_type = bool
    entity = Person
    label = "Member of a couple who cannot share a bedroom (LHA size criteria)"
    documentation = (
        "The claimant or partner of a couple who receives a qualifying "
        "disability benefit (attendance allowance or armed forces "
        "independence payment, the care component of Disability Living "
        "Allowance at the middle or highest rate, or the daily living "
        "component of Personal Independence Payment) and is not reasonably "
        "able to share a bedroom with the other member of the couple because "
        "of their disability (cannot_reasonably_share_bedroom_due_to_"
        "disability). This is the renter in the Universal Credit disabled "
        "person condition and the Housing Benefit 'member of a couple who "
        "cannot share a bedroom', in force from 1 April 2017. Attendance "
        "allowance counted only at the higher rate until 27 January 2025. "
        "The law also lists the Scottish devolved equivalents, which the "
        "model counts only where the data record them as the DWP benefits."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
        "https://www.legislation.gov.uk/uksi/2017/213/made",
        "https://www.legislation.gov.uk/uksi/2025/3/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.LHA.cannot_share_bedroom.couple_member
        # UC Sch 4 para 12(6A): the renter and a joint renter; HB Regs 2006
        # reg 2(1): a member of a couple.
        couple_member = person("is_claimant_or_partner", period) & person.benunit(
            "is_couple", period
        )
        # Para 12(6A)(a); reg 2(1), "member of a couple who cannot share a
        # bedroom", (a).
        qualifying_benefit = add(person, period, p.benefits) > 0
        # Para 12(6A)(b); reg 2(1), (b).
        cannot_share = person(
            "cannot_reasonably_share_bedroom_due_to_disability", period
        )
        return p.in_effect & couple_member & qualifying_benefit & cannot_share

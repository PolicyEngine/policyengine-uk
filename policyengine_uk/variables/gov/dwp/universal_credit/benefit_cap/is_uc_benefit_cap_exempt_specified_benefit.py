from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)

# UC Regs 2013 reg 83(1) names, for each benefit, whose receipt (or
# entitlement) lifts the cap.

# "a claimant is receiving" (reg 83(1)(b)-(e)): industrial injuries benefit,
# attendance allowance, which reg 2 defines to include armed forces
# independence payment, and a war pension or armed forces compensation.
CLAIMANT_BENEFITS = [
    "attendance_allowance",
    "armed_forces_independence_payment",
    "iidb",
    "afcs",
]

# "a claimant, or a child or qualifying young person for whom a claimant is
# responsible" (reg 83(1)(f)).
CHILD_OR_QUALIFYING_YOUNG_PERSON_BENEFITS = [
    "dla",
]

# "a claimant, or a qualifying young person for whom a claimant is
# responsible" (reg 83(1)(g), (i), (ia)).
QUALIFYING_YOUNG_PERSON_BENEFITS = [
    "pip",
    "carers_allowance",
    "carer_support_payment",
]


class is_uc_benefit_cap_exempt_specified_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Universal Credit benefit cap through a specified benefit or element"
    documentation = (
        "Whether the award includes the LCWRA or carer element, or a "
        "claimant (or, for some benefits, a child or qualifying young person "
        "a claimant is responsible for) receives or is entitled to a benefit "
        "listed in UC Regs 2013 reg. 83(1): employment and support allowance "
        "with the support component, industrial injuries benefit, attendance "
        "allowance (including armed forces independence payment, reg. 2), a "
        "war pension or armed forces compensation, disability living "
        "allowance, personal independence payment, carer's allowance or "
        "carer support payment. A claimant is the single claimant or each "
        "joint claimant: a partner who cannot be a joint claimant, so that "
        "the other member claims as a single person (reg. 3(3)), is not one, "
        "and another member of the benefit unit, such as a non-dependent "
        "adult, does not lift the cap with their own benefit. Working tax "
        "credit, which cannot be paid with Universal Credit, is Housing "
        "Benefit's exception (HB Regs 2006 reg. 75E), not this one."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/83",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        claimant = claimant_or_partner & ~other_member_of_single_claim(person, period)

        # A child or qualifying young person a claimant is responsible for
        # (UC Regs 2013 regs 4-5), which includes every 16-year-old until the
        # 1 September after their birthday (reg 5(1)(a)) unless they receive
        # Universal Credit, ESA or JSA themselves (reg 5(5)); annual ages
        # cannot place that date, so any such 16-year-old counts.
        age = person("age", period)
        child_or_young_person = ~claimant_or_partner & person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        sixteen = (
            (age >= 16)
            & (age < 17)
            & ~claimant_or_partner
            & ~person("is_looked_after_by_local_authority", period)
            & ~person("receives_benefits_in_own_right", period)
        )
        child_or_young_person = child_or_young_person | sixteen
        young_person = (
            child_or_young_person
            & person("is_qualifying_young_person_for_universal_credit", period)
        ) | sixteen

        def received_by(benefits, members):
            return add_for_members(benunit, period, benefits, members) > 0

        # Reg 83(1)(a): "the claimant is receiving an employment and support
        # allowance that includes the support component". Contributory and
        # income-related allowances both carry it.
        receiving_esa = (person("esa_contrib", period) > 0) | person(
            "is_on_income_related_esa", period
        )
        esa_support_component = benunit.any(
            claimant & receiving_esa & person("esa_includes_support_component", period)
        )

        # Reg 83(1)(a), (j): the LCWRA or carer element is included in the
        # award: a claimant with limited capability for work and work-related
        # activity or caring responsibilities (regs 27(1), 29(1)), or an
        # element entered directly although no member's circumstances give
        # it (decided by value).
        lcwra = person("uc_limited_capability_for_WRA", period)
        lcwra_element = benunit.any(claimant & lcwra) | (
            (benunit("uc_LCWRA_element", period) > 0) & ~benunit.any(lcwra)
        )
        carer = person("is_carer_for_benefits", period)
        carer_element = benunit.any(claimant & carer) | (
            (benunit("uc_carer_element", period) > 0) & ~benunit.any(carer)
        )

        return (
            esa_support_component
            | received_by(CLAIMANT_BENEFITS, claimant)
            | received_by(
                CHILD_OR_QUALIFYING_YOUNG_PERSON_BENEFITS,
                claimant | child_or_young_person,
            )
            | received_by(QUALIFYING_YOUNG_PERSON_BENEFITS, claimant | young_person)
            | lcwra_element
            | carer_element
        )

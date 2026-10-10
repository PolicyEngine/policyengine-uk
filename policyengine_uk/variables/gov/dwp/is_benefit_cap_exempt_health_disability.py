from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_couple
from policyengine_uk.utils.supplied_inputs import supplied_input
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim_in_shared_rules,
)

# HB Regs 2006 reg 75F(1) and UC Regs 2013 reg 83(1) name, for each benefit,
# whose receipt (or entitlement) lifts the cap.

# "the claimant or the claimant's partner is receiving" (HB reg 75F(1)(b)-(d));
# "a claimant is receiving" (UC reg 83(1)(b)-(e)). Armed Forces Compensation
# Scheme payments are the guaranteed income payments that count as a war
# pension (HB reg 75F(2)(a); UC reg 83(1)(e)).
CLAIMANT_OR_PARTNER_BENEFITS = [
    "attendance_allowance",
    "iidb",
    "afcs",
]

# "the claimant, the claimant's partner or a child or young person for whom
# the claimant or the claimant's partner is responsible" (HB reg 75F(1)(e));
# "a claimant, or a child or qualifying young person for whom a claimant is
# responsible" (UC reg 83(1)(f)).
CHILD_OR_YOUNG_PERSON_BENEFITS = [
    "dla",
]

# "the claimant, the claimant's partner or a young person for whom the
# claimant or the claimant's partner is responsible" (HB reg 75F(1)(ea), (h),
# (ha)); "a claimant, or a qualifying young person for whom a claimant is
# responsible" (UC reg 83(1)(g), (i), (ia)). Carer's allowance and carer
# support payment count by entitlement, not payment: (h)-(ha) and (i)-(ia)
# name a person "entitled to" them, even if an overlapping benefit reduces
# the payment to nil.
YOUNG_PERSON_BENEFITS = [
    "pip",
    "is_entitled_to_carer_benefit",
]

# Armed forces independence payment: Housing Benefit lists it with personal
# independence payment, for a young person too (HB reg 75F(1)(ea)); Universal
# Credit counts it as attendance allowance, a claimant's only (UC Regs 2013
# reg 2, reg 83(1)(c)). Either scheme: the claimant, partner or a Housing
# Benefit young person.
HOUSING_BENEFIT_YOUNG_PERSON_BENEFITS = [
    "armed_forces_independence_payment",
]


class is_benefit_cap_exempt_health_disability(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the benefit cap through a specified benefit, UC element or working tax credit"
    documentation = (
        "Whether the family is outside the benefit cap because the claimant, "
        "their partner or, for some benefits, a child or young person they "
        "are responsible for receives or is entitled to a benefit listed in "
        "HB Regs 2006 reg 75F(1) or UC Regs 2013 reg 83(1), or because the "
        "claimant or couple is entitled to working tax credit (HB Regs 2006 "
        "reg 75E(2)). Another member of the benefit unit, such as a "
        "non-dependent adult, does not lift the cap with their own benefit, "
        "and nor does a partner who cannot be a joint claimant, so that the "
        "other member claims Universal Credit as a single person (UC Regs "
        "2013 reg 3(3)). For a family on Universal Credit the claimant and "
        "partner are the award's claimants, otherwise Housing Benefit's "
        "claimant and partner (benefit_cap_couple). "
        "The model applies one cap to Universal Credit and Housing Benefit, so "
        "an exception in either scheme counts: Universal Credit's LCWRA and "
        "carer elements, and Housing Benefit's wider young-person tests."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75F",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75E",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/83",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # The couple of the scheme the cap reduces (benefit_cap_couple): the
        # claimants of a Universal Credit award, or Housing Benefit's
        # claimant and partner (HB Regs 2006 reg 2(1)).
        claimant_or_partner = benefit_cap_couple(benunit, period)
        # UC reg 83(1) reads "a claimant". A partner who cannot be a joint
        # claimant, so that the other member claims Universal Credit as a
        # single person (reg 3(3)), is a member of the couple but not a
        # claimant: their own benefits and limited capability do not lift the
        # cap. Housing Benefit has no such claim, so a family that stays on
        # legacy benefits keeps both members.
        claimant = claimant_or_partner & ~other_member_of_single_claim_in_shared_rules(
            person, period
        )

        # A child or young person the claimant or partner is responsible for.
        # Housing Benefit counts a child under 16 or a Child Benefit
        # qualifying young person (HB Regs 2006 regs 2(1), 19); Universal
        # Credit a child or qualifying young person (UC Regs 2013 regs 4-5),
        # which includes every 16-year-old until the 1 September after their
        # birthday (reg 5(1)(a)), unless they receive Universal Credit, ESA
        # or JSA themselves (reg 5(5)). Annual ages cannot place that date, so
        # any such 16-year-old counts, as for the family rate in
        # is_responsible_for_child_or_young_person_for_uc_or_housing_benefit
        # (which does not yet apply reg 5(5)).
        age = person("age", period)
        legacy_child_or_young_person = person(
            "is_child_or_young_person_for_legacy_benefits", period
        )
        housing_benefit_young_person = legacy_child_or_young_person & person(
            "is_qualifying_young_person_for_child_benefit", period
        )
        uc_child_or_young_person = ~claimant_or_partner & person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        uc_sixteen = (
            (age >= 16)
            & (age < 17)
            & ~claimant_or_partner
            & ~person("is_looked_after_by_local_authority", period)
            & ~person("receives_benefits_in_own_right", period)
        )
        child_or_young_person = (
            legacy_child_or_young_person | uc_child_or_young_person | uc_sixteen
        )
        young_person = (
            housing_benefit_young_person
            | (
                uc_child_or_young_person
                & person("is_qualifying_young_person_for_universal_credit", period)
            )
            | uc_sixteen
        )

        def received_by(benefits, members):
            return add_for_members(benunit, period, benefits, members) > 0

        # HB reg 75F(1)(a), UC reg 83(1)(a): "the claimant or the claimant's
        # partner is receiving an employment and support allowance ... which
        # includes a support component"; UC reg 83(1)(a) "the claimant".
        # Contributory and income-related allowances both carry it; another
        # member's allowance does not count.
        receiving_esa = (person("esa_contrib", period) > 0) | person(
            "is_on_income_related_esa", period
        )
        esa_support_component = benunit.any(
            claimant & receiving_esa & person("esa_includes_support_component", period)
        )

        # UC reg 83(1)(a), (j): the LCWRA or carer element is included in the
        # award. For calculated elements that is a claimant who has limited
        # capability for work and work-related activity or caring
        # responsibilities (UC Regs 2013 regs 27(1), 29(1)); the model does
        # not have the reg 28 waiting period or regs 29(5)-(6), 30(3). Where
        # reg 29(4) leaves a carer with limited capability only the LCWRA
        # element, that element exempts. An element entered directly is
        # included whatever the members' circumstances: one supplied as an
        # input with a positive amount, or one that is positive although no
        # member's circumstances give it (decided by value, for a reform that
        # replaces the element's formula).
        def element_included(element, circumstance):
            amount = benunit(element, period)
            entered = supplied_input(benunit, element, period)
            entered_positive = (
                np.zeros_like(amount, dtype=bool) if entered is None else entered > 0
            )
            return (
                benunit.any(claimant & circumstance)
                | entered_positive
                | ((amount > 0) & ~benunit.any(circumstance))
            )

        lcwra_element = element_included(
            "uc_LCWRA_element", person("uc_limited_capability_for_WRA", period)
        )
        carer_element = element_included(
            "uc_carer_element", person("is_carer_for_benefits", period)
        )

        # HB reg 75E(2): the claimant is, or the couple are jointly, entitled
        # to working tax credit.
        working_tax_credit = benunit("working_tax_credit", period) > 0

        return (
            esa_support_component
            | received_by(CLAIMANT_OR_PARTNER_BENEFITS, claimant)
            | received_by(
                CHILD_OR_YOUNG_PERSON_BENEFITS, claimant | child_or_young_person
            )
            | received_by(YOUNG_PERSON_BENEFITS, claimant | young_person)
            | received_by(
                HOUSING_BENEFIT_YOUNG_PERSON_BENEFITS,
                claimant | housing_benefit_young_person,
            )
            | lcwra_element
            | carer_element
            | working_tax_credit
        )

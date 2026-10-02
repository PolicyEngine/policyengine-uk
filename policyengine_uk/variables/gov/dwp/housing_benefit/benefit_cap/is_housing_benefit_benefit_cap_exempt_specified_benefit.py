from policyengine_uk.model_api import *

# HB Regs 2006 reg 75F(1) names, for each benefit, whose receipt (or
# entitlement) lifts the cap.

# "the claimant or the claimant's partner is receiving" (reg 75F(1)(b)-(d)):
# industrial injuries benefit, attendance allowance, a war pension, which
# includes an Armed Forces Compensation Scheme guaranteed income payment
# (reg 75F(2)(a)).
CLAIMANT_OR_PARTNER_BENEFITS = [
    "attendance_allowance",
    "iidb",
    "afcs",
]

# "the claimant, the claimant's partner or a child or young person for whom
# the claimant or the claimant's partner is responsible" (reg 75F(1)(e)).
CHILD_OR_YOUNG_PERSON_BENEFITS = [
    "dla",
]

# "the claimant, the claimant's partner or a young person for whom the
# claimant or the claimant's partner is responsible" (reg 75F(1)(ea), (h),
# (ha)): personal independence payment, armed forces independence payment,
# carer's allowance and carer support payment.
YOUNG_PERSON_BENEFITS = [
    "pip",
    "armed_forces_independence_payment",
    "carers_allowance",
    "carer_support_payment",
]


class is_housing_benefit_benefit_cap_exempt_specified_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Housing Benefit benefit cap through a specified benefit"
    documentation = (
        "Whether the claimant, their partner or, for some benefits, a child "
        "or young person they are responsible for receives or is entitled to "
        "a benefit listed in HB Regs 2006 reg. 75F(1): employment and support "
        "allowance with the support component, industrial injuries benefit, "
        "attendance allowance, a war pension or armed forces compensation, "
        "disability living allowance, personal independence payment, armed "
        "forces independence payment, carer's allowance or carer support "
        "payment. Housing Benefit has no claim by a member of a couple as a "
        "single person, so the partner's benefits always count; another "
        "member of the benefit unit, such as a non-dependent adult, does not "
        "lift the cap with their own benefit. The Universal Credit LCWRA and "
        "carer elements are not Housing Benefit exceptions. Regulation "
        "75F(1)(g) (a claimant receiving Universal Credit) never applies: the "
        "model pays a family Universal Credit or Housing Benefit, not both."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75F",
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # The claimant and partner (HB Regs 2006 reg 2(1)).
        claimant = person("is_claimant_or_partner", period)
        # A child or young person the claimant or partner is responsible for:
        # a child under 16 or a Child Benefit qualifying young person (HB
        # Regs 2006 regs 2(1), 19).
        child_or_young_person = person(
            "is_child_or_young_person_for_legacy_benefits", period
        )
        young_person = child_or_young_person & person(
            "is_qualifying_young_person_for_child_benefit", period
        )

        def received_by(benefits, members):
            return add_for_members(benunit, period, benefits, members) > 0

        # Reg 75F(1)(a): "the claimant or the claimant's partner is receiving
        # an employment and support allowance ... which includes a support
        # component". Contributory and income-related allowances both carry
        # it; another member's allowance does not count.
        receiving_esa = (person("esa_contrib", period) > 0) | person(
            "is_on_income_related_esa", period
        )
        esa_support_component = benunit.any(
            claimant & receiving_esa & person("esa_includes_support_component", period)
        )
        return (
            esa_support_component
            | received_by(CLAIMANT_OR_PARTNER_BENEFITS, claimant)
            | received_by(
                CHILD_OR_YOUNG_PERSON_BENEFITS, claimant | child_or_young_person
            )
            | received_by(YOUNG_PERSON_BENEFITS, claimant | young_person)
        )

from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import award_of_couple
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
)
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award

# HB Regs 2006 reg 75F(1) names, for each benefit, whose receipt (or
# entitlement) lifts the cap.

# "the claimant or the claimant's partner is receiving" (reg 75F(1)(b)-(d)):
# industrial injuries benefit, attendance allowance, and a war pension, which
# includes the Armed Forces Compensation Scheme's guaranteed income payments
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
# and entitlement to carer's allowance or carer support payment. These count
# by entitlement, not payment: (h)-(ha) name a person "entitled to" them, even
# if an overlapping benefit reduces the payment to nil.
YOUNG_PERSON_BENEFITS = [
    "pip",
    "armed_forces_independence_payment",
    "is_entitled_to_carer_benefit",
]


class is_housing_benefit_benefit_cap_exempt_specified_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Housing Benefit benefit cap through a specified benefit"
    documentation = (
        "Whether the claimant, partner or (for some benefits) a child or "
        "young person they are responsible for receives or is entitled to a "
        "benefit listed in HB Regs 2006 reg. 75F(1): employment and support "
        "allowance with the support component, industrial injuries benefit, "
        "attendance allowance, a war pension or armed forces compensation, "
        "disability living allowance, personal independence payment, armed "
        "forces independence payment, or entitlement to carer's allowance or "
        "carer support payment; or a Housing Benefit claimant is receiving "
        "Universal Credit (reg. 75F(1)(g)), whose own cap applies instead. "
        "Housing Benefit has no claim by a member of a couple as a single "
        "person, so the partner's benefits always count. Another member of "
        "the benefit unit, such as a non-dependent adult, does not lift the "
        "cap with their own benefit. The Universal Credit LCWRA and carer "
        "elements are not Housing Benefit exceptions. Regulation 75F(1)(g) "
        "reads a family with Housing Benefit before the cap and an award of "
        "Universal Credit before the cap (universal_credit_pre_benefit_cap), "
        "so a Universal Credit award the cap reduces to nil still lifts the "
        "Housing Benefit cap. A young person is the model's Child Benefit "
        "qualifying young person (HB Regs 2006 reg. 19), which includes a "
        "16-year-old who has left education, until the 31 August after their "
        "16th birthday (Child Benefit (General) Regulations 2006 reg. 4), and "
        "a school leaver in an extension period or before a terminal date "
        "where those inputs are set (regs. 5 and 7). Such a young person's "
        "own disability living allowance, personal independence payment or "
        "armed forces independence payment lifts the cap."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75F",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # The claimant and partner (HB Regs 2006 reg 2(1)).
        claimant_or_partner = person("is_claimant_or_partner", period)

        # A child under 16 or a Child Benefit qualifying young person the
        # claimant or partner is responsible for (HB Regs 2006 regs 2(1), 19).
        # A 16-year-old who has left education is one for the year (Child
        # Benefit (General) Regulations 2006 reg. 4), as the cap rate counts
        # them (has_sixteen_year_old_dependant).
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
        # it; another member's allowance does not count. The couple's
        # income-related award is claimant_or_partner_esa_income
        # (award_of_couple), and it is received by its payee (reg 2(3A);
        # is_on_income_related_esa reads the same).
        couple_esa_award = award_of_couple(
            benunit,
            period,
            "esa_income",
            "esa_income_reported",
            income_related_esa_award,
            claimant_or_partner,
        )
        receiving_income_related_esa = benunit.project(
            couple_esa_award > 0
        ) & is_payee_of_couple_award(
            person, period, "esa_income_reported", couple=claimant_or_partner
        )
        receiving_esa = (person("esa_contrib", period) > 0) | (
            receiving_income_related_esa
        )
        esa_support_component = benunit.any(
            claimant_or_partner
            & receiving_esa
            & person("esa_includes_support_component", period)
        )

        # Reg 75F(1)(g): "the claimant is receiving universal credit". The
        # claimant is a Housing Benefit claimant, a family with Housing
        # Benefit before the cap; it is then capped through Universal Credit,
        # which counts its Housing Benefit as nil (UC Regs 2013 reg 80(2A)).
        # A family on Universal Credit alone keeps the exceptions above, so
        # the two schemes' exceptions can be compared for it. Housing Benefit
        # eligibility (housing_benefit_eligible) rules out a family that
        # claims Universal Credit, so this applies only where both awards are
        # supplied.
        receiving_universal_credit = (
            benunit("universal_credit_pre_benefit_cap", period) > 0
        ) & (benunit("housing_benefit_pre_benefit_cap", period) > 0)

        return (
            receiving_universal_credit
            | esa_support_component
            | received_by(CLAIMANT_OR_PARTNER_BENEFITS, claimant_or_partner)
            | received_by(
                CHILD_OR_YOUNG_PERSON_BENEFITS,
                claimant_or_partner | child_or_young_person,
            )
            | received_by(YOUNG_PERSON_BENEFITS, claimant_or_partner | young_person)
        )

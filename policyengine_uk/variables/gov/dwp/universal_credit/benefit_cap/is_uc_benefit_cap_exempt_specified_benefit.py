from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import award_of_couple
from policyengine_uk.utils.formula_origin import calculated_by
from policyengine_uk.utils.supplied_inputs import supplied_input
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
)
from policyengine_uk.variables.gov.dwp.esa_income import (
    income_related_esa_award_on_reports,
)
from policyengine_uk.variables.gov.dwp.universal_credit.carer_element.uc_carer_element import (
    uc_carer_element,
)
from policyengine_uk.variables.gov.dwp.universal_credit.disability_element.limited_work_ability.uc_LCWRA_element import (
    uc_LCWRA_element,
)

# UC Regs 2013 reg 83(1) names, for each benefit, whose receipt (or
# entitlement) lifts the cap.

# "a claimant is receiving" (reg 83(1)(b)-(e)): industrial injuries benefit,
# attendance allowance, which reg 2 defines to include armed forces
# independence payment, and a war pension, which includes the Armed Forces
# Compensation Scheme's guaranteed income payments.
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
# responsible" (reg 83(1)(g), (i), (ia)). Carer's allowance and carer support
# payment count by entitlement, not payment: (i)-(ia) name a person "entitled
# to" them, even if an overlapping benefit reduces the payment to nil.
QUALIFYING_YOUNG_PERSON_BENEFITS = [
    "pip",
    "is_entitled_to_carer_benefit",
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
        "joint claimant (is_uc_assessed_claimant): a partner who cannot be a "
        "joint claimant, so that the other member claims as a single person "
        "(reg. 3(3)), is not one, and another member of the benefit unit, "
        "such as a non-dependent adult, does not lift the cap with their own "
        "benefit. Working tax credit, which cannot be paid with Universal "
        "Credit, is Housing Benefit's exception (HB Regs 2006 reg. 75E), not "
        "this one."
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
        # The members of the couple whose income the award assesses
        # (is_uc_assessed_claimant), including the other member of a couple
        # where one member claims as a single person (reg 78(2)). Reg 83(1)
        # reads "a claimant": that other member (reg 3(3)) is a member of the
        # couple but not a claimant, so their own benefits and limited
        # capability do not lift the cap.
        couple = person("is_uc_assessed_claimant", period)
        claimant = couple & ~other_member_of_single_claim(person, period)

        # A child or qualifying young person a claimant is responsible for
        # (UC Regs 2013 regs 4-5), which includes every 16-year-old until the
        # 1 September after their birthday (reg 5(1)(a)), unless they receive
        # Universal Credit, ESA or JSA themselves (reg 5(5)). Annual ages
        # cannot place that date, so any such 16-year-old counts, as for the
        # family rate in is_uc_benefit_cap_single_claimant_rate.
        age = person("age", period)
        child_or_young_person = ~couple & person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        sixteen = (
            (age >= 16)
            & (age < 17)
            & ~couple
            & ~person("is_looked_after_by_local_authority", period)
            & ~person("receives_benefits_in_own_right", period)
        )
        young_person = (
            child_or_young_person
            & person("is_qualifying_young_person_for_universal_credit", period)
        ) | sixteen
        child_or_young_person = child_or_young_person | sixteen

        def received_by(benefits, members):
            return add_for_members(benunit, period, benefits, members) > 0

        # Reg 83(1)(a): "the claimant is receiving an employment and support
        # allowance ... which includes a support component". Contributory and
        # income-related allowances both carry it; another member's allowance
        # does not count. The couple's income-related award is
        # claimant_or_partner_esa_income where the couple is the claimant and
        # partner, and is read from their reports otherwise
        # (award_of_couple); it is received by its payee
        # (is_payee_of_couple_award).
        couple_esa_award = award_of_couple(
            benunit,
            period,
            "esa_income",
            "esa_income_reported",
            income_related_esa_award_on_reports,
            couple,
        )
        receiving_income_related_esa = benunit.project(
            couple_esa_award > 0
        ) & is_payee_of_couple_award(
            person,
            period,
            "esa_income_reported",
            # WRA 2007 s.1(3)(c): not a member who has reached pensionable age.
            can_claim=~person("is_SP_age", period),
            couple=couple,
        )
        receiving_esa = (person("esa_contrib", period) > 0) | (
            receiving_income_related_esa
        )
        esa_support_component = benunit.any(
            claimant & receiving_esa & person("esa_includes_support_component", period)
        )

        # Reg 83(1)(a), (j): the LCWRA or carer element is included in the
        # award. An element entered for the award is included exactly when it
        # is positive, whatever the members' circumstances (an entry of nil
        # means the award does not include it). An element a reform's formula
        # gives is included when positive. The element is for "a claimant"
        # (regs 27(1), 29(1)), and the model's own formulas give it only for a
        # claimant's limited capability for work and work-related activity or
        # caring responsibilities, so the element they give is included when
        # positive; the check that a claimant has the circumstance guards
        # against a formula that does not. A nil amount (a nil rate) is not
        # included.
        # The Universal Credit rebalancing rescales the formula's elements
        # from 2026 (scenarios/uc_reform.py) and is read the same way. The
        # model does not have the reg 28 waiting period or regs 29(5)-(6),
        # 30(3). Where reg 29(4) leaves a carer with limited capability only
        # the LCWRA element, that element exempts.
        def element_included(element, model_variable, circumstance):
            entered = supplied_input(benunit, element, period)
            if entered is not None:
                return entered > 0
            positive = benunit(element, period) > 0
            if not calculated_by(benunit, element, period, model_variable):
                return positive
            only_other_members = benunit.any(~claimant & circumstance) & ~benunit.any(
                claimant & circumstance
            )
            return positive & ~only_other_members

        lcwra_element = element_included(
            "uc_LCWRA_element",
            uc_LCWRA_element,
            person("uc_limited_capability_for_WRA", period),
        )
        carer_element = element_included(
            "uc_carer_element",
            uc_carer_element,
            person("is_carer_for_benefits", period),
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

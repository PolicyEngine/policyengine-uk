from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)

# Benefits whose receipt by "a claimant" (or, for some, a child or qualifying
# young person the claimant is responsible for) lifts the cap: industrial
# injuries benefit (UC Regs 2013 reg. 83(1)(b)), attendance allowance (c),
# which reg. 2 defines to include armed forces independence payment,
# disability living allowance (f), personal independence payment (g), and
# entitlement to carer's allowance (i) or carer support payment (ia).
SPECIFIED_PERSONAL_BENEFITS = [
    "attendance_allowance",
    "armed_forces_independence_payment",
    # Entitlement, not payment: reg. 83(1)(i)-(ia) read "is entitled to", so
    # an overlapping benefit that reduces the payment to nil still counts.
    "is_entitled_to_carer_benefit",
    "dla",
    "pip_dl",
    "pip_m",
    "iidb",
]


class is_uc_benefit_cap_exempt_specified_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Universal Credit benefit cap through a specified benefit or element"
    documentation = (
        "Whether the award includes the LCWRA or carer element, or a "
        "claimant receives a benefit listed in UC Regs 2013 reg. 83(1): "
        "employment and support allowance with the support component, "
        "industrial injuries benefit, attendance allowance (including armed "
        "forces independence payment, reg. 2), a war pension or armed forces "
        "compensation, disability living allowance, personal "
        "independence payment, or entitlement to carer's allowance or carer "
        "support payment. "
        "A partner who cannot be a joint claimant, so that the other member "
        "claims as a single person (reg. 3(3)), is not a claimant: their own "
        "benefits and limited capability lift no cap. Working tax credit, "
        "which cannot be paid with Universal Credit, is Housing Benefit's "
        "exception (HB Regs 2006 reg. 75E), not this one."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/83",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # The exceptions read "a claimant" (reg. 83(1)); the other member of a
        # single claim is not one.
        claimant_side = ~other_member_of_single_claim(person, period)

        # Reg. 83(1)(a): the LCWRA element is included in the award, or the
        # claimant receives an employment and support allowance that includes
        # the support component (contributory or income-related allowances
        # stand in for it).
        lcwra = benunit.any(
            person("uc_limited_capability_for_WRA", period) & claimant_side
        )
        esa_support_component = (benunit("esa_income", period) > 0) | (
            add_for_members(benunit, period, ["esa_contrib"], claimant_side) > 0
        )
        # Reg. 83(1)(j): the carer element is included in the award.
        carer_element = benunit("uc_carer_element", period) > 0
        specified_benefits = (
            add_for_members(benunit, period, SPECIFIED_PERSONAL_BENEFITS, claimant_side)
            > 0
        )
        # Reg. 83(1)(d)-(e): a war pension, which includes Armed Forces
        # Compensation Scheme payments.
        afcs = add_for_members(benunit, period, ["afcs"], claimant_side) > 0

        return lcwra | esa_support_component | carer_element | specified_benefits | afcs

from policyengine_uk.model_api import *

# Benefits whose receipt (or entitlement) by the claimant or partner, or for
# some a child or young person, lifts the cap: industrial injuries benefit
# (HB Regs 2006 reg. 75F(1)(b)), attendance allowance (c), disability living
# allowance (e), personal independence payment and armed forces independence
# payment (ea), and entitlement to carer's allowance (h) or carer support
# payment (ha).
SPECIFIED_PERSONAL_BENEFITS = [
    "attendance_allowance",
    "armed_forces_independence_payment",
    # Entitlement, not payment: reg. 75F(1)(h)-(ha) read "is entitled to", so
    # an overlapping benefit that reduces the payment to nil still counts.
    "is_entitled_to_carer_benefit",
    "dla",
    "pip_dl",
    "pip_m",
    "iidb",
]


class is_housing_benefit_benefit_cap_exempt_specified_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Housing Benefit benefit cap through a specified benefit"
    documentation = (
        "Whether the claimant, partner or (for some benefits) a child or "
        "young person receives or is entitled to a benefit listed in HB Regs "
        "2006 reg. 75F(1): employment and support allowance with the support "
        "component, industrial injuries benefit, attendance allowance, a war "
        "pension or armed forces compensation, disability living allowance, "
        "personal independence payment, armed forces independence payment, "
        "or entitlement to carer's allowance or carer support payment. "
        "Housing Benefit has no claim by a member of a couple as a single "
        "person, so the partner's benefits always count. The Universal "
        "Credit LCWRA and carer elements are not Housing Benefit exceptions. "
        "Regulation 75F(1)(g) (a claimant receiving Universal Credit) never "
        "applies: the model pays a family Universal Credit or Housing "
        "Benefit, not both."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75F",
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
    )

    def formula(benunit, period, parameters):
        # Reg. 75F(1)(a): an employment and support allowance which includes
        # a support component (contributory or income-related allowances
        # stand in for it).
        esa_support_component = (benunit("esa_income", period) > 0) | (
            add(benunit, period, ["esa_contrib"]) > 0
        )
        specified_benefits = add(benunit, period, SPECIFIED_PERSONAL_BENEFITS) > 0
        # Reg. 75F(1)(d) and (2)(a): a war pension, including a guaranteed
        # income payment under the Armed Forces Compensation Scheme.
        afcs = add(benunit, period, ["afcs"]) > 0
        return esa_support_component | specified_benefits | afcs

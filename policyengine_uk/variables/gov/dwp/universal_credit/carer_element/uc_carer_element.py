from policyengine_uk.model_api import *


class uc_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    documentation = (
        "The amount an award includes because a claimant has regular and "
        "substantial caring responsibilities for a severely disabled person. "
        "Only a claimant's caring counts: a child or qualifying young person "
        "who is a carer does not give the claimants the element. Joint "
        "claimants who are both carers have an element each; the model does "
        "not record who is cared for, and takes two carers to care for "
        "different people, as it does when it pays each of them Carer's "
        "Allowance. A claimant who is a carer and has limited capability for "
        "work and work-related activity has the LCWRA element instead, unless "
        "that element is included for the other joint claimant."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 12(2)(c)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/12",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 29(1), (2) and (4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 30",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/30",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.carer
        person = benunit.members
        # Reg. 29(1): the element is included "where a claimant has regular
        # and substantial caring responsibilities for a severely disabled
        # person" (reg. 30: `is_carer_for_benefits`).
        claimant = person("is_uc_assessed_claimant", period)
        carer = claimant & person("is_carer_for_benefits", period)
        limited_capability = claimant & person("uc_limited_capability_for_WRA", period)
        # Reg. 29(2): "an award is to include the carer element for both joint
        # claimants if they both qualify for it, but only if they are not
        # caring for the same severely disabled person".
        carers_without_limited_capability = benunit.sum(carer & ~limited_capability)
        # Reg. 29(4): where the carer "has limited capability for work and
        # work-related activity (and, in the case of joint claimants, the
        # LCWRA element has not been included in respect of the other
        # claimant), only the LCWRA element may be included in respect of the
        # claimant". Where both joint claimants have limited capability the
        # award has one LCWRA element (reg. 27(4)), for one of them, which
        # leaves a carer element for the other.
        carers_with_limited_capability = benunit.sum(carer & limited_capability)
        claimants_with_limited_capability = benunit.sum(limited_capability)
        carers_keeping_the_carer_element = min_(
            carers_with_limited_capability,
            max_(claimants_with_limited_capability - 1, 0),
        )
        elements = carers_without_limited_capability + carers_keeping_the_carer_element
        return elements * p.amount * MONTHS_IN_YEAR

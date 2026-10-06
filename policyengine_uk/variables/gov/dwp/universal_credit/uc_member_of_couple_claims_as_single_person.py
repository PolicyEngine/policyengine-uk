from policyengine_uk.model_api import *


class uc_member_of_couple_claims_as_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "A member of the couple claims Universal Credit as a single person"
    documentation = (
        "Whether the claimant is a member of a couple but claims as a single "
        "person because the other member cannot be a joint claimant "
        "(Universal Credit Regulations 2013 reg. 3(3)): one member of the "
        "couple is `uc_is_ineligible_partner` and the other is a claimant who "
        "meets the modelled age conditions of section 4(1)(a) and (b). The "
        "award then has a single claimant's amounts (reg. 36(3)), the "
        "couple's capital (reg. 18(2)) and the deduction joint claimants "
        "would have (reg. 22(3)). False where no member can claim: both "
        "flagged, a single adult flagged, or a claimant over State Pension "
        "age."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 3(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        ),
        dict(
            title="Welfare Reform Act 2012 s. 4",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        ),
    ]

    def formula(benunit, period, parameters):
        person = benunit.members
        ineligible_partner = person("is_uc_assessed_claimant", period) & person(
            "uc_is_ineligible_partner", period
        )
        # Reg. 3(3) lets the other member claim; WRA 2012 s. 4(1)(a) and (b)
        # (with reg. 8) decide whether they can, as in is_uc_eligible.
        can_claim = (
            person("is_uc_single_or_joint_claimant", period)
            & person("meets_uc_minimum_age_condition", period)
            & ~person("is_SP_age", period)
        )
        return benunit.any(ineligible_partner) & benunit.any(can_claim)

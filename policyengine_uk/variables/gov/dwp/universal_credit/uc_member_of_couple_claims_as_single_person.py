from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import couple_members


class uc_member_of_couple_claims_as_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "A member of the couple claims Universal Credit as a single person"
    documentation = (
        "Whether the claimant is a member of a couple but claims as a single "
        "person because the other member cannot be a joint claimant "
        "(Universal Credit Regulations 2013 reg. 3(3)): one member of the "
        "couple is `uc_is_ineligible_partner` and the other is a claimant. "
        "The award then has a single claimant's amounts (reg. 36(3)), the "
        "couple's capital (reg. 18(2)) and the deduction joint claimants "
        "would have (reg. 22(3)). False where neither member of the couple "
        "can claim, so there is no claim."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 3(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        ),
    ]

    def formula(benunit, period, parameters):
        person = benunit.members
        ineligible_partner = couple_members(person, period) & person(
            "uc_is_ineligible_partner", period
        )
        claimant = person("is_uc_single_or_joint_claimant", period)
        return benunit.any(ineligible_partner) & benunit.any(claimant)

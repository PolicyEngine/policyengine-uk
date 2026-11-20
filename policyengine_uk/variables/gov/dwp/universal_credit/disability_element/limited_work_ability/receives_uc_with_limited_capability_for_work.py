from policyengine_uk.model_api import *


class receives_uc_with_limited_capability_for_work(Variable):
    value_type = bool
    entity = Person
    label = "receives Universal Credit with limited capability for work"
    documentation = (
        "Whether this person has limited capability for work (Universal "
        "Credit Regulations 2013 reg 39), is a Universal Credit claimant "
        "(a single claimant or one of joint claimants) and is in a benefit "
        "unit with a Universal Credit award. uc_limited_capability_for_work "
        "is the assessment alone, and defaults from disability, so it does "
        "not establish that Universal Credit is in payment. The claimant "
        "condition excludes a partner who cannot be a joint claimant "
        "(reg 3(3), for example one subject to immigration control), whose "
        "partner's single award is not theirs."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 39",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/39",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 3(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        ),
    ]

    def formula(person, period, parameters):
        has_uc_award = person.benunit("universal_credit", period) > 0
        is_claimant = person("is_uc_single_or_joint_claimant", period)
        return (
            person("uc_limited_capability_for_work", period)
            & is_claimant
            & has_uc_award
        )

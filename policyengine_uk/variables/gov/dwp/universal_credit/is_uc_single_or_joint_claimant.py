from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import claimants


class is_uc_single_or_joint_claimant(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit claimant (a single claimant or each joint claimant)"
    documentation = (
        "A claimant in the sense of the Welfare Reform Act 2012 s. 40: a "
        "single claimant or each of joint claimants. This is the claimant or "
        "partner (`is_uc_claimant`), the two eldest if more are flagged, less "
        "a partner who cannot be a joint claimant (`uc_is_ineligible_partner`): "
        "where the other member of a couple is under 18 and outside "
        "regulation 8, not in Great Britain, a prisoner, excluded by "
        "regulation 19 or subject to immigration control, the member who can "
        "claim does so as a single person (Universal Credit Regulations 2013 "
        "reg. 3(3)). Such a partner is still a member of the couple: their "
        "capital and income count (regs. 18(2) and 22(3)), but rules that "
        "turn on a claimant's own circumstances do not read theirs."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 40",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/40",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 3(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        ),
    ]

    def formula(person, period, parameters):
        return claimants(person, period)

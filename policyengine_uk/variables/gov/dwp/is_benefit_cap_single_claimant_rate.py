from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    single_claim_in_rules_shared_with_legacy_benefits,
)


class is_benefit_cap_single_claimant_rate(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit cap single claimant rate applies"
    documentation = (
        "Whether the claimant is a single claimant, not responsible for a "
        "child or young person. The model uses one benefit cap for Universal "
        "Credit and Housing Benefit, so the family rate applies if either "
        "scheme's child or young-person test is met. Couple status stands for "
        "joint-claim status, except that a member of a couple who claims "
        "Universal Credit as a single person (regulation 3(3)) is a single "
        "claimant: regulation 80A sets the limits by single claimant and "
        "joint claimants (ADM E5007 note 3). The welfare benefits capped are "
        "still the couple's (regulations 78(2) and 79(1)). Housing Benefit "
        "has no such single claim, so a family that stays on legacy "
        "benefits (reports one and would not claim Universal Credit) keeps "
        "the couple rate."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80A",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/78",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75CA",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
    )

    def formula(benunit, period, parameters):
        single_claimant = ~benunit(
            "is_couple", period
        ) | single_claim_in_rules_shared_with_legacy_benefits(benunit, period)
        return single_claimant & ~benunit(
            "is_responsible_for_child_or_young_person_for_uc_or_housing_benefit",
            period,
        )

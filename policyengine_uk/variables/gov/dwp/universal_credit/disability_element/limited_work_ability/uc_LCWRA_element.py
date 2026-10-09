from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)


class uc_LCWRA_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit limited capability for work-related-activity element"
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 27(1)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/27",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 36(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/36",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.disabled
        person = benunit.members
        limited_capability = person("uc_limited_capability_for_WRA", period)
        # The element is for "a claimant" with limited capability for work and
        # work-related activity (reg. 27(1)). A partner who cannot be a joint
        # claimant, so that the other member claims as a single person
        # (reg. 3(3)), is not a claimant.
        not_a_claimant = other_member_of_single_claim(person, period)
        person_amounts = (limited_capability & ~not_a_claimant) * p.amount
        return benunit.sum(person_amounts) * MONTHS_IN_YEAR

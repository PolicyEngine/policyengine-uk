from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)


class uc_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    definition_period = YEAR
    unit = GBP
    defined_for = "benunit_has_carer"
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 29(1)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 36(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/36",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.carer
        person = benunit.members
        # The element is for "a claimant" with regular and substantial caring
        # responsibilities (reg. 29(1)). A partner who cannot be a joint
        # claimant, so that the other member claims as a single person
        # (reg. 3(3)), is not a claimant: their caring gives no element.
        not_a_claimant = other_member_of_single_claim(person, period)
        carer = person("is_carer_for_benefits", period)
        only_carer_is_not_a_claimant = benunit.any(
            carer & not_a_claimant
        ) & ~benunit.any(carer & ~not_a_claimant)
        return ~only_carer_is_not_a_claimant * p.amount * MONTHS_IN_YEAR

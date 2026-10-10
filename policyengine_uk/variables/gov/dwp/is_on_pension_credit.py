from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
)


class is_on_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "on Pension Credit"
    documentation = (
        "Whether State Pension Credit is payable to this person. Pension "
        "Credit is the claimant's entitlement, with their partner's income "
        "and capital treated as theirs (SPCA 2002 ss.1 and 5), and is paid "
        "to the claimant, not the partner. The claimant must have attained "
        "the qualifying age (s.1(2)(b)), so of the claimant and partner only "
        "a member who has can be the payee: the one who reports the award, "
        "or else the benefit-unit head, or else the elder. Where neither "
        "member has attained it, the same order applies to both. They are on "
        "it only while the benefit unit's award (pension_credit) is "
        "positive, as for the legacy income-related awards. Any other member "
        "of the benefit unit claims in their own right and is on it only if "
        "they report an award themselves."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/5",
    )

    def formula(person, period, parameters):
        couple_award = (person.benunit("pension_credit", period) > 0) & (
            is_payee_of_couple_award(
                person,
                period,
                "pension_credit_reported",
                can_claim=person(
                    "has_attained_state_pension_credit_qualifying_age", period
                ),
            )
        )
        own_award = person("pension_credit_reported", period) > 0
        return where(person("is_claimant_or_partner", period), couple_award, own_award)

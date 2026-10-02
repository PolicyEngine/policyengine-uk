from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim_in_shared_rules,
    single_claim_in_rules_shared_with_legacy_benefits,
)


class is_lha_shared_accommodation_rate_specified_renter(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter restricted to the shared accommodation rate"
    documentation = (
        "The modelled specified-renter conditions: no partner, or a member of "
        "a couple who claims Universal Credit as a single person (UC "
        "regulation 3(3); Schedule 4 paragraph 28(2)), below the shared "
        "accommodation age threshold, not responsible for a child or young "
        "person under the UC or Housing Benefit rules, no non-dependant under "
        "the household composition proxy, and not excepted by a disability "
        "benefit (UC Schedule 4 paragraph 29(5)). The age and the exception "
        "are the renter's own: the other member of a couple claiming as a "
        "single person is neither a renter nor a non-dependant (paragraph "
        "9(2)(b)). Other paragraph 29 exceptions are not modelled. The same "
        "category serves Housing Benefit, whose young-individual definition "
        "(HB regulation 2(1)) has neither the disability exception nor a "
        "single claim by a member of a couple. The model applies the "
        "disability exception to Housing Benefit too, and the single-claim "
        "rule unless the family claims legacy benefits "
        "(`claims_legacy_benefits`)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/27",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/29",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.LHA
        person = benunit.members
        # UC Sch 4 para 28(2): "the renter is a single person (or a member of
        # a couple claiming as a single person) who (a) is under 35 years old;
        # and (b) is not an excepted person". Where a member of a couple
        # claims as a single person (reg. 3(3)), the renter is that member:
        # the other member's age and benefits do not count.
        claims_as_single_person = single_claim_in_rules_shared_with_legacy_benefits(
            benunit, period
        )
        other_member = other_member_of_single_claim_in_shared_rules(person, period)
        renter = person("is_claimant_or_partner", period) & ~other_member
        renter_age = benunit.max(where(renter, person("age", period), -np.inf))
        # UC Sch 4 para 29(5): a renter under 35 receiving
        # attendance allowance, DLA care at the middle or highest rate, or the
        # PIP daily living component is excepted. Other para 29 exceptions
        # (care leavers, hostel residents, MAPPA, domestic abuse, modern
        # slavery, foster parents) are not observed.
        excepted_disabled_renter = benunit.any(
            renter
            & (add(person, period, p.shared_accommodation_exception_benefits) > 0)
        )
        return (
            (~benunit("is_couple", period) | claims_as_single_person)
            & (renter_age < p.shared_accommodation_age_threshold)
            & ~benunit(
                "is_responsible_for_child_or_young_person_for_uc_or_housing_benefit",
                period,
            )
            & ~benunit("lha_renter_has_non_dependant", period)
            & ~excepted_disabled_renter
        )

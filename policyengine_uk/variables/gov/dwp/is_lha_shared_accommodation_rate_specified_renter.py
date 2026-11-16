from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)


class is_lha_shared_accommodation_rate_specified_renter(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter restricted to the shared accommodation rate"
    documentation = (
        "The Universal Credit specified-renter conditions (UC Regs 2013 Sch 4 "
        "paras 27 and 28): a single person, or a member of a couple claiming "
        "as a single person (reg. 3(3)), who is under the shared "
        "accommodation age threshold and not excepted by a disability benefit "
        "(para 29(5); armed forces independence payment counts as attendance "
        "allowance, reg. 2) or as a foster parent or adopter (para 29(9A)); "
        "not responsible for a child or qualifying young person under UC "
        "regs 4 and 5; and with no non-dependant (see "
        "universal_credit_renter_has_non_dependant). The age and "
        "the exceptions are the renter's own: the other member of a couple "
        "claiming as a single person is neither the renter nor a "
        "non-dependant (para 9(2)(b)). Other paragraph 29 exceptions are not "
        "modelled. Housing Benefit has its own test: see "
        "is_housing_benefit_young_individual and housing_benefit_LHA_category."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/27",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/29",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.LHA
        person = benunit.members
        # UC Sch 4 para 28(2): "the renter is a single person (or a member of
        # a couple claiming as a single person) who (a) is under 35 years old;
        # and (b) is not an excepted person". Where a member of a couple
        # claims as a single person (reg. 3(3)), the renter is that member:
        # the other member's age and benefits do not count.
        claims_as_single_person = benunit(
            "uc_member_of_couple_claims_as_single_person", period
        )
        other_member = other_member_of_single_claim(person, period)
        renter = person("is_claimant_or_partner", period) & ~other_member
        renter_age = benunit.max(where(renter, person("age", period), -np.inf))
        # UC Sch 4 para 29(5): a renter under 35 receiving
        # attendance allowance (which includes armed forces independence
        # payment, reg 2), DLA care at the middle or highest rate, or the PIP
        # daily living component is excepted. Other para 29 exceptions (care
        # leavers, hostel residents, MAPPA, domestic abuse, modern slavery)
        # are not observed.
        excepted_disabled_renter = benunit.any(
            renter
            & (add(person, period, p.shared_accommodation_exception_benefits) > 0)
        )
        # Para 29(9A): a renter who satisfies the foster parent condition.
        excepted_foster_parent = benunit(
            "lha_renter_meets_foster_parent_condition", period
        )
        return (
            (~benunit("is_couple", period) | claims_as_single_person)
            & (renter_age < p.shared_accommodation_age_threshold)
            # Para 28(3)-(4): responsibility for a child or qualifying young
            # person under UC regs 4 and 5, and the para 9 non-dependant. A
            # Housing Benefit young person who is not a Universal Credit
            # qualifying young person is a non-dependant (para 9(2)), which
            # universal_credit_renter_has_non_dependant counts.
            & ~benunit(
                "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
                period,
            )
            & ~benunit("universal_credit_renter_has_non_dependant", period)
            & ~excepted_disabled_renter
            & ~excepted_foster_parent
        )

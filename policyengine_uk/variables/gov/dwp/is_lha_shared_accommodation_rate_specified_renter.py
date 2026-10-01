from policyengine_uk.model_api import *


class is_lha_shared_accommodation_rate_specified_renter(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter restricted to the shared accommodation rate"
    documentation = (
        "The modelled specified-renter conditions: no partner, below the shared "
        "accommodation age threshold, not responsible for a child or young "
        "person under the UC or Housing Benefit rules, no non-dependant under "
        "the household composition proxy, and not excepted by a disability "
        "benefit (UC Schedule 4 paragraph 29(5)) or as a foster parent or "
        "adopter (paragraph 29(9A)). Other paragraph 29 exceptions and "
        "couples claiming as single people are not modelled. Housing Benefit "
        "has its own young-individual test: see "
        "is_housing_benefit_young_individual."
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
        # UC Sch 4 para 29(5): a renter under 35 receiving
        # attendance allowance (which includes armed forces independence
        # payment, reg 2), DLA care at the middle or highest rate, or the PIP
        # daily living component is excepted. Other para 29 exceptions (care
        # leavers, hostel residents, MAPPA, domestic abuse, modern slavery)
        # are not observed.
        excepted_disabled_renter = benunit.any(
            person("is_claimant_or_partner", period)
            & (add(person, period, p.shared_accommodation_exception_benefits) > 0)
        )
        # Para 29(9A): a renter who satisfies the foster parent condition.
        excepted_foster_parent = benunit(
            "lha_renter_meets_foster_parent_condition", period
        )
        return (
            ~benunit("is_couple", period)
            & (
                benunit("eldest_claimant_or_partner_age", period)
                < p.shared_accommodation_age_threshold
            )
            & ~benunit(
                "is_responsible_for_child_or_young_person_for_uc_or_housing_benefit",
                period,
            )
            & ~benunit("lha_renter_has_non_dependant", period)
            & ~excepted_disabled_renter
            & ~excepted_foster_parent
        )

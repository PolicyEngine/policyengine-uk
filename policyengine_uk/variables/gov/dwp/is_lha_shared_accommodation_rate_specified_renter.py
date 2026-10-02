from policyengine_uk.model_api import *


class is_lha_shared_accommodation_rate_specified_renter(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter restricted to the shared accommodation rate"
    documentation = (
        "The modelled Universal Credit specified-renter conditions: no "
        "partner, below the shared accommodation age threshold, not "
        "responsible for a child or qualifying young person, no non-dependant "
        "(see universal_credit_renter_has_non_dependant), and not excepted by "
        "a disability benefit (UC Schedule 4 paragraph 29(5)) or as a foster "
        "parent or adopter (paragraph 29(9A)). Other paragraph 29 exceptions "
        "and couples claiming as single people are not modelled. Housing "
        "Benefit has its own test: see is_housing_benefit_young_individual "
        "and housing_benefit_LHA_category."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/27",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/29",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
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
            # Para 28(3)-(4): responsibility under UC regs 4-5 and the para
            # 9 non-dependant, not the legacy schemes' child or young person.
            & ~benunit(
                "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
                period,
            )
            & ~benunit("universal_credit_renter_has_non_dependant", period)
            & ~excepted_disabled_renter
            & ~excepted_foster_parent
        )

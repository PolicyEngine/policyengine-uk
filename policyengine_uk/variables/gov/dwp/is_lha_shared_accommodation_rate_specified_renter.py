from policyengine_uk.model_api import *


class is_lha_shared_accommodation_rate_specified_renter(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter restricted to the shared accommodation rate"
    documentation = (
        "The modelled specified-renter conditions: no partner, below the shared "
        "accommodation age threshold, not responsible for a UC child or "
        "qualifying young person, and no non-dependant under the household "
        "composition proxy. UC Schedule 4 paragraph 29 exceptions and couples "
        "claiming as single people are not modelled. This category also serves "
        "Housing Benefit, whose young-person definition instead follows Child "
        "Benefit (HB regulation 19)."
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
        return (
            ~benunit("is_couple", period)
            & (
                benunit("eldest_claimant_or_partner_age", period)
                < p.shared_accommodation_age_threshold
            )
            & ~benunit(
                "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
                period,
            )
            & ~benunit("lha_renter_has_non_dependant", period)
        )

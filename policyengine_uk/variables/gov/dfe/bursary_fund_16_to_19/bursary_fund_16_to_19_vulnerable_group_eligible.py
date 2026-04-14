from policyengine_uk.model_api import *


class bursary_fund_16_to_19_vulnerable_group_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for vulnerable-group 16 to 19 Bursary Fund support"
    documentation = (
        "Whether the student meets the defined vulnerable-group conditions for the 16 to 19 Bursary Fund. "
        "This first-pass model uses explicit care/self-supporting inputs and person-level reported-benefit "
        "proxies for own-right UC, IS, and ESA receipt."
    )
    definition_period = YEAR
    defined_for = "would_claim_bursary_fund_16_to_19"

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND

        age_eligible = person("bursary_fund_16_to_19_age_eligible", period)
        in_qualifying_education = person(
            "bursary_fund_16_to_19_in_qualifying_education", period
        )

        in_care_or_care_leaver = person(
            "bursary_fund_16_to_19_in_care_or_care_leaver", period
        )
        self_supporting = person("bursary_fund_16_to_19_self_supporting", period)

        receives_uc_or_is = person(
            "bursary_fund_16_to_19_receives_uc_or_is_in_own_right", period
        )
        receives_uc_or_esa = person(
            "bursary_fund_16_to_19_receives_uc_or_esa_in_own_right", period
        )

        receives_disability_benefit = (person("dla", period) > 0) | (
            person("pip", period) > 0
        )

        vulnerable_group = (
            in_care_or_care_leaver
            | (self_supporting & receives_uc_or_is)
            | (receives_disability_benefit & receives_uc_or_esa)
        )

        return in_england & age_eligible & in_qualifying_education & vulnerable_group

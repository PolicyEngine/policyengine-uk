from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import (
    is_excluded_relevant_benefit_partner,
    reports_relevant_benefit,
)


class pawhp_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for the Pension Age Winter Heating Payment"
    documentation = (
        "Whether this individual is entitled to a Pension Age Winter Heating "
        "Payment: they have reached pensionable age and live in Scotland, "
        "they are not the other member of a couple on a relevant benefit "
        "whose payment is made to their partner, and, for the 2024 "
        "qualifying week, they are entitled to a relevant benefit (reg 7, "
        "with reg 7(2) treating both members of a couple as entitled, and "
        "reg 9(1)(d) as made paying one of them). For the "
        "2025 qualifying week the couple rule (reg 10(8) as substituted by "
        "SSI 2025/282) applied only within reg 10, so reg 9(d), which "
        "excludes 'one member of a couple ... who is entitled to a relevant "
        "benefit' once the other member is paid, read literally reaches only "
        "a member entitled in their own right. The model makes one payment "
        "per couple on a relevant benefit in 2025 too, as for the 2024 week "
        "(reg 7(2)) and from April 2026 (reg 2A, inserted by SSI 2026/170)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/5",
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/9",
        "https://www.legislation.gov.uk/ssi/2025/282/regulation/7/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.social_security_scotland.pawhp
        country = person.household("country", period).decode_to_str()
        resident = p.active & (country == "SCOTLAND")
        pension_age = person("is_SP_age", period) | (
            not p.eligibility.state_pension_age_requirement
        )
        qualifies = resident & pension_age
        on_relevant_benefit = person("is_on_pawhp_relevant_benefit", period)
        meets_benefit_condition = on_relevant_benefit | (
            not p.eligibility.require_benefits
        )
        excluded = is_excluded_relevant_benefit_partner(
            person,
            period,
            qualifies,
            on_relevant_benefit,
            reports_relevant_benefit(person, period, p.eligibility),
        )
        return qualifies & meets_benefit_condition & ~excluded

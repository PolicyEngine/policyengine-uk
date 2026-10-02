from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import (
    is_excluded_relevant_benefit_partner,
    reports_relevant_benefit,
)


class winter_fuel_payment_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for the Winter Fuel Payment"
    documentation = (
        "Whether this person is entitled to a Winter Fuel Payment: they have "
        "reached pensionable age and live where the payment is made, they "
        "are not the partner of the person paid for a couple on a relevant "
        "benefit, and, for the 2024 qualifying week only, they are on a "
        "relevant benefit of their own or their couple's (SI 2024/869 reg "
        "2(2)(b)). Up to the 2023 week and from the 2025 week everyone of "
        "pensionable age is entitled (SI 2000/729 reg 2; SI 2025/969 reg 2; "
        "NISR 2025/142 reg 2). From 2025-26 the winter fuel payment charge "
        "recovers the payment through income tax from a person whose own "
        "total income exceeds £35,000 and who is not on a relevant benefit "
        "(winter_fuel_payment_charge); entitlement, and so the shared "
        "amounts, are unaffected by it. The deprecated household income test "
        "in gov.dwp.winter_fuel_payment.eligibility.taxable_income_test "
        "applies only in a reform that requires a relevant benefit."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2000/729/regulation/2",
        "https://www.legislation.gov.uk/uksi/2024/869/regulation/2",
        "https://www.legislation.gov.uk/uksi/2024/869/regulation/4",
        "https://www.legislation.gov.uk/uksi/2025/969/regulation/2",
        "https://www.legislation.gov.uk/uksi/2025/969/regulation/4",
        "https://www.legislation.gov.uk/nisr/2025/142/regulation/2",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.winter_fuel_payment.eligibility
        country = person.household("country", period).decode_to_str()
        resident = np.isin(country, p.countries)
        is_SP_age = person("is_SP_age", period)
        pension_age = is_SP_age | (not p.state_pension_age_requirement)
        qualifies = resident & pension_age
        on_relevant_benefit = person(
            "is_on_winter_fuel_payment_relevant_benefit", period
        )
        income_test = p.taxable_income_test
        meets_income_test = (
            person.household.any(
                is_SP_age
                & (person("total_income", period) <= income_test.maximum_taxable_income)
            )
            & np.isin(country, ["ENGLAND", "WALES"])
            & income_test.use_maximum_taxable_income
        )
        meets_means_condition = (
            on_relevant_benefit | (not p.require_benefits) | meets_income_test
        )
        excluded = is_excluded_relevant_benefit_partner(
            person,
            period,
            qualifies,
            on_relevant_benefit,
            reports_relevant_benefit(person, period, p),
        )
        return qualifies & meets_means_condition & ~excluded

from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import winter_heating_payment_amount


class winter_fuel_payment(Variable):
    value_type = float
    entity = Person
    label = "Winter Fuel Payment"
    documentation = (
        "The Winter Fuel Payment made to this person. A person on a relevant "
        "benefit receives the full amount (the higher amount if they or their "
        "partner have reached 80), once per couple. Anyone else receives the "
        "full amount if no other person in their household is eligible, and "
        "a shared amount otherwise."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2000/729/regulation/2",
        "https://www.legislation.gov.uk/uksi/2024/869/regulation/3",
        "https://www.legislation.gov.uk/uksi/2025/969/regulation/3",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.winter_fuel_payment
        return winter_heating_payment_amount(
            person,
            period,
            person("winter_fuel_payment_eligible", period),
            person("is_on_winter_fuel_payment_relevant_benefit", period),
            p.amount,
            p.eligibility.higher_age_requirement,
        )

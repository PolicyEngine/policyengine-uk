from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import winter_heating_payment_amount


class pension_age_winter_heating_payment(Variable):
    value_type = float
    entity = Person
    label = "Pension Age Winter Heating Payment"
    documentation = (
        "The Pension Age Winter Heating Payment made to this individual. An "
        "individual entitled to a relevant benefit receives the full amount "
        "(the higher amount if they or their partner have reached 80), once "
        "per couple. From the 2025 qualifying week anyone else receives the "
        "full amount if they do not live with another entitled individual, "
        "and a shared amount otherwise."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/10/made",
        "https://www.legislation.gov.uk/ssi/2025/282/regulation/9/made",
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/10",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.social_security_scotland.pawhp
        return winter_heating_payment_amount(
            person,
            period,
            person("pawhp_eligible", period),
            person("is_on_pawhp_relevant_benefit", period),
            p.amount,
            p.eligibility.higher_age_requirement,
        )

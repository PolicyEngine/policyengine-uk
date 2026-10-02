from policyengine_uk.model_api import *

# The payments s.681I(6)(a) defines as a "winter fuel payment": the Winter
# Fuel Payment in England and Wales (SI 2025/969) and Northern Ireland (NISR
# 2025/142), and Scotland's Pension Age Winter Heating Payment (SSI 2024/351).
WINTER_FUEL_PAYMENTS = [
    "winter_fuel_payment",
    "pension_age_winter_heating_payment",
]


class winter_fuel_payment_charge(Variable):
    value_type = float
    entity = Person
    label = "winter fuel payment charge"
    documentation = (
        "The charge to income tax that recovers a person's winter fuel "
        "payment: the whole payment, when the person's own total income for "
        "the tax year exceeds the threshold and they are not entitled to a "
        "relevant benefit in the qualifying week. It is additional tax at "
        "Step 7 of the income tax calculation, so tax reductions do not "
        "offset it. The payment itself, and who counts as another entitled "
        "person for the shared amounts, are unaffected by the charge."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/1/section/681I",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/30",
        "https://www.legislation.gov.uk/ukpga/2026/11/schedule/10",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.charges.winter_fuel_payment
        payment = add(person, period, WINTER_FUEL_PAYMENTS)
        over_threshold = person("total_income", period) > p.income_threshold
        on_relevant_benefit = add(person, period, p.relevant_benefits) > 0
        return p.in_effect * payment * over_threshold * ~on_relevant_benefit

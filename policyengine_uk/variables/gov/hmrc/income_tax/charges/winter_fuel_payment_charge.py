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
        "relevant benefit in the qualifying week. Total income includes the "
        "statutory sick and maternity pay the model taxes as employment "
        "income. It is additional tax at "
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
        # Total income is the income charged to tax (ITA 2007 s.23 Step 1).
        # The model taxes statutory sick and maternity pay as employment
        # income (employment_benefits, in taxable_employment_income), but
        # total_income leaves them out, so they are added here.
        total_income = person("total_income", period) + person(
            "employment_benefits", period
        )
        over_threshold = total_income > p.income_threshold
        on_relevant_benefit = add(person, period, p.relevant_benefits) > 0
        return p.in_effect * payment * over_threshold * ~on_relevant_benefit

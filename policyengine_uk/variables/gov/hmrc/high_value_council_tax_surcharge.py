from policyengine_uk.model_api import *


class high_value_council_tax_surcharge(Variable):
    value_type = float
    entity = Household
    label = "High Value Council Tax Surcharge"
    documentation = (
        "Additional annual surcharge on owners of residential property in England "
        "worth at least £2 million in 2026 prices."
    )
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        if period.start.year < 2028:
            return 0

        country = household("country", period)
        in_england = country == country.possible_values.ENGLAND

        p = parameters(period)
        property_value = household("main_residence_value", period)
        current_index = p.gov.economic_assumptions.indices.obr.per_capita.gdp
        baseline_index = parameters(
            "2026"
        ).gov.economic_assumptions.indices.obr.per_capita.gdp
        value_2026_prices = property_value / (current_index / baseline_index)

        surcharge = p.gov.hmrc.council_tax.high_value_surcharge.amount.calc(
            value_2026_prices
        )
        return where(in_england, surcharge, 0)

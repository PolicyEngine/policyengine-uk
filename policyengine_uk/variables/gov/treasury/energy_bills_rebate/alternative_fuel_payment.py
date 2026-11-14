from policyengine_uk.model_api import *


class ebr_alternative_fuel_payment(Variable):
    label = "Alternative Fuel Payment (EBR)"
    documentation = (
        "Calendar-year sum of the monthly Alternative Fuel Payment, as "
        "ebr_energy_bills_credit sums the Energy Bills Support Scheme."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://assets.publishing.service.gov.uk/media/63a59ed48fa8f5654fe0a812/ebss-ni-direction.pdf#page=2",
        "https://www.gov.uk/government/news/households-across-northern-ireland-to-start-receiving-600-uk-government-energy-support",
    )

    def formula(household, period, parameters):
        annual_payment = 0
        for month in range(1, MONTHS_IN_YEAR + 1):
            annual_payment = annual_payment + household(
                "monthly_ebr_alternative_fuel_payment",
                f"{period.this_year}-{month:02d}",
            )
        return annual_payment

from policyengine_uk.model_api import *


class monthly_ebr_alternative_fuel_payment(Variable):
    label = "Monthly Alternative Fuel Payment"
    documentation = (
        "Northern Ireland's £200 Alternative Fuel Payment for the month. "
        "Electricity suppliers paid it with the £400 Energy Bills Support "
        "Scheme amount, as one £600 payment to each eligible domestic "
        "customer, whatever fuel the household heats with. Great Britain's "
        "Alternative Fuel Payment, for households that heat with heating oil, "
        "LPG, biomass and other alternative fuels, is not modelled."
    )
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = GBP
    defined_for = "ebr_energy_bills_credit_eligible"
    reference = (
        "https://assets.publishing.service.gov.uk/media/63a59ed48fa8f5654fe0a812/ebss-ni-direction.pdf#page=2",
        "https://www.gov.uk/government/news/households-across-northern-ireland-to-start-receiving-600-uk-government-energy-support",
        "https://www.gov.uk/government/news/increased-flexibility-of-alternative-fuel-payments-so-more-households-will-be-supported-with-their-energy-bills",
    )

    def formula(household, period, parameters):
        ebr = parameters(period).gov.treasury.energy_bills_rebate
        country = household("country", period.this_year)
        is_northern_ireland = country == country.possible_values.NORTHERN_IRELAND
        return is_northern_ireland * ebr.alternative_fuel_payment_northern_ireland

from policyengine_uk.model_api import *


class household_energy_payment(Variable):
    label = "Household Energy Payment"
    documentation = (
        "One-off payment to households in the qualifying council tax bands and "
        "countries, delivered by local authorities through the council tax "
        "system. Budget 2026 sets £100 for bands A to D in England, from "
        "January 2027."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://assets.publishing.service.gov.uk/media/6ae1ec57bdb574cf1c9b3f12/E03668986_HMT_Budget_2026_ELAY__2_.pdf#page=117",
        "https://www.gov.uk/government/publications/budget-2026-document/budget-2026-html",
    ]

    def formula(household, period, parameters):
        p = parameters(period).gov.treasury.household_energy_payment
        band = household("council_tax_band", period)
        country = household("country", period)
        in_band = np.isin(band.decode_to_str(), list(p.bands))
        in_country = np.isin(country.decode_to_str(), list(p.countries))
        return in_band * in_country * p.amount

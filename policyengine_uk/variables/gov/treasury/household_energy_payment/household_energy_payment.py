from policyengine_uk.model_api import *


class household_energy_payment(Variable):
    label = "Household Energy Payment"
    documentation = (
        "One-off payment to households in the qualifying council tax bands and "
        "countries, which local authorities pay into bank accounts. Budget "
        "2026 sets £100 for bands A to D in England, from "
        "January 2027. It goes to the householder liable for council tax on "
        "their main home, including most households exempt from council tax. "
        "The model pays every household in a qualifying band: survey data "
        "hold only main homes, so second homes and empty properties do not "
        "arise, but the model can't tell which households have a landlord "
        "liable for council tax (council tax in the rent), so it pays them, "
        "which slightly overstates recipients."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://assets.publishing.service.gov.uk/media/6ae1ec57bdb574cf1c9b3f12/E03668986_HMT_Budget_2026_ELAY__2_.pdf#page=117",
        "https://www.gov.uk/government/publications/budget-2026-document/budget-2026-html",
        "https://www.gov.uk/government/news/what-the-autumn-budget-2026-means-for-your-energy-bills",
    ]

    def formula(household, period, parameters):
        p = parameters(period).gov.treasury.household_energy_payment
        band = household("council_tax_band", period)
        country = household("country", period)
        in_band = np.isin(band.decode_to_str(), list(p.bands))
        in_country = np.isin(country.decode_to_str(), list(p.countries))
        return in_band * in_country * p.amount

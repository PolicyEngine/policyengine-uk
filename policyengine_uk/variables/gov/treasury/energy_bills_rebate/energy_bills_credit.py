from policyengine_uk.model_api import *


class ebr_energy_bills_credit(Variable):
    label = "Energy bills credit (EBR)"
    documentation = "Energy Bills Support Scheme discount. Modeled as a flat transfer."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://assets.publishing.service.gov.uk/media/632c38bf8fa8f53cb3746e74/energy-bills-support-scheme-ministerial-direction.pdf",
        "https://www.gov.uk/government/news/households-across-northern-ireland-to-start-receiving-600-uk-government-energy-support",
    )

    def formula(household, period, parameters):
        ebr = parameters(period).gov.treasury.energy_bills_rebate
        country = household("country", period)
        is_northern_ireland = country == country.possible_values.NORTHERN_IRELAND
        return where(
            is_northern_ireland,
            ebr.energy_bills_credit_northern_ireland,
            ebr.energy_bills_credit,
        )

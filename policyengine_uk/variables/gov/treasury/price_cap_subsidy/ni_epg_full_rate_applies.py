from policyengine_uk.model_api import *


class ni_epg_full_rate_applies(Variable):
    label = "Full Northern Ireland Energy Price Guarantee rates apply"
    documentation = (
        "Caller assertion that every positive-use electricity and mains-gas "
        "supply represented this month qualifies for the full published "
        "Northern Ireland discounts. Tariffs must sufficiently exceed the "
        "applicable floor, with contract, payment and multi-rate conditions "
        "met. Missing or false does not establish zero actual support."
    )
    entity = Household
    definition_period = MONTH
    value_type = bool
    reference = (
        "https://www.gov.uk/government/publications/energy-bills-support/energy-price-guarantee-up-until-30-june-2023",
    )

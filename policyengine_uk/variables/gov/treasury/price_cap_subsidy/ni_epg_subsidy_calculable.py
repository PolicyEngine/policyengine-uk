from policyengine_uk.model_api import *
from policyengine_uk.utils.energy_price_guarantee import ni_epg_calculation


class ni_epg_subsidy_calculable(Variable):
    label = "Can calculate Northern Ireland full-rate Energy Price Guarantee subsidy"
    documentation = (
        "Northern Ireland only. During supported months, positive-use relief "
        "requires supplied monthly fuel quantities, a full-rate applicability "
        "assertion and a compatible gross pre-discount monthly bill. A zero "
        "subsidy with this flag false is uncomputed, not observed no-support. "
        "Zero-rate months and explicitly supplied zero use are known zero. "
        "Current microdata lack the required inputs; low-tariff and partial-rate "
        "contracts remain unsupported."
    )
    entity = Household
    definition_period = MONTH
    value_type = bool

    def formula(household, period, parameters):
        return ni_epg_calculation(household, period, parameters)[1]

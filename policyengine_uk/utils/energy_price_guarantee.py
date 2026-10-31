"""Calculate supported full-rate Northern Ireland consumer bill relief."""

import numpy as np

from policyengine_uk.utils.supplied_inputs import supplied_input


def ni_epg_calculation(household, period, parameters):
    """Return consumer relief and whether supplied inputs establish it."""
    country = household("country", period.this_year)
    in_northern_ireland = country == country.possible_values.NORTHERN_IRELAND
    zero = np.zeros(household.count)
    p = parameters(period).gov.ofgem.energy_price_guarantee_northern_ireland
    if p.electricity_discount == 0 and p.gas_discount == 0:
        return zero, in_northern_ireland

    electricity = supplied_input(household, "electricity_consumption_kwh", period)
    gas = supplied_input(household, "gas_consumption_kwh", period)
    if electricity is None or gas is None:
        return zero, np.zeros_like(in_northern_ireland)

    known_use = (
        np.isfinite(electricity) & np.isfinite(gas) & (electricity >= 0) & (gas >= 0)
    )
    zero_use = known_use & (electricity == 0) & (gas == 0)
    full_rate = supplied_input(household, "ni_epg_full_rate_applies", period)
    bill = supplied_input(household, "monthly_domestic_energy_consumption", period)
    if full_rate is None or bill is None:
        return zero, in_northern_ireland & zero_use

    vat = parameters(period).gov.hmrc.vat
    relief = electricity * p.electricity_discount * (
        1 + vat.domestic_electricity_rate.northern_ireland
    ) + gas * p.gas_discount * (1 + vat.reduced_rate)
    supported = (
        in_northern_ireland
        & known_use
        & full_rate
        & np.isfinite(bill)
        & (bill >= 0)
        & (bill >= relief)
    )
    calculable = in_northern_ireland & (zero_use | supported)
    return np.where(supported, relief, 0), calculable

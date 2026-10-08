from types import SimpleNamespace

from policyengine_uk.model_api import *
from policyengine_uk.utils.parameters import fiscal_year_average


def _domestic_energy_vat(household, period, electricity_rate, gas_rate, priced_rate):
    # electricity_consumption and gas_consumption are priced at Ofgem cap unit
    # rates, which include VAT at the reduced rate, so the VAT-exclusive base is
    # the bill divided by one plus that rate (5/105 of the bill at 5%). The
    # base is held fixed when the rate changes. The inputs are calibrated to
    # NEED consumption, not grossed up to receipts, so neither the survey
    # consumption coverage nor the household share of VAT receipts applies.
    country = household("country", period)
    northern_ireland = country == country.possible_values.NORTHERN_IRELAND
    rate = where(
        northern_ireland,
        electricity_rate.northern_ireland,
        electricity_rate.great_britain,
    )
    electricity = household("electricity_consumption", period) / (1 + priced_rate)
    gas = household("gas_consumption", period) / (1 + priced_rate)
    return electricity * rate + gas * gas_rate


class domestic_energy_vat(Variable):
    label = "VAT on domestic electricity and gas"
    documentation = (
        "VAT on the household's electricity and gas bills. Electricity is "
        "charged at its own rate, which is zero in Great Britain from 1 October "
        "2026 to 31 March 2027; gas is charged at the reduced rate."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1994/23/schedule/7A",
        "https://www.legislation.gov.uk/uksi/2026/987/contents/made",
    ]

    def formula(household, period, parameters):
        p = parameters(period)
        vat = p.gov.hmrc.vat
        return _domestic_energy_vat(
            household,
            period,
            vat.domestic_electricity_rate,
            vat.reduced_rate,
            p.baseline.gov.hmrc.vat.reduced_rate,
        )


class baseline_domestic_energy_vat(Variable):
    label = "baseline VAT on domestic electricity and gas"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        # The baseline parameter tree keeps its dated values (it is not
        # converted to fiscal years), so the electricity rates are
        # day-weighted here as the reform tree's are, or a simulation with no
        # reform would show a VAT change in 2026-27.
        rates = household.simulation.tax_benefit_system.parameters.baseline.gov
        rates = rates.hmrc.vat.domestic_electricity_rate
        year = period.start.year
        electricity_rate = SimpleNamespace(
            great_britain=fiscal_year_average(rates.great_britain, year),
            northern_ireland=fiscal_year_average(rates.northern_ireland, year),
        )
        reduced_rate = parameters(period).baseline.gov.hmrc.vat.reduced_rate
        return _domestic_energy_vat(
            household, period, electricity_rate, reduced_rate, reduced_rate
        )

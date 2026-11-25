from types import SimpleNamespace

from policyengine_uk.model_api import *
from policyengine_uk.utils.parameters import fiscal_year_average


def _domestic_energy_vat(household, period, parameters, electricity_rate, gas_rate):
    # electricity_rate and gas_rate each carry great_britain and
    # northern_ireland rates.
    # electricity_consumption and gas_consumption are priced including 5% VAT
    # by the data build, so the VAT-exclusive base is the bill
    # divided by 1.05 (5/105 of the bill is VAT). The divisor is the rate the
    # inputs were priced at (gov.simulation.vat.energy_input_price_basis_rate),
    # never the statutory rate being modelled, so the base stays fixed when a
    # reform changes a VAT rate. The inputs are calibrated to NEED consumption,
    # not grossed up to receipts, so neither the survey consumption coverage
    # nor the household share of VAT receipts applies.
    priced_rate = parameters(period).gov.simulation.vat.energy_input_price_basis_rate
    country = household("country", period)
    northern_ireland = country == country.possible_values.NORTHERN_IRELAND
    electricity_vat = where(
        northern_ireland,
        electricity_rate.northern_ireland,
        electricity_rate.great_britain,
    )
    gas_vat = where(northern_ireland, gas_rate.northern_ireland, gas_rate.great_britain)
    electricity = household("electricity_consumption", period) / (1 + priced_rate)
    gas = household("gas_consumption", period) / (1 + priced_rate)
    return electricity * electricity_vat + gas * gas_vat


class domestic_energy_vat(Variable):
    label = "VAT on domestic electricity and gas"
    documentation = (
        "VAT on the household's electricity and gas bills. Electricity has "
        "its own rate, which is zero in Great Britain from 1 October 2026 and "
        "in Northern Ireland from 1 April 2027, to 30 June 2027. Gas has its "
        "own rate too, which equals the reduced rate in current law."
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
            parameters,
            vat.domestic_electricity_rate,
            vat.domestic_gas_rate,
        )


class baseline_domestic_energy_vat(Variable):
    label = "baseline VAT on domestic electricity and gas"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        # The baseline parameter tree keeps its dated values (it is not
        # converted to fiscal years), so the electricity and gas rates are
        # day-weighted here as the reform tree's are, or a simulation with no
        # reform would show a VAT change in 2026-27.
        vat = household.simulation.tax_benefit_system.parameters.baseline.gov.hmrc.vat
        year = period.start.year

        def day_weighted(rates):
            return SimpleNamespace(
                great_britain=fiscal_year_average(rates.great_britain, year),
                northern_ireland=fiscal_year_average(rates.northern_ireland, year),
            )

        return _domestic_energy_vat(
            household,
            period,
            parameters,
            day_weighted(vat.domestic_electricity_rate),
            day_weighted(vat.domestic_gas_rate),
        )

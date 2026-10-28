"""Household electricity and gas price indices, with VAT at the input basis rate.

Builds ``gov.economic_assumptions.energy_prices.quarterly``,
``.calendar_year`` and ``.fiscal_year`` from the published inputs under
``gov.economic_assumptions.energy_prices`` (see the README beside this file).
Each index prices its fuel with VAT at the rate the electricity and gas inputs
assume (``gov.simulation.vat.energy_input_price_basis_rate``), so a VAT
change, in the published prices or in a reform, never moves it.

Quarterly levels, from the first quarter of 2015:

- to the last quarter ONS publishes in full (``last_full_quarter`` in the
  ``ons`` metadata, which the importer writes), the mean of the monthly CPI
  index, each month divided by the VAT factor the price includes:
  ``1 + s * ((1 + r) / (1 + b) - 1)``, where ``r`` is the UK electricity VAT
  rate in the published price on the 15th (``embedded_electricity_vat``, the
  Great Britain and Northern Ireland rates weighted by consumption), ``b`` the
  basis rate and ``s`` electricity's share of the series' CPI weight (1 for
  electricity, 0 for gas);
- after that, the level a year earlier grown by the OBR's utilities
  inflation for the quarter with the change in electricity VAT taken out:
  ``(1 + g) * u(q - 4) / u(q) - 1``, where ``u`` is the same factor for
  electricity's share of the utilities weight (electricity and gas), averaged
  over the quarter's months. Past the OBR's last quarter the last rate holds.

The generator reads every input at the month or quarter it applies to, not
at its stated dates, so a reform keyed by year (one value for a calendar
year) applies to each month or quarter of it, and one with no end, which
removes the stated values after its start, to every month or quarter after
it. A month or quarter with no value is an error.

The OBR forecasts utilities only, so electricity and gas grow at the same
rate after the ONS outturn: each index is the fuel's own price to there and a
utilities proxy after it.

Annual levels average a year's four quarters, each weighted by its share of
the year's domestic consumption (``consumption_shares``; for electricity, gas
and solid fuels, electricity's and gas's shares weighted by their CPI
weights). ``calendar_year`` averages January to December, ``fiscal_year``
April to March: model year 2026 is fiscal year 2026-27. Both are dated
1 January. Where ``held_flat`` is true for a year, as ``no_economic_assumptions``
sets it, the annual levels take the previous year's.
"""

import re

from policyengine_core.parameters import Parameter, ParameterNode

FIRST_YEAR = 2015
# The last calendar and fiscal year of the annual indices; fiscal year 2041
# needs the first quarter of 2042.
LAST_YEAR = 2041
SERIES = {
    "electricity": "electricity",
    "gas": "gas",
    "electricity_gas_and_solid_fuels": "electricity, gas and solid fuels",
}


def _next(quarter):
    year, number = quarter
    return (year + 1, 1) if number == 4 else (year, number + 1)


def _year_earlier(quarter):
    return quarter[0] - 1, quarter[1]


def _quarters(first, last):
    quarters = [first]
    while quarters[-1] < last:
        quarters.append(_next(quarters[-1]))
    return quarters


def _months(quarter):
    year, number = quarter
    return [(year, month) for month in range(3 * number - 2, 3 * number + 1)]


def _start(quarter):
    return f"{quarter[0]:04d}-{3 * quarter[1] - 2:02d}-01"


def _label(quarter):
    return f"{quarter[0]}Q{quarter[1]}"


def _stated(parameter):
    """The dates of a series' stated values, leaving out removed ones."""
    return [
        entry.instant_str for entry in parameter.values_list if entry.value is not None
    ]


class EnergyPriceInputs:
    """The published inputs, read from a raw parameter tree."""

    def __init__(self, parameters: ParameterNode):
        self.prices = parameters.gov.economic_assumptions.energy_prices
        self.basis_rate = parameters.gov.simulation.vat.energy_input_price_basis_rate
        last = str(self.prices.ons.metadata.get("last_full_quarter"))
        match = re.fullmatch(r"(\d{4})Q([1-4])", last)
        if match is None:
            raise ValueError(
                "The ONS prices must state the last quarter ONS publishes in "
                f"full as last_full_quarter metadata, such as 2026Q3, not {last}."
            )
        self.last_outturn = int(match[1]), int(match[2])
        if self.last_outturn < (FIRST_YEAR, 4):
            raise ValueError(
                f"ONS prices must cover the four quarters of {FIRST_YEAR}."
            )
        stated = _stated(self.prices.obr.utilities)
        if not stated:
            raise ValueError("The OBR utilities inflation forecast has no values.")
        self.forecast_start = _next(self.last_outturn)
        first = int(min(stated)[:4]), (int(min(stated)[5:7]) + 2) // 3
        if first > self.forecast_start:
            raise ValueError(
                f"The OBR utilities forecast starts in {_label(first)}, after "
                f"{_label(self.forecast_start)}, the first quarter without three "
                "months of ONS prices."
            )

    def ons_price(self, key: str, year: int, month: int) -> float:
        """The ONS CPI index for a series in a month."""
        price = self.prices.ons.get_child(key)(f"{year:04d}-{month:02d}-01")
        if price is None:
            raise ValueError(f"ONS {key} prices have no value for {year}-{month:02d}.")
        return price

    def electricity_vat_factor(self, year: int, month: int) -> float:
        """Published electricity price over its price at the basis rate."""
        day = f"{year:04d}-{month:02d}-15"
        vat = self.prices.embedded_electricity_vat
        ni = vat.northern_ireland_share(day)
        rate = (1 - ni) * vat.great_britain(day) + ni * vat.northern_ireland(day)
        return (1 + rate) / (1 + self.basis_rate(day))

    def electricity_share(self, key: str, year: int) -> float:
        """Electricity's share of a series' CPI weight in a year."""
        if key == "electricity":
            return 1.0
        if key == "gas":
            return 0.0
        weights = self.prices.ons.weights
        instant = f"{year}-01-01"
        return weights.electricity(instant) / weights.get_child(key)(instant)

    def utilities_electricity_share(self, year: int) -> float:
        weights = self.prices.ons.weights
        instant = f"{year}-01-01"
        electricity = weights.electricity(instant)
        return electricity / (electricity + weights.gas(instant))

    def utilities_vat_factor(self, quarter) -> float:
        """Published utilities price over its price at the basis rate."""
        factor = sum(self.electricity_vat_factor(*month) for month in _months(quarter))
        share = self.utilities_electricity_share(quarter[0])
        return 1 + share * (factor / 3 - 1)

    def utilities_growth(self, quarter) -> float:
        """OBR utilities inflation for a quarter, before the VAT change."""
        growth = self.prices.obr.utilities(_start(quarter))
        if growth is None:
            raise ValueError(
                f"The OBR utilities forecast has no value for {_label(quarter)}."
            )
        return (1 + growth) * self.utilities_vat_factor(
            _year_earlier(quarter)
        ) / self.utilities_vat_factor(quarter) - 1

    def consumption_shares(self, key: str, year: int) -> list:
        """Each quarter's weight in a year's average, summing to one."""
        instant = f"{year}-01-01"

        def fuel(name):
            node = self.prices.consumption_shares.get_child(name)
            return [node.get_child(f"q{n}")(instant) for n in range(1, 5)]

        if key == "electricity_gas_and_solid_fuels":
            weights = self.prices.ons.weights
            electricity = weights.electricity(instant)
            gas = weights.gas(instant)
            shares = [
                (electricity * e + gas * g) / (electricity + gas)
                for e, g in zip(fuel("electricity"), fuel("gas"))
            ]
        else:
            shares = fuel(key)
        total = sum(shares)
        return [share / total for share in shares]


def quarterly_levels(inputs: EnergyPriceInputs, key: str) -> dict:
    """Quarterly levels at the basis rate, 2015 = 100 before the adjustment."""
    levels = {}
    for quarter in _quarters((FIRST_YEAR, 1), (LAST_YEAR + 1, 1)):
        if quarter <= inputs.last_outturn:
            share = inputs.electricity_share(key, quarter[0])
            levels[quarter] = (
                sum(
                    inputs.ons_price(key, *month)
                    / (1 + share * (inputs.electricity_vat_factor(*month) - 1))
                    for month in _months(quarter)
                )
                / 3
            )
        else:
            levels[quarter] = levels[_year_earlier(quarter)] * (
                1 + inputs.utilities_growth(quarter)
            )
    return levels


def annual_levels(inputs: EnergyPriceInputs, key: str, quarterly: dict):
    """Consumption-weighted calendar and fiscal year levels, held where set."""
    calendar, fiscal = {}, {}
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        q1, q2, q3, q4 = inputs.consumption_shares(key, year)
        calendar[year] = sum(
            share * quarterly[(year, n)] for n, share in enumerate((q1, q2, q3, q4), 1)
        )
        fiscal[year] = (
            q2 * quarterly[(year, 2)]
            + q3 * quarterly[(year, 3)]
            + q4 * quarterly[(year, 4)]
            + q1 * quarterly[(year + 1, 1)]
        )
    for year in range(FIRST_YEAR + 1, LAST_YEAR + 1):
        if inputs.prices.held_flat(f"{year}-01-01"):
            calendar[year] = calendar[year - 1]
            fiscal[year] = fiscal[year - 1]
    return calendar, fiscal


def add_energy_price_indices(parameters: ParameterNode) -> ParameterNode:
    inputs = EnergyPriceInputs(parameters)
    prices = inputs.prices
    descriptions = {
        "quarterly": (
            "Quarterly price level of household {}, with VAT at the energy "
            "input basis rate, by calendar quarter."
        ),
        "calendar_year": (
            "Price level of household {} in a calendar year, January to "
            "December, with VAT at the energy input basis rate."
        ),
        "fiscal_year": (
            "Price level of household {} in a model year, the fiscal year "
            "April to March, with VAT at the energy input basis rate."
        ),
    }
    nodes = {}
    for name in descriptions:
        nodes[name] = ParameterNode(name=f"{prices.name}.{name}", data={})
        prices.add_child(name, nodes[name])
    for key, label in SERIES.items():
        quarterly = quarterly_levels(inputs, key)
        calendar, fiscal = annual_levels(inputs, key, quarterly)
        series = {
            "quarterly": {_start(q): value for q, value in quarterly.items()},
            "calendar_year": {f"{y}-01-01": value for y, value in calendar.items()},
            "fiscal_year": {f"{y}-01-01": value for y, value in fiscal.items()},
        }
        for name, values in series.items():
            nodes[name].add_child(
                key,
                Parameter(
                    name=f"{prices.name}.{name}.{key}",
                    data={
                        "description": descriptions[name].format(label),
                        "metadata": {"label": f"{label.capitalize()} price index"},
                        "values": values,
                    },
                ),
            )
    return parameters

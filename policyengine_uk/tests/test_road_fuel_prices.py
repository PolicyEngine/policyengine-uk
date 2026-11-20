from pathlib import Path

import pytest
import yaml

import policyengine_uk
from policyengine_uk.system import system

PRICES = system.parameters.household.consumption.fuel.prices
YOY = system.parameters.gov.economic_assumptions.yoy_growth


@pytest.mark.parametrize(
    "year, petrol_pence, diesel_pence",
    [
        # DESNZ Quarterly Energy Prices table 4.1.2, annual typical retail
        # prices (ULSP, ULSD), the series Microcosm UK uses to price spending.
        (2023, 147.746334, 158.188711),
        (2024, 141.477665, 148.328885),
        (2025, 135.072210, 142.548575),
    ],
)
def test_pump_prices_are_desnz_annual_averages(year, petrol_pence, diesel_pence):
    assert PRICES.petrol(year) * 100 == pytest.approx(petrol_pence, abs=1e-5)
    assert PRICES.diesel(year) * 100 == pytest.approx(diesel_pence, abs=1e-5)


@pytest.mark.parametrize("fuel", ["petrol", "diesel"])
def test_spending_litre_proxy_is_derived_from_the_pump_prices(fuel):
    """The proxy must be re-derived whenever the pump prices change.

    Spending grows by the proxy, household weights by population, and
    litres are spending divided by the price, so weighted litres follow
    the HMRC/OBR road-fuel volume path only if
    (1 + proxy) = (1 + volume) x price_t / price_t-1 / (1 + population).
    """
    proxy = getattr(YOY.obr, f"{fuel}_spending_litre_proxy")
    price = getattr(PRICES, fuel)
    volume = YOY.obr.road_fuel_volume
    population = YOY.ons.population
    # The years the YAML itself declares; the loaded parameter also carries
    # values the system adds before the first declared date.
    source = Path(policyengine_uk.__file__).parent / (
        "parameters/gov/economic_assumptions/yoy_growth.yaml"
    )
    declared = yaml.safe_load(source.read_text())["obr"][
        f"{fuel}_spending_litre_proxy"
    ]["values"]
    years = sorted(int(str(date)[:4]) for date in declared)
    assert years[0] == 2021
    for year in years:
        expected = (1 + volume(year)) * price(year) / price(year - 1) / (
            1 + population(year)
        ) - 1
        assert proxy(year) == pytest.approx(expected, abs=1e-12), (
            f"{fuel}_spending_litre_proxy for {year} no longer matches the "
            f"pump prices; re-derive it from household.consumption.fuel.prices."
        )

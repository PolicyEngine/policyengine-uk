"""Bus fare parameters agree with each other and with the facts they encode."""

import datetime
import runpy
from pathlib import Path

import pytest
import yaml

from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario
from policyengine_uk import Simulation

BUS_PARAMETERS = Path(__file__).parents[1] / "parameters" / "gov" / "dft" / "bus"


def last_published_quarter():
    """The first day of the last quarter in the published fares index, and
    the day after it ends."""
    raw = yaml.safe_load((BUS_PARAMETERS / "local_bus_fares_index.yaml").read_text())
    areas = {key: values for key, values in raw.items() if key.isupper()}
    starts = {max(values) for values in areas.values()}
    # DfT publishes every area's quarter in the same release.
    assert len(starts) == 1, starts
    (start,) = starts
    month = start.month + 3
    end = datetime.date(start.year + month // 13, (month - 1) % 12 + 1, 1)
    return start, end


def test_reference_cap_is_the_cap_the_published_index_reflects():
    start, end = last_published_quarter()
    assert (start, end) == (datetime.date(2026, 1, 1), datetime.date(2026, 4, 1))
    bus = system.parameters.gov.dft.bus
    changes = sorted(
        {
            datetime.date.fromisoformat(value.instant_str)
            for schedule in (bus.fares.cap, bus.reference_fares.cap)
            for value in schedule.values_list
        }
    )
    held = bus.reference_fares(start.isoformat()).cap
    for day in changes + [start, end]:
        reference = bus.reference_fares(day.isoformat()).cap
        if day < end:
            # Up to the last published quarter, the index reflects the cap
            # in force.
            assert reference == bus.fares(day.isoformat()).cap, day
        else:
            # After it, the index holds the cap of that quarter.
            assert reference == held, day


BANDS = ("LOW", "MIDDLE", "HIGH")
SINGLE_SHARE = 0.70
# DfT BUS01a journeys less BUS01c older/disabled journeys, England outside
# London. Other concessions remain in priced boardings, with their discounts
# reflected in the average yield.
# https://assets.publishing.service.gov.uk/media/69c11f97cfa346b9d4704a50/bus01.ods
PRICED_BOARDINGS_2023_24 = 1_780_912_900.01636 - 391_017_149.37439
PRICED_BOARDINGS_2024_25 = 1_850_509_887.26131 - 402_846_350.14539


def test_outside_london_yield_uses_older_disabled_concessions():
    # BUS05ai FY2024-25 receipts divided by BUS01a boardings less only the
    # older/disabled BUS01c journeys. Subtracting every concessionary journey
    # also excludes other concessions and inflates this yield.
    yield_per_boarding = system.parameters.gov.dft.bus.yield_per_boarding
    assert yield_per_boarding.ENGLAND_OUTSIDE_LONDON("2024-01-01") == pytest.approx(
        2_069_953_713.42079 / PRICED_BOARDINGS_2024_25, abs=1e-12
    )


@pytest.mark.parametrize(
    "area, expected",
    [
        ("LONDON", 1.017729905895),
        ("SCOTLAND", 2.599723222144),
        ("NORTHERN_IRELAND", 2.550929922065),
    ],
)
def test_other_area_yields_are_unchanged(area, expected):
    yield_per_boarding = system.parameters.gov.dft.bus.yield_per_boarding
    assert yield_per_boarding.children[area]("2024-01-01") == expected


def cpi(year):
    indices = system.parameters.gov.economic_assumptions.indices.obr
    return indices.consumer_price_index(f"{year}-01-01")


def bands(year=2024):
    """(share, fare) of each band, as the model reads them in a year."""
    table = system.parameters.gov.dft.bus.uncapped_single_fares
    at = f"{year}-01-01"
    return [
        (table.share.children[band](at), table.fare.children[band](at))
        for band in BANDS
    ]


def saving(cap, year=2024, price_ratio=1.0):
    """Mean saving per single ticket from a cap held all year."""
    return sum(share * max(price_ratio * fare - cap, 0) for share, fare in bands(year))


def test_uncapped_fare_bands():
    (low_share, low), (middle_share, middle), (high_share, high) = bands()
    assert low_share + middle_share + high_share == pytest.approx(1)
    # Bands at FY2024-25 prices: at or below GBP 2, up to GBP 3, above GBP 3.
    assert low <= 2 < middle <= 3 < high
    # Fares move with CPI after FY2024-25; shares stay.
    for year in (2025, 2027):
        for (share, fare), (later_share, later_fare) in zip(bands(), bands(year)):
            assert later_share == share
            assert later_fare == pytest.approx(fare * cpi(year) / cpi(2024))


def test_table_matches_dft_cap_evaluation():
    # Frontier Economics and SYSTRA for DfT, Table 6: all single tickets
    # averaged GBP 2.15 before the cap and GBP 1.83 after (a GBP 0.32
    # saving); those above GBP 2 averaged GBP 2.73, which puts their share
    # near 0.32 / 0.73 = 0.44. Read at face value, as the fit does.
    table = bands()
    above = [(share, fare) for share, fare in table if fare > 2]
    above_share = sum(share for share, _ in above)
    assert sum(share * fare for share, fare in table) == pytest.approx(2.15, abs=0.03)
    assert above_share == pytest.approx(0.44, abs=0.05)
    assert sum(share * fare for share, fare in above) / above_share == pytest.approx(
        2.73, abs=0.05
    )
    assert saving(2) == pytest.approx(0.32, abs=0.03)


def test_table_matches_january_2025_index_step():
    # BUS0415a outside London rose 11.0% from December 2024 to March 2025,
    # when the cap rose from GBP 2 to GBP 3; neighbouring quarters moved 0.1%
    # to 2.3%. The cap's part, 9% to 11% of the yield at the December 2024
    # index level (1.429858292587 * 185.9 / 190.2282).
    december_yield = 1.429858292587 * 185.9 / 190.2282
    step = SINGLE_SHARE * (saving(2) - saving(3)) / december_yield
    assert 0.09 <= step <= 0.11


def test_table_matches_2023_24_fare_cap_grant():
    # BUS05bi fare cap support for 2023-24, a full year at GBP 2: GBP 278.95m,
    # over 1,390m priced boardings. Fares at 2023-24 prices.
    grant = (
        SINGLE_SHARE
        * PRICED_BOARDINGS_2023_24
        * saving(2, price_ratio=cpi(2023) / cpi(2024))
    )
    assert grant == pytest.approx(278_951_028, rel=0.15)


def test_table_matches_announced_cap_funding():
    # Over GBP 150m for the GBP 3 cap in 2025 (DfT written statement, 29
    # October 2024) and GBP 400m for the GBP 2 cap in 2027 (DfT, 22 July 2026),
    # at the 2024-25 number of priced boardings.
    cap_3 = SINGLE_SHARE * PRICED_BOARDINGS_2024_25 * saving(3, year=2025)
    cap_2 = SINGLE_SHARE * PRICED_BOARDINGS_2024_25 * saving(2, year=2027)
    assert cap_3 == pytest.approx(150e6, rel=0.20)
    assert cap_2 == pytest.approx(400e6, rel=0.20)


def test_removed_reference_year_gives_directions():
    with pytest.raises(ValueError) as error:
        Simulation(
            situation={"people": {"person": {"age": {2025: 30}}}},
            scenario=Scenario(
                parameter_changes={"gov.dft.bus.reference_year": {"2025": 2025}}
            ),
        )
    message = str(error.value)
    assert "gov.dft.bus.reference_year has been removed" in message
    assert "gov.dft.bus.benchmark_year" in message
    assert "gov.dft.bus.fares.cap" in message


def test_removed_uncapped_single_fare_gives_directions():
    with pytest.raises(ValueError) as error:
        Simulation(
            situation={"people": {"person": {"age": {2025: 30}}}},
            scenario=Scenario(
                parameter_changes={"gov.dft.bus.uncapped_single_fare": {"2025": 4}}
            ),
        )
    message = str(error.value)
    assert "gov.dft.bus.uncapped_single_fare has been removed" in message
    assert "gov.dft.bus.uncapped_single_fares" in message
    assert "local_bus_uncapped_single_fare" in message


def test_uncapped_table_matches_fit(pytestconfig):
    # The fit uses published DfT facts and the current OBR CPI path. Changes
    # to those inputs require refitting both shares and fares.
    # CI tests installed wheels from the checkout's pyproject.toml too.
    script = pytestconfig.inipath.parent / "scripts" / "fit_bus_cap_savings.py"
    fit = runpy.run_path(str(script))["fit"]
    _, (shares, fares) = fit()
    for (share, fare), fitted_share, fitted_fare in zip(bands(), shares, fares):
        assert share == pytest.approx(fitted_share, abs=1e-12)
        assert fare == pytest.approx(fitted_fare, abs=1e-12)

"""Real incomes use the prices of gov.simulation.price_base_year (#2875).

``inflation_adjustment`` divides ``consumer_price_index`` on 1 January of the
base year by the index in the period. ``inflation_adjustment_ahc`` divides one
index on 1 January of the base year by the same index in the period. It uses
``consumer_price_index_ahc`` when both dates fall within its modeled coverage
and have index values, and ``consumer_price_index`` on both dates otherwise.
The coverage year excludes the flat values that parameter processing backdates
before the first modeled AHC year. No formula reads the clock,
so a simulation gives the same answers whatever year it runs in.

Invariants:

1. Identity: each adjustment equals 1 when the period equals the base year,
   for every base year from 2009, where the CPI index starts. For
   ``inflation_adjustment_ahc`` that includes base years before 2022.
2. Positivity: each adjustment stays positive wherever the indices have
   values.
3. Rebasing: for any two base years, the ratio of the two adjustments does
   not depend on the period. It holds for ``inflation_adjustment`` from 2009
   and for ``inflation_adjustment_ahc`` across periods and base years from
   2022.
4. Before-housing-costs real incomes use ``inflation_adjustment``. The two
   after-housing-costs real incomes use ``inflation_adjustment_ahc``, including
   its CPI fallback when either date has no AHC index.

The property tests set the base year on a fresh simulation's own parameter
tree, which is faster than a reform; ``test_tree_update_matches_reform``
checks that the two routes agree.
"""

import functools

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import instant

from policyengine_uk import Simulation
from policyengine_uk.system import system

INDICES = system.parameters.gov.economic_assumptions.indices.obr
CPI = INDICES.consumer_price_index
CPI_AHC = INDICES.consumer_price_index_ahc
BASE_YEAR = "gov.simulation.price_base_year"
DEFAULT_BASE_YEAR = 2026

SITUATION = {
    "people": {
        "adult": {"age": {"2026": 40}, "employment_income": {"2026": 30_000}},
    },
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}

# Base years the property tests draw from: the first CPI year, years before
# and within the stretch where the AHC index reads 1, the default, a forecast
# year and a year after the last index value.
BASE_YEARS = [2009, 2014, 2018, 2022, 2026, 2031, 2080]
PERIODS = st.integers(min_value=2009, max_value=2080)

PROPERTY_SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)

REAL_INCOMES = {
    "real_household_net_income": ("household_net_income", "inflation_adjustment"),
    "real_household_net_income_ahc": (
        "household_net_income_ahc",
        "inflation_adjustment_ahc",
    ),
    "real_hbai_household_net_income": (
        "hbai_household_net_income",
        "inflation_adjustment",
    ),
    "real_hbai_household_net_income_ahc": (
        "hbai_household_net_income_ahc",
        "inflation_adjustment_ahc",
    ),
}


def cpi(year):
    return CPI(f"{year}-01-01")


@functools.lru_cache(maxsize=None)
def simulation_at_base_year(base_year):
    """A fresh simulation whose own parameter tree prices to ``base_year``."""
    sim = Simulation(situation=SITUATION)
    sim.tax_benefit_system.parameters.get_child(BASE_YEAR).update(
        start=instant("2000-01-01"), stop=instant("2100-12-31"), value=base_year
    )
    sim.tax_benefit_system._parameters_at_instant_cache.clear()
    return sim


@functools.lru_cache(maxsize=None)
def baseline_simulation():
    return Simulation(situation=SITUATION)


@pytest.fixture(scope="module", autouse=True)
def release_simulations():
    yield
    simulation_at_base_year.cache_clear()
    baseline_simulation.cache_clear()


def adjustment(variable, base_year, period):
    sim = simulation_at_base_year(base_year)
    return float(sim.calculate(variable, period)[0])


# Example tests.


def test_default_base_year():
    parameter = system.parameters.get_child(BASE_YEAR)
    for year in (2009, 2015, 2026, 2027, 2050, 2100):
        assert parameter(f"{year}-01-01") == DEFAULT_BASE_YEAR


@pytest.mark.parametrize(
    "period", [2009, 2014, 2015, 2021, 2022, 2026, 2027, 2030, 2074, 2080]
)
def test_inflation_adjustment_against_cpi(period):
    expected = cpi(DEFAULT_BASE_YEAR) / cpi(period)
    actual = baseline_simulation().calculate("inflation_adjustment", period)
    assert actual[0] == pytest.approx(expected, rel=1e-6)


def test_ahc_adjustment_uses_one_index():
    sim = baseline_simulation()
    start_year = int(
        sim.tax_benefit_system.parameters.get_child(
            "gov.simulation.ahc_price_index_start_year"
        )("2026-01-01")
    )
    for period in (2012, 2015, 2021, 2022, 2027, 2030):
        if period >= start_year and DEFAULT_BASE_YEAR >= start_year:
            expected = CPI_AHC("2026-01-01") / CPI_AHC(f"{period}-01-01")
        else:
            expected = cpi(2026) / cpi(period)
        actual = sim.calculate("inflation_adjustment_ahc", period)[0]
        assert actual == pytest.approx(expected, rel=1e-6)
    # Backdating supplies flat values in 2015 and 2021; those values do not
    # extend the modeled history. CPI also prices both dates for an early base.
    assert CPI_AHC("2012-01-01") is None
    assert CPI_AHC("2015-01-01") == 1
    assert CPI_AHC("2021-01-01") == 1
    for base_year in (2012, 2015, 2021):
        early_base = simulation_at_base_year(base_year)
        actual = early_base.calculate("inflation_adjustment_ahc", 2026)[0]
        assert actual == pytest.approx(cpi(base_year) / cpi(2026), rel=1e-6)


def test_reform_changes_the_base_year():
    # A reform can pass the year as a float.
    reformed = Simulation(
        situation=SITUATION,
        reform={BASE_YEAR: {"2000-01-01.2100-12-31": 2030.0}},
    )
    baseline = baseline_simulation()
    adjustment_2026 = reformed.calculate("inflation_adjustment", 2026)[0]
    assert adjustment_2026 == pytest.approx(cpi(2030) / cpi(2026), rel=1e-6)
    assert reformed.calculate("inflation_adjustment", 2030)[0] == pytest.approx(1)
    assert reformed.calculate("inflation_adjustment_ahc", 2030)[0] == pytest.approx(1)
    assert reformed.calculate("real_household_net_income", 2026)[0] == pytest.approx(
        baseline.calculate("household_net_income", 2026)[0] * cpi(2030) / cpi(2026),
        rel=1e-5,
    )
    assert baseline.calculate("inflation_adjustment", 2026)[0] == pytest.approx(1)


def test_tree_update_matches_reform():
    reformed = Simulation(
        situation=SITUATION,
        reform={BASE_YEAR: {"2000-01-01.2100-12-31": 2031}},
    )
    for variable in ("inflation_adjustment", "inflation_adjustment_ahc"):
        for period in (2012, 2026, 2040):
            assert adjustment(variable, 2031, period) == pytest.approx(
                reformed.calculate(variable, period)[0], rel=1e-7
            )


def test_labels_name_no_year():
    for name in (
        "inflation_adjustment",
        "inflation_adjustment_ahc",
        "real_household_net_income",
        "real_household_net_income_ahc",
    ):
        label = system.variables[name].label
        assert "base-year" in label
        assert not any(char.isdigit() for char in label), label
    assert (
        system.variables["real_household_net_income"].label
        != system.variables["real_household_net_income_ahc"].label
    )


# Property tests.


@PROPERTY_SETTINGS
@given(base_year=st.sampled_from(BASE_YEARS))
def test_identity_in_the_base_year(base_year):
    for variable in ("inflation_adjustment", "inflation_adjustment_ahc"):
        assert adjustment(variable, base_year, base_year) == pytest.approx(1)


@PROPERTY_SETTINGS
@given(base_year=st.sampled_from(BASE_YEARS), period=PERIODS)
def test_positive(base_year, period):
    for variable in ("inflation_adjustment", "inflation_adjustment_ahc"):
        value = adjustment(variable, base_year, period)
        assert np.isfinite(value) and value > 0


@PROPERTY_SETTINGS
@given(
    base_years=st.lists(st.sampled_from(BASE_YEARS), min_size=2, max_size=2),
    periods=st.lists(PERIODS, min_size=2, max_size=2),
)
def test_rebasing_does_not_depend_on_the_period(base_years, periods):
    (b1, b2), (p1, p2) = base_years, periods
    variable = "inflation_adjustment"
    ratio_1 = adjustment(variable, b1, p1) / adjustment(variable, b2, p1)
    ratio_2 = adjustment(variable, b1, p2) / adjustment(variable, b2, p2)
    assert ratio_1 == pytest.approx(ratio_2, rel=1e-6)
    assert ratio_1 == pytest.approx(cpi(b1) / cpi(b2), rel=1e-6)


@PROPERTY_SETTINGS
@given(
    base_years=st.lists(
        st.sampled_from([b for b in BASE_YEARS if b >= 2022]), min_size=2, max_size=2
    ),
    periods=st.lists(st.integers(2022, 2080), min_size=2, max_size=2),
)
def test_ahc_rebasing_does_not_depend_on_the_period(base_years, periods):
    (b1, b2), (p1, p2) = base_years, periods
    variable = "inflation_adjustment_ahc"
    ratio_1 = adjustment(variable, b1, p1) / adjustment(variable, b2, p1)
    ratio_2 = adjustment(variable, b1, p2) / adjustment(variable, b2, p2)
    assert ratio_1 == pytest.approx(ratio_2, rel=1e-6)


@settings(PROPERTY_SETTINGS, max_examples=8)
@given(
    base_year=st.sampled_from(BASE_YEARS),
    period=st.sampled_from([2024, 2026, 2028]),
)
def test_real_income_is_nominal_times_adjustment(base_year, period):
    sim = simulation_at_base_year(base_year)
    for real, (nominal, adjustment_variable) in REAL_INCOMES.items():
        multiplier = sim.calculate(adjustment_variable, period)[0]
        assert sim.calculate(real, period)[0] == pytest.approx(
            sim.calculate(nominal, period)[0] * multiplier, rel=1e-5, abs=0.01
        )


# DWP's HBAI methodology assigns a CPI series excluding rents, maintenance
# repairs and water charges to AHC income (2014/15 methodology, file page 61):
# https://assets.publishing.service.gov.uk/media/5a74abb640f0b61df477785e/households-below-average-income-quality-metholodogy-2014-2015.pdf#page=61
# The current methodology retains bespoke CPI variants:
# https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#adjustment-for-inflation
# These deliberately chosen index levels give exact, independent ratios.
# They are regression inputs, not official historical index observations.
@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize(
    "period,base_year,ahc_levels,cpi_levels,ahc_multiplier,cpi_multiplier",
    [
        pytest.param(
            2024,
            2026,
            {2024: 100, 2026: 120},
            {2024: 100, 2026: 150},
            6 / 5,
            3 / 2,
            id="ahc-forward-rebasing",
        ),
        pytest.param(
            2026,
            2024,
            {2024: 100, 2026: 125},
            {2024: 90, 2026: 100},
            4 / 5,
            9 / 10,
            id="ahc-backward-rebasing",
        ),
        pytest.param(
            2026,
            2026,
            {2026: 120},
            {2026: 150},
            1,
            1,
            id="base-year-identity",
        ),
        pytest.param(
            2012,
            2026,
            {2012: None, 2026: 120},
            {2012: 100, 2026: 150},
            3 / 2,
            3 / 2,
            id="missing-ahc-period-uses-cpi-at-both-dates",
        ),
        pytest.param(
            2026,
            2012,
            {2012: None, 2026: 120},
            {2012: 100, 2026: 150},
            2 / 3,
            2 / 3,
            id="missing-ahc-base-uses-cpi-at-both-dates",
        ),
        pytest.param(
            2012,
            2014,
            {2012: None, 2014: None},
            {2012: 100, 2014: 120},
            6 / 5,
            6 / 5,
            id="both-ahc-dates-missing-use-cpi",
        ),
        pytest.param(
            2015,
            2026,
            {2015: 1, 2026: 120},
            {2015: 100, 2026: 150},
            3 / 2,
            3 / 2,
            id="backdated-2015-period-falls-back-to-cpi",
        ),
        pytest.param(
            2026,
            2015,
            {2015: 1, 2026: 120},
            {2015: 100, 2026: 150},
            2 / 3,
            2 / 3,
            id="backdated-2015-base-falls-back-to-cpi",
        ),
        pytest.param(
            2021,
            2026,
            {2021: 1, 2026: 120},
            {2021: 100, 2026: 150},
            3 / 2,
            3 / 2,
            id="backdated-2021-period-falls-back-to-cpi",
        ),
        pytest.param(
            2026,
            2021,
            {2021: 1, 2026: 120},
            {2021: 100, 2026: 150},
            2 / 3,
            2 / 3,
            id="backdated-2021-base-falls-back-to-cpi",
        ),
        pytest.param(
            2022,
            2026,
            {2022: 1, 2026: 1.2},
            {2022: 100, 2026: 150},
            6 / 5,
            3 / 2,
            id="supported-2022-period-uses-ahc",
        ),
        pytest.param(
            2026,
            2022,
            {2022: 1, 2026: 1.25},
            {2022: 90, 2026: 100},
            4 / 5,
            9 / 10,
            id="supported-2022-base-uses-ahc",
        ),
    ],
)
@pytest.mark.parametrize(
    "hbai_ahc_income,accounting_ahc_income",
    [
        pytest.param(1_200, 600, id="positive-income"),
        pytest.param(-1_200, -600, id="negative-income"),
        pytest.param(0, 0, id="zero-income"),
    ],
)
def test_real_ahc_income_uses_appropriate_price_index(
    period,
    base_year,
    ahc_levels,
    cpi_levels,
    ahc_multiplier,
    cpi_multiplier,
    hbai_ahc_income,
    accounting_ahc_income,
):
    """Price both AHC definitions with the AHC series or its stated fallback."""
    nominal_incomes = {
        "household_net_income": 2_000,
        "hbai_household_net_income": 2_400,
        "household_net_income_ahc": accounting_ahc_income,
        "hbai_household_net_income_ahc": hbai_ahc_income,
    }
    sim = Simulation(
        situation={
            "people": {"adult": {"age": {str(period): 40}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {
                "household": {
                    "members": ["adult"],
                    **{
                        name: {str(period): value}
                        for name, value in nominal_incomes.items()
                    },
                }
            },
        }
    )
    # The module-scoped fixture constructs a clone per Simulation; each case
    # owns its parameter nodes and histories. No cached simulation is reused.
    parameters = sim.tax_benefit_system.parameters
    assert parameters is not system.parameters
    controlled_paths = {
        BASE_YEAR: base_year,
        "gov.economic_assumptions.indices.obr.consumer_price_index": cpi_levels,
        "gov.economic_assumptions.indices.obr.consumer_price_index_ahc": ahc_levels,
    }
    for path, values in controlled_paths.items():
        node = parameters.get_child(path)
        global_node = system.parameters.get_child(path)
        assert node is not global_node
        assert node.values_list is not global_node.values_list
        if path == BASE_YEAR:
            node.update(
                start=instant("2000-01-01"),
                stop=instant("2100-12-31"),
                value=values,
            )
            continue
        for year, level in values.items():
            if level is None:
                assert node(f"{year}-01-01") is None
            else:
                node.update(
                    start=instant(f"{year}-01-01"),
                    stop=instant(f"{year}-12-31"),
                    value=level,
                )
    sim.tax_benefit_system._parameters_at_instant_cache.clear()

    # BHC controls precede the AHC assertion, including on the RED baseline.
    actual_bhc = {
        real: float(sim.calculate(real, period)[0])
        for real in (
            "real_household_net_income",
            "real_hbai_household_net_income",
        )
    }
    expected_bhc = {
        "real_household_net_income": 2_000 * cpi_multiplier,
        "real_hbai_household_net_income": 2_400 * cpi_multiplier,
    }
    assert actual_bhc == pytest.approx(expected_bhc, rel=1e-6, abs=0.01)
    # Calculate both readers before asserting, so the baseline observes both.
    actual_ahc = {
        real: float(sim.calculate(real, period)[0])
        for real in (
            "real_household_net_income_ahc",
            "real_hbai_household_net_income_ahc",
        )
    }
    expected_ahc = {
        "real_household_net_income_ahc": accounting_ahc_income * ahc_multiplier,
        "real_hbai_household_net_income_ahc": hbai_ahc_income * ahc_multiplier,
    }
    assert actual_ahc == pytest.approx(expected_ahc, rel=1e-6, abs=0.01)


def test_ahc_coverage_year_matches_first_stored_growth_year():
    """Keep model coverage tied to the raw AHC series, before backdating."""
    from pathlib import Path

    import yaml

    package_root = Path(__file__).resolve().parents[1]
    growth_path = package_root / "parameters/gov/economic_assumptions/yoy_growth.yaml"
    coverage_path = (
        package_root / "parameters/gov/simulation/ahc_price_index_start_year.yaml"
    )
    # BaseLoader leaves date keys as strings, including the timeless year 0000.
    growth = yaml.load(growth_path.read_text(), Loader=yaml.BaseLoader)
    coverage = yaml.load(coverage_path.read_text(), Loader=yaml.BaseLoader)
    dates = growth["obr"]["consumer_price_index_ahc"]["values"]
    first_stored_year = min(int(date[:4]) for date in dates)
    assert first_stored_year == 2022
    assert {int(value) for value in coverage["values"].values()} == {first_stored_year}
    assert (
        system.parameters.get_child("gov.simulation.ahc_price_index_start_year")(
            "2026-01-01"
        )
        == first_stored_year
    )


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize(
    "coverage_start_year,period,base_year,ahc_multiplier,cpi_multiplier",
    [
        pytest.param(2022, 2024, 2026, 6 / 5, 3 / 2, id="supported-period"),
        pytest.param(2025, 2024, 2026, 3 / 2, 3 / 2, id="override-excludes-period"),
        pytest.param(2022, 2026, 2024, 5 / 6, 2 / 3, id="supported-base"),
        pytest.param(2025, 2026, 2024, 2 / 3, 2 / 3, id="override-excludes-base"),
    ],
)
def test_ahc_coverage_parameter_selects_one_index(
    coverage_start_year, period, base_year, ahc_multiplier, cpi_multiplier
):
    """An explicit coverage override selects CPI for either unsupported date."""
    sim = Simulation(situation=SITUATION)
    parameters = sim.tax_benefit_system.parameters
    assert parameters is not system.parameters
    values_by_path = {
        BASE_YEAR: {2024: base_year, 2026: base_year},
        "gov.simulation.ahc_price_index_start_year": {
            2024: coverage_start_year,
            2026: coverage_start_year,
        },
        "gov.economic_assumptions.indices.obr.consumer_price_index": {
            2024: 100,
            2026: 150,
        },
        "gov.economic_assumptions.indices.obr.consumer_price_index_ahc": {
            2024: 100,
            2026: 120,
        },
    }
    for path, values in values_by_path.items():
        node = parameters.get_child(path)
        global_node = system.parameters.get_child(path)
        assert node is not global_node
        assert node.values_list is not global_node.values_list
        for year, value in values.items():
            node.update(
                start=instant(f"{year}-01-01"),
                stop=instant(f"{year}-12-31"),
                value=value,
            )
    sim.tax_benefit_system._parameters_at_instant_cache.clear()
    # Both raw AHC values remain present, so only the coverage choice changes.
    assert sim.calculate("inflation_adjustment", period)[0] == pytest.approx(
        cpi_multiplier, rel=1e-6
    )
    assert sim.calculate("inflation_adjustment_ahc", period)[0] == pytest.approx(
        ahc_multiplier, rel=1e-6
    )

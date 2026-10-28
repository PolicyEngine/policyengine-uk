"""Properties of the household energy price indices.

``add_energy_price_indices`` builds them from the published inputs under
``gov.economic_assumptions.energy_prices``. These tests run it on the
statutory parameters, alone or with changed inputs; the changed inputs are
test data, not forecasts.

Invariants:

1. Every index covers 2015 to 2041 (quarterly to the first quarter of 2042)
   with finite, positive levels, and generation is deterministic.
2. Outturn: a quarter ONS publishes in full is the mean of its monthly index,
   each month divided by the published-over-basis VAT factor for that series.
3. Forecast: re-applying the published VAT to an index's year-on-year growth
   gives the OBR's utilities inflation (the round trip of the adjustment), and
   with no VAT change the growth is the OBR's exactly.
4. Annual levels are the consumption-weighted means of their quarters:
   January to December for calendar years, April to March for fiscal years.
5. A change to statutory VAT never moves the indices, the projected dataset
   amounts or a direct situation's uprated amounts.
6. Higher OBR growth in one forecast quarter raises that quarter and the same
   quarter of each later year, and nothing else.
7. ``held_flat`` from a year holds the annual levels at the year before.
8. Inputs are read at each month and quarter, so a reform that states one
   value for a year or a span of quarters sets each month or quarter in it,
   and the outturn ends at ``last_full_quarter`` whatever a reform states.
"""

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    DECLARED_ENERGY_INPUTS,
    ENERGY_PRICE_SERIES,
    ENERGY_PRICES,
    extend_single_year_dataset,
    uprate_energy,
)
from policyengine_uk.parameters.gov.economic_assumptions import (
    create_energy_price_indices as indices,
)
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import statutory_parameters
from policyengine_uk.utils.scenario import Scenario

SERIES = tuple(indices.SERIES)
FIRST, LAST = indices.FIRST_YEAR, indices.LAST_YEAR
QUARTERS = indices._quarters((FIRST, 1), (LAST + 1, 1))
OUTTURN = indices._quarters((FIRST, 1), (2026, 3))
FORECAST = indices._quarters((2026, 4), (LAST + 1, 1))
BASIS = 0.05
ENERGY = tuple(sorted(DECLARED_ENERGY_INPUTS))
GB_RATE = "gov.hmrc.vat.domestic_electricity_rate.great_britain"
NI_RATE = "gov.hmrc.vat.domestic_electricity_rate.northern_ireland"
REDUCED_RATE = "gov.hmrc.vat.reduced_rate"


@pytest.fixture(scope="module")
def raw():
    return statutory_parameters()


def prices_of(tree):
    return tree.gov.economic_assumptions.energy_prices


def build(raw, edit=None):
    """The generated indices for a copy of ``raw``, after ``edit(copy)``."""
    tree = raw.clone()
    if edit is not None:
        edit(tree)
    indices.add_energy_price_indices(tree)
    return prices_of(tree)


def levels(prices, kind, key):
    parameter = prices.get_child(kind).get_child(key)
    return {entry.instant_str: entry.value for entry in parameter.values_list}


def quarter_level(prices, key, quarter):
    return levels(prices, "quarterly", key)[indices._start(quarter)]


@pytest.fixture(scope="module")
def current(raw):
    return build(raw)


def electricity_share(raw, key, year):
    """Electricity's share of a series' CPI weight, from the ONS weights."""
    if key == "electricity":
        return 1.0
    if key == "gas":
        return 0.0
    weights = prices_of(raw).ons.weights
    instant = f"{year}-01-01"
    return weights.electricity(instant) / weights.get_child(key)(instant)


def published_rate(raw, year, month):
    vat = prices_of(raw).embedded_electricity_vat
    day = f"{year:04d}-{month:02d}-15"
    ni = vat.northern_ireland_share(day)
    return (1 - ni) * vat.great_britain(day) + ni * vat.northern_ireland(day)


def utilities_factor(raw, quarter):
    """Published utilities price over its price with VAT at the basis rate."""
    weights = prices_of(raw).ons.weights
    instant = f"{quarter[0]}-01-01"
    share = weights.electricity(instant) / (
        weights.electricity(instant) + weights.gas(instant)
    )
    electricity = np.mean(
        [(1 + published_rate(raw, *m)) / (1 + BASIS) for m in indices._months(quarter)]
    )
    return 1 + share * (electricity - 1)


# 1. Coverage, positivity, determinism.


@pytest.mark.parametrize("key", SERIES)
def test_indices_cover_every_year_and_quarter_with_positive_levels(current, key):
    quarterly = levels(current, "quarterly", key)
    assert sorted(quarterly) == [indices._start(q) for q in QUARTERS]
    assert all(math.isfinite(v) and v > 0 for v in quarterly.values())
    for kind in ("calendar_year", "fiscal_year"):
        annual = levels(current, kind, key)
        assert sorted(annual) == [f"{y}-01-01" for y in range(FIRST, LAST + 1)]
        assert all(math.isfinite(v) and v > 0 for v in annual.values())


def test_generation_is_deterministic(raw, current):
    again = build(raw)
    for key in SERIES:
        for kind in ("quarterly", "calendar_year", "fiscal_year"):
            assert levels(again, kind, key) == levels(current, kind, key)


def test_the_processed_system_reads_the_generated_levels_at_their_dates(current):
    processed = system.parameters.gov.economic_assumptions.energy_prices
    for key in SERIES:
        for kind in ("quarterly", "calendar_year", "fiscal_year"):
            parameter = processed.get_child(kind).get_child(key)
            assert parameter.metadata["preserve_calendar_dates"]
            for instant, value in levels(current, kind, key).items():
                assert parameter(instant) == value


def test_energy_variables_uprate_by_the_fiscal_year_index_of_their_fuel():
    for variable, key in ENERGY_PRICE_SERIES.items():
        assert system.variables[variable].uprating == (
            f"{ENERGY_PRICES}.fiscal_year.{key}"
        )
    assert set(ENERGY_PRICE_SERIES) == DECLARED_ENERGY_INPUTS
    assert set(ENERGY_PRICE_SERIES.values()) == set(SERIES)


# 2. Outturn.


def ons_mean(raw, key, quarter, divide=lambda year, month: 1.0):
    ons = prices_of(raw).ons.get_child(key)
    return np.mean(
        [ons(f"{y:04d}-{m:02d}-15") / divide(y, m) for y, m in indices._months(quarter)]
    )


@pytest.mark.parametrize("key", SERIES)
def test_outturn_is_ons_where_the_published_vat_is_the_basis_rate(raw, current, key):
    # Every published price to September 2026 includes VAT at 5%.
    for quarter in OUTTURN:
        assert quarter_level(current, key, quarter) == pytest.approx(
            ons_mean(raw, key, quarter), rel=1e-12
        )


@settings(max_examples=30, deadline=None, derandomize=True)
@given(
    year=st.integers(2015, 2025),
    month=st.integers(1, 12),
    rate=st.sampled_from([0.0, 0.02, 0.2]),
    ni_too=st.booleans(),
)
def test_outturn_divides_out_a_published_vat_change(raw, year, month, rate, ni_too):
    period = f"month:{year:04d}-{month:02d}"

    def edit(tree):
        vat = prices_of(tree).embedded_electricity_vat
        vat.great_britain.update(period=period, value=rate)
        if ni_too:
            vat.northern_ireland.update(period=period, value=rate)

    changed = build(raw, edit)
    ni = (
        0.0
        if ni_too
        else prices_of(raw).embedded_electricity_vat.northern_ireland_share(
            "2024-01-01"
        )
    )
    published = (1 - ni) * rate + ni * BASIS
    quarter = (year, (month + 2) // 3)
    for key in SERIES:
        share = electricity_share(raw, key, year)

        def divide(y, m):
            if (y, m) != (year, month):
                return 1.0
            return 1 + share * ((1 + published) / (1 + BASIS) - 1)

        assert quarter_level(changed, key, quarter) == pytest.approx(
            ons_mean(raw, key, quarter, divide), rel=1e-12
        )


# 3. Forecast.


@pytest.mark.parametrize("key", SERIES)
def test_reapplying_the_published_vat_gives_the_obr_forecast(raw, current, key):
    utilities = prices_of(raw).obr.utilities
    last = max(entry.instant_str for entry in utilities.values_list)
    for quarter in FORECAST:
        earlier = (quarter[0] - 1, quarter[1])
        growth = quarter_level(current, key, quarter) / quarter_level(
            current, key, earlier
        )
        published = (
            growth * utilities_factor(raw, quarter) / utilities_factor(raw, earlier)
        )
        obr = utilities(min(indices._start(quarter), last))
        assert published - 1 == pytest.approx(obr, abs=1e-12), quarter


def test_the_vat_cut_quarters_are_the_ones_adjusted(raw, current):
    # Hand-computed for 2027Q1: Great Britain zero-rated, Northern Ireland at
    # 5% (its relief starts in April 2027), 2026Q1 all at 5%. Weights:
    # ONS 2026 CPI weights CJXA 20.6065 and CJXB 10.3002; DESNZ 2024 NI share.
    share = 20.6065 / (20.6065 + 10.3002)
    published = (1 - 0.0269) * 0 + 0.0269 * 0.05
    factor = 1 + share * ((1 + published) / 1.05 - 1)
    expected = (1 + 0.113241) / factor - 1
    for key in SERIES:
        growth = quarter_level(current, key, (2027, 1)) / quarter_level(
            current, key, (2026, 1)
        )
        assert growth - 1 == pytest.approx(expected, abs=1e-12)
    # 2028Q3 compares two quarters at 5%: the OBR's rate as published.
    growth = quarter_level(current, "gas", (2028, 3)) / quarter_level(
        current, "gas", (2027, 3)
    )
    assert growth - 1 == pytest.approx(-0.070888, abs=1e-12)


@pytest.mark.parametrize("key", SERIES)
def test_without_a_published_vat_change_growth_is_the_obr_forecast(raw, key):
    def edit(tree):
        vat = prices_of(tree).embedded_electricity_vat
        for rate in (vat.great_britain, vat.northern_ireland):
            rate.update(start="2026-01-01", value=BASIS)

    unchanged = build(raw, edit)
    utilities = prices_of(raw).obr.utilities
    for quarter in indices._quarters((2026, 4), (2032, 1)):
        earlier = (quarter[0] - 1, quarter[1])
        growth = quarter_level(unchanged, key, quarter) / quarter_level(
            unchanged, key, earlier
        )
        assert growth - 1 == pytest.approx(
            utilities(indices._start(quarter)), abs=1e-12
        )


@settings(max_examples=25, deadline=None, derandomize=True)
@given(
    position=st.integers(0, len(indices._quarters((2026, 4), (2032, 1))) - 1),
    delta=st.sampled_from([1e-4, 0.01, 0.2]),
)
def test_higher_obr_growth_raises_only_its_quarter_of_each_later_year(
    raw, current, position, delta
):
    forecast = indices._quarters((2026, 4), (2032, 1))
    quarter = forecast[position]
    start = indices._start(quarter)

    def edit(tree):
        utilities = prices_of(tree).obr.utilities
        value = utilities(start)
        if quarter == forecast[-1]:
            utilities.update(start=start, value=value + delta)
        else:
            utilities.update(period=f"month:{start[:7]}:3", value=value + delta)

    changed = build(raw, edit)
    for key in SERIES:
        for q in QUARTERS:
            before = quarter_level(current, key, q)
            after = quarter_level(changed, key, q)
            # The last forecast rate also holds for every quarter after it.
            if q >= quarter and (q[1] == quarter[1] or quarter == forecast[-1]):
                assert after > before, (key, q)
            else:
                assert after == before, (key, q)


def test_a_forecast_that_starts_after_the_outturn_ends_is_an_error(raw):
    def edit(tree):
        utilities = prices_of(tree).obr.utilities
        utilities.update(period="month:2026-10:3", value=None)

    with pytest.raises(ValueError, match="OBR utilities forecast starts in 2027Q1"):
        build(raw, edit)


def test_the_ons_prices_state_every_month_to_the_last_full_quarter(raw):
    # The generator reads each month's effective price, so a month missing
    # from the file would silently take the month before's.
    inputs = indices.EnergyPriceInputs(raw.clone())
    assert inputs.last_outturn == OUTTURN[-1]
    months = {
        f"{year:04d}-{month:02d}-01"
        for quarter in OUTTURN
        for year, month in indices._months(quarter)
    }
    for key in SERIES:
        assert months <= set(indices._stated(prices_of(raw).ons.get_child(key))), key


@pytest.mark.parametrize("value", [None, "2026-07", "2026Q5"])
def test_the_last_full_quarter_must_be_stated(raw, value):
    def edit(tree):
        metadata = prices_of(tree).ons.metadata
        if value is None:
            del metadata["last_full_quarter"]
        else:
            metadata["last_full_quarter"] = value

    with pytest.raises(ValueError, match="last_full_quarter"):
        build(raw, edit)


def test_ons_prices_that_end_before_the_last_full_quarter_are_an_error(raw):
    def edit(tree):
        prices_of(tree).ons.gas.update(start="2026-09-01", value=None)

    with pytest.raises(ValueError, match="gas prices end in 2026-08"):
        build(raw, edit)


def test_a_gap_in_the_ons_prices_is_an_error(raw):
    def edit(tree):
        prices_of(tree).ons.gas.update(period="month:2020-05", value=None)

    with pytest.raises(ValueError, match="gas prices have no value for 2020-05"):
        build(raw, edit)


# 4. Annual levels.


@pytest.mark.parametrize("key", SERIES)
def test_annual_levels_are_consumption_weighted_quarterly_means(raw, current, key):
    inputs = indices.EnergyPriceInputs(raw.clone())
    quarterly = {q: quarter_level(current, key, q) for q in QUARTERS}
    for year in range(FIRST, LAST + 1):
        shares = inputs.consumption_shares(key, year)
        assert sum(shares) == pytest.approx(1, abs=1e-15)
        calendar = [quarterly[(year, n)] for n in range(1, 5)]
        fiscal = [quarterly[(year + 1, 1)]] + calendar[1:]
        for kind, quarters in (("calendar_year", calendar), ("fiscal_year", fiscal)):
            assert levels(current, kind, key)[f"{year}-01-01"] == pytest.approx(
                np.dot(shares, quarters), rel=1e-12
            )


def test_combined_seasonal_shares_weight_the_fuels_by_cpi_weight(raw):
    inputs = indices.EnergyPriceInputs(raw.clone())
    electricity = inputs.consumption_shares("electricity", 2026)
    gas = inputs.consumption_shares("gas", 2026)
    combined = inputs.consumption_shares("electricity_gas_and_solid_fuels", 2026)
    weight = 20.6065 / (20.6065 + 10.3002)
    for e, g, c in zip(electricity, gas, combined):
        assert c == pytest.approx(weight * e + (1 - weight) * g, rel=1e-12)
    # The DESNZ 2015-2025 means: winter quarters weigh most, gas far more so.
    assert electricity == pytest.approx([0.2929, 0.2242, 0.2051, 0.2778], abs=1e-12)
    assert gas == pytest.approx([0.4250, 0.1642, 0.0799, 0.3309], abs=1e-12)


@settings(max_examples=30, deadline=None, derandomize=True)
@given(year=st.integers(2016, 2024), month=st.integers(1, 12))
def test_a_month_moves_its_calendar_year_and_the_fiscal_year_it_falls_in(
    raw, current, year, month
):
    def edit(tree):
        gas = prices_of(tree).ons.gas
        gas.update(
            period=f"month:{year:04d}-{month:02d}",
            value=gas(f"{year:04d}-{month:02d}-15") * 1.5,
        )

    changed = build(raw, edit)
    fiscal_year = year if month >= 4 else year - 1
    for kind, moved in (("calendar_year", year), ("fiscal_year", fiscal_year)):
        before, after = levels(current, kind, "gas"), levels(changed, kind, "gas")
        for y in range(FIRST, 2025):
            if y == moved:
                assert after[f"{y}-01-01"] > before[f"{y}-01-01"], (kind, y)
            else:
                assert after[f"{y}-01-01"] == before[f"{y}-01-01"], (kind, y)


@settings(max_examples=20, deadline=None, derandomize=True)
@given(start=st.integers(FIRST + 1, LAST))
def test_held_flat_holds_the_annual_levels_at_the_year_before(raw, current, start):
    def edit(tree):
        prices_of(tree).held_flat.update(start=f"{start}-01-01", value=True)

    held = build(raw, edit)
    for key in SERIES:
        assert levels(held, "quarterly", key) == levels(current, "quarterly", key)
        for kind in ("calendar_year", "fiscal_year"):
            before, after = levels(current, kind, key), levels(held, kind, key)
            for year in range(FIRST, LAST + 1):
                instant = f"{year}-01-01"
                if year < start:
                    assert after[instant] == before[instant]
                else:
                    assert after[instant] == before[f"{start - 1}-01-01"]


# 5. VAT reforms move neither the indices nor projected spending.

VAT_PATHS = (GB_RATE, NI_RATE, REDUCED_RATE)


@settings(max_examples=40, deadline=None, derandomize=True)
@given(
    path=st.sampled_from(VAT_PATHS),
    year=st.integers(2015, 2040),
    month=st.integers(1, 12),
    months=st.integers(1, 60),
    rate=st.sampled_from([0.0, 0.025, 0.05, 0.2]),
)
def test_statutory_vat_changes_never_move_the_indices(
    raw, current, path, year, month, months, rate
):
    def edit(tree):
        tree.get_child(path).update(
            period=f"month:{year:04d}-{month:02d}:{months}", value=rate
        )

    changed = build(raw, edit)
    for key in SERIES:
        for kind in ("quarterly", "calendar_year", "fiscal_year"):
            assert levels(changed, kind, key) == levels(current, kind, key)


def energy_dataset(basis):
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [40, 50],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "region": ["LONDON", "NORTHERN_IRELAND"],
                "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
                "council_tax": [0.0, 0.0],
                "rent": [0.0, 0.0],
                "household_weight": [1.0, 2.0],
                "domestic_energy_consumption": [1_800.0, 900.0],
                "electricity_consumption": [1_200.0, 600.0],
                "gas_consumption": [600.0, 300.0],
            }
        ),
        fiscal_year=2025,
        energy_price_basis=basis,
    )


def situation():
    return {
        "people": {"person": {"age": {2025: 40}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "region": {2025: "LONDON"},
                "electricity_consumption": {2025: 1_200.0},
                "gas_consumption": {2025: 600.0},
                "domestic_energy_consumption": {2025: 1_800.0},
            }
        },
    }


VAT_REFORMS = {
    "no electricity VAT from 2027": {GB_RATE: {"2027-04-06.2033-04-05": 0.0}},
    "20% in Northern Ireland": {NI_RATE: {"2026-04-06.2033-04-05": 0.2}},
    "reduced rate at 8%": {REDUCED_RATE: {"2026-04-06.2033-04-05": 0.08}},
}


@pytest.fixture(scope="module")
def baseline_runs():
    basis = {"period_type": "calendar_year", "period_value": 2025}
    return (
        Simulation(dataset=energy_dataset(basis)),
        Simulation(situation=situation()),
    )


@pytest.mark.parametrize("reform", list(VAT_REFORMS), ids=list(VAT_REFORMS))
def test_vat_reforms_leave_projected_energy_spending_unchanged(baseline_runs, reform):
    basis = {"period_type": "calendar_year", "period_value": 2025}
    data_baseline, situation_baseline = baseline_runs
    data = Simulation(dataset=energy_dataset(basis), reform=VAT_REFORMS[reform])
    direct = Simulation(situation=situation(), reform=VAT_REFORMS[reform])
    vat_moved = False
    for year in range(2026, 2033):
        for variable in ENERGY:
            np.testing.assert_array_equal(
                data.calculate(variable, year),
                data_baseline.calculate(variable, year),
            )
            np.testing.assert_array_equal(
                direct.calculate(variable, year),
                situation_baseline.calculate(variable, year),
            )
        vat_moved |= not np.array_equal(
            data.calculate("domestic_energy_vat", year),
            data_baseline.calculate("domestic_energy_vat", year),
        )
    # Not vacuous: the reform does change the VAT charged on that spending.
    assert vat_moved


# 6. The dataset projection and Core's variable uprating agree.


@pytest.mark.parametrize("target", range(2026, 2033))
def test_core_uprating_matches_the_dataset_projection(target):
    basis = {"period_type": "fiscal_year", "period_value": 2025}
    observed = energy_dataset(basis)
    projected = observed.copy()
    projected.time_period = str(target)
    uprate_energy(projected, observed, system.parameters)
    direct = Simulation(situation=situation())
    for variable in ENERGY:
        np.testing.assert_allclose(
            direct.calculate(variable, target)[0],
            projected.household[variable].to_numpy()[0],
            rtol=1e-6,
        )


def test_calendar_and_fiscal_bases_read_their_own_index():
    calendar = {"period_type": "calendar_year", "period_value": 2025}
    fiscal = {"period_type": "fiscal_year", "period_value": 2025}
    prices = system.parameters.gov.economic_assumptions.energy_prices
    for basis, kind in ((calendar, "calendar_year"), (fiscal, "fiscal_year")):
        projected = extend_single_year_dataset(
            energy_dataset(basis), system.parameters, end_year=2028
        )
        for variable, key in ENERGY_PRICE_SERIES.items():
            ratio = prices.fiscal_year.get_child(key)("2028-01-01") / prices.get_child(
                kind
            ).get_child(key)("2025-01-01")
            np.testing.assert_allclose(
                projected[2028].household[variable],
                energy_dataset(basis).household[variable] * ratio,
                rtol=1e-12,
            )


# 7. No economic assumptions.


@pytest.mark.parametrize(
    "scenario",
    [
        "freeze",
        "freeze then reform",
        "reform then freeze",
    ],
)
def test_no_economic_assumptions_holds_direct_energy_amounts_flat(scenario):
    reform = Scenario.from_reform(
        {"gov.hmrc.income_tax.allowances.personal_allowance.amount": {"2027": 15_000}}
    )
    chosen = {
        "freeze": no_economic_assumptions,
        "freeze then reform": no_economic_assumptions + reform,
        "reform then freeze": reform + no_economic_assumptions,
    }[scenario]
    simulation = Simulation(situation=situation(), scenario=chosen)
    for year in range(2025, 2033):
        for variable in ENERGY:
            np.testing.assert_allclose(
                simulation.calculate(variable, year),
                simulation.calculate(variable, 2025),
                rtol=1e-12,
            )
    held = simulation.tax_benefit_system.parameters.gov.economic_assumptions
    fiscal = held.energy_prices.fiscal_year.electricity
    assert fiscal("2030-01-01") == fiscal("2024-01-01")
    current = system.parameters.gov.economic_assumptions.energy_prices
    assert fiscal("2023-01-01") == current.fiscal_year.electricity("2023-01-01")


# 8. Reforms to the inputs.


def realised_obr_rate(raw, level, quarter):
    """Growth in a forecast quarter with the published VAT re-applied."""
    earlier = (quarter[0] - 1, quarter[1])
    growth = level(quarter) / level(earlier)
    return growth * utilities_factor(raw, quarter) / utilities_factor(raw, earlier) - 1


@settings(max_examples=30, deadline=None, derandomize=True)
@given(
    first=st.integers(2026, 2034),
    span=st.integers(1, 6),
    rate=st.floats(-0.3, 0.6, allow_nan=False, allow_infinity=False),
    by_year=st.booleans(),
)
def test_a_forecast_reform_sets_the_rate_of_every_quarter_it_covers(
    raw, current, first, span, rate, by_year
):
    # One stated value for whole years, as a reform keyed by year leaves, or
    # for a span of quarters from a fourth quarter, across the year end;
    # either removes the stated values of the quarters inside it.
    if by_year:
        years = min(span, 3)
        period = f"year:{first}:{years}"
        covered = indices._quarters((first, 1), (first + years - 1, 4))
    else:
        period = f"month:{first}-10:{3 * span}"
        covered = indices._quarters((first, 4), (first + 2, 4))[:span]

    def edit(tree):
        prices_of(tree).obr.utilities.update(period=period, value=rate)

    changed = build(raw, edit)
    effective = changed.obr.utilities
    covered = [quarter for quarter in covered if quarter in FORECAST]
    assert covered
    for key in SERIES:
        for quarter in OUTTURN:
            assert quarter_level(changed, key, quarter) == quarter_level(
                current, key, quarter
            )
        for quarter in FORECAST:
            expected = effective(indices._start(quarter))
            if quarter in covered:
                assert expected == rate
            assert realised_obr_rate(
                raw, lambda q: quarter_level(changed, key, q), quarter
            ) == pytest.approx(expected, abs=1e-9), (key, quarter)


def test_a_year_keyed_forecast_reform_builds_a_simulation(raw):
    # Regression: one stated value for 2027 used to leave the generator
    # without a rate for 2027Q2 to 2027Q4.
    reform = {f"{ENERGY_PRICES}.obr.utilities": {"2027": 0.5}}
    reformed = Simulation(situation=situation(), reform=reform)
    baseline = Simulation(situation=situation())
    prices = reformed.tax_benefit_system.parameters.gov.economic_assumptions
    quarterly = prices.energy_prices.quarterly
    for key in SERIES:
        level = quarterly.get_child(key)
        for quarter in indices._quarters((2027, 1), (2027, 4)):
            assert realised_obr_rate(
                raw, lambda q: level(indices._start(q)), quarter
            ) == pytest.approx(0.5, abs=1e-9), (key, quarter)
    for variable in ENERGY:
        assert (
            reformed.calculate(variable, 2027)[0]
            > baseline.calculate(variable, 2027)[0]
        )


@pytest.mark.parametrize("year", [2025, 2026])
def test_a_year_keyed_ons_reform_sets_each_month_of_the_year(raw, current, year):
    def edit(tree):
        prices_of(tree).ons.electricity.update(period=f"year:{year}:1", value=130.0)

    changed = build(raw, edit)
    outturn = [quarter for quarter in OUTTURN if quarter[0] == year]
    for quarter in outturn:
        # Published VAT is the basis rate in these quarters.
        assert quarter_level(changed, "electricity", quarter) == pytest.approx(
            130.0, rel=1e-12
        )
    # The forecast still starts after 2026Q3, though the reform states a
    # value for 2027 (the September 2026 price, after the year it sets).
    for quarter in FORECAST:
        earlier = (quarter[0] - 1, quarter[1])
        assert quarter_level(changed, "gas", quarter) == quarter_level(
            current, "gas", quarter
        )
        assert quarter_level(changed, "electricity", quarter) / quarter_level(
            changed, "electricity", earlier
        ) == pytest.approx(
            quarter_level(current, "electricity", quarter)
            / quarter_level(current, "electricity", earlier),
            rel=1e-12,
        )

"""Projected State Pension weekly rates are rounded as each Up-rating Order
rounds them.

DWP applies the review's percentage to the current full weekly rates of the
basic and new State Pensions and rounds the results to the nearest 5p
(written answer HL10770, 20 October 2025; Explanatory Memorandum to SI
2020/234, paragraph 7.17), and HM Treasury's forecast baseline projects both
the same way (Budget 2026 policy costings, Annex A, page 114). The model
projects each year after the last published rate from the year before
(``create_rate_projection``).

Invariants, for both rates:

1. Published rates are untouched: every stated rate is the parameter file's.
2. Grid: every projected rate is a whole number of 5p.
3. Chain: each projected year is the previous year's rate raised by that
   April's triple lock rate, to the nearest 5p, so within 2.5p of the
   unrounded product.
4. Differential: April 2027 gives the £13,036.40 a year of HM Treasury's
   Pension Tax Allowance explainer (52 weeks at £250.70), and the £93.28 of
   tax it says that income would otherwise bear.
5. A pensioner whose only income is the full new State Pension has total
   income of 52 weeks at the projected rate, the explainer's Pension Tax
   Allowance threshold, in 2027-28 to 2029-30 (to the float32 precision
   simulations hold).
6. The rounding is a parameter: each reform route moves the projection by
   it, zero gives the unrounded chain, and the baseline stays current law.
   A rate a reform states for a year stays as stated.
7. A changed triple lock rate or index moves the projection, at full
   precision: a half rounds up (£273.675 to £273.70).
8. Properties (Hypothesis): rounding lands on the grid, within half a unit,
   idempotently and monotonically; a projected path is the chained rule for
   any rates; a rise never lowers the rate.
"""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd
import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.state_pension.create_rate_projection import (
    project_weekly_rate,
    round_weekly_rate,
    uprate_weekly_rate,
)
from policyengine_uk.system import system

PARAMETERS = Path(__file__).parents[1] / "parameters"
STATE_PENSION = "gov.dwp.state_pension"
ROUNDING = f"{STATE_PENSION}.weekly_rate_rounding"
TRIPLE_LOCK = "gov.economic_assumptions.yoy_growth.triple_lock"
TRIPLE_LOCK_INDEX = "gov.economic_assumptions.indices.triple_lock"
RATES = {
    "new": f"{STATE_PENSION}.new_state_pension.amount",
    "basic": f"{STATE_PENSION}.basic_state_pension.amount",
}
LAST_PUBLISHED = 2026
# The uprating index runs to 2039; later years are held at its last value.
PROJECTED = range(LAST_PUBLISHED + 1, 2040)
FIVE_PENCE = Decimal("0.05")
WEEKS_IN_YEAR = 52
# Simulations hold float32, which at £13,000 resolves about a tenth of a
# penny; the unrounded rates put these incomes 57p to £1.86 off.
HALF_PENNY = 0.005

PROPERTY_SETTINGS = settings(
    max_examples=200,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def weekly(parameters, path, year):
    """A rate in force over fiscal year ``year`` (the 30 April value)."""
    return float(parameters.get_child(path)(f"{year}-04-30"))


def triple_lock(parameters, year):
    return float(parameters.get_child(TRIPLE_LOCK)(f"{year}-01-01"))


def nearest(amount, unit=FIVE_PENCE):
    return (Decimal(amount) / unit).quantize(Decimal(1), ROUND_HALF_UP) * unit


def uprated(previous, rate, unit=FIVE_PENCE):
    """The rule, written independently of the model's implementation."""
    return float(
        nearest(Decimal(repr(float(previous))) * (1 + Decimal(repr(float(rate)))), unit)
    )


def on_grid(amount, unit=FIVE_PENCE):
    return Decimal(repr(float(amount))) % unit == 0


def stated_values(path):
    file = PARAMETERS.joinpath(*path.split(".")).with_suffix(".yaml")
    return yaml.safe_load(file.read_text())["values"]


# 1-3. Published rates, the grid and the chain.


@pytest.mark.parametrize("scheme", RATES)
def test_published_rates_are_the_parameter_files(scheme):
    stated = stated_values(RATES[scheme])
    amount = system.parameters.get_child(RATES[scheme])
    for date, value in stated.items():
        assert float(amount(f"{date}")) == pytest.approx(value, abs=1e-12), date


@pytest.mark.parametrize("scheme", RATES)
def test_every_projected_rate_is_a_whole_number_of_5p(scheme):
    for year in PROJECTED:
        rate = weekly(system.parameters, RATES[scheme], year)
        assert on_grid(rate), (year, rate)


@pytest.mark.parametrize("scheme", RATES)
def test_each_projected_year_is_the_year_before_uprated_to_the_nearest_5p(scheme):
    parameters = system.parameters
    path = RATES[scheme]
    for year in PROJECTED:
        previous = weekly(parameters, path, year - 1)
        rise = triple_lock(parameters, year)
        rate = weekly(parameters, path, year)
        assert rate == pytest.approx(uprated(previous, rise), abs=1e-12), year
        assert abs(rate - previous * (1 + rise)) <= 0.025 + 1e-9, year


@pytest.mark.parametrize(
    "scheme, expected",
    [
        # 2027 to 2029: £241.30 x 1.039 = £250.7107, then x 1.034 =
        # £259.2238 (where the unrounded path, £259.2357, would round to
        # £259.25), then x 1.025 = £265.68.
        ("new", [250.70, 259.20, 265.70]),
        ("basic", [192.10, 198.65, 203.60]),
    ],
)
def test_rates_on_the_october_2026_forecast(scheme, expected):
    """The triple lock is 3.9%, 3.4% and 2.5% for April 2027 to 2029 on the
    stored forecast. For April 2027 the statutory review (HCWS427, 28 October
    2026) confirmed 3.9%, "around £490" a year on the full new State Pension
    (52 x £9.40 = £488.80) and "around £375" on the basic (52 x £7.20 =
    £374.40)."""
    rises = [triple_lock(system.parameters, year) for year in (2027, 2028, 2029)]
    assert rises == pytest.approx([0.039, 0.034, 0.025])
    rates = [weekly(system.parameters, RATES[scheme], y) for y in (2027, 2028, 2029)]
    assert rates == pytest.approx(expected, abs=1e-12)


# 4-5. The full new State Pension against the Pension Tax Allowance
# explainer.


def full_new_state_pension_only(scenario=None):
    """One pensioner whose only income is the full new State Pension (the
    April 2026 rate in 2026-27 data)."""
    person = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "age": [70],
            "state_pension_reported": [241.30 * WEEKS_IN_YEAR],
        }
    )
    dataset = UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "council_tax": [2_000.0],
                "rent": [0.0],
            }
        ),
        fiscal_year=2026,
    )
    return Simulation(dataset=dataset, scenario=scenario)


@pytest.fixture(scope="module")
def pensioner():
    return full_new_state_pension_only()


def test_april_2027_is_the_pension_tax_allowance_explainer_figure(pensioner):
    """HM Treasury's Pension Tax Allowance explainer (28 October 2026): "the
    full annual value of the new State Pension will increase to £13,036.40",
    and Steph, whose only income it is, "would have £93.28 of income tax to
    pay" without the allowance. The unrounded rate gave £13,036.97 and
    £93.39."""
    # Simulations hold float32, a thousandth of a pound apart at this size.
    for variable in ("state_pension", "total_income"):
        assert float(pensioner.calculate(variable, 2027)[0]) == pytest.approx(
            13_036.40, abs=HALF_PENNY
        )
    assert float(pensioner.calculate("income_tax", 2027)[0]) == pytest.approx(
        93.28, abs=0.001
    )


@pytest.mark.parametrize("year", [2027, 2028, 2029])
def test_full_new_state_pension_income_is_the_pension_tax_allowance_threshold(
    pensioner, year
):
    """The explainer sets the allowance's threshold at the full annual value
    of the new State Pension, 52 weeks at the weekly rate, and uprates it "in
    line with" that value for 2028-29 and 2029-30. A pensioner with only that
    pension has exactly that income, a whole number of 5p a week, so sits at
    the threshold, not a few pence above it."""
    rate = weekly(pensioner.tax_benefit_system.parameters, RATES["new"], year)
    assert on_grid(rate)
    income = float(pensioner.calculate("total_income", year)[0])
    assert income == pytest.approx(rate * WEEKS_IN_YEAR, abs=HALF_PENNY)
    assert float(pensioner.calculate("additional_state_pension", year)[0]) == 0


# 6. The rounding is a parameter.


ROUTES = {
    "reform-dict": lambda change: Simulation(situation=SITUATION, reform=change),
    "parameter-changes": lambda change: Simulation(
        situation=SITUATION, scenario=Scenario(parameter_changes=change)
    ),
    "before-data-load": lambda change: Simulation(
        situation=SITUATION,
        scenario=Scenario(parameter_changes=change, applied_before_data_load=True),
    ),
}
SITUATION = {
    "people": {"pensioner": {"age": {2025: 70}}},
    "benunits": {"benunit": {"members": ["pensioner"]}},
    "households": {"household": {"members": ["pensioner"]}},
}


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("unit", [0, 0.01, 1])
def test_each_reform_route_moves_the_projection_by_the_rounding(route, unit):
    reformed = ROUTES[route]({ROUNDING: unit})
    parameters = reformed.tax_benefit_system.parameters
    for path in RATES.values():
        previous = weekly(parameters, path, LAST_PUBLISHED)
        for year in PROJECTED:
            rate = weekly(parameters, path, year)
            rise = triple_lock(parameters, year)
            if unit:
                expected = uprated(previous, rise, Decimal(repr(unit)))
            else:
                expected = previous * (1 + rise)
            assert rate == pytest.approx(expected, abs=1e-6), (path, year)
            previous = rate
        # The baseline stays current law.
        assert weekly(parameters.baseline, path, 2028) == weekly(
            system.parameters, path, 2028
        )


def test_without_rounding_the_projection_is_the_unrounded_uprating():
    """Zero rounding gives the unrounded chain: the last published rate
    times the triple lock's growth since then. (General uprating gave this to
    within a third of a penny through 2039; it read the index stored to five
    decimal places.)"""
    reformed = ROUTES["parameter-changes"]({ROUNDING: 0})
    parameters = reformed.tax_benefit_system.parameters
    for path in RATES.values():
        level = weekly(parameters, path, LAST_PUBLISHED)
        for year in PROJECTED:
            level *= 1 + triple_lock(parameters, year)
            # Each year's product is kept to £0.000001.
            assert weekly(parameters, path, year) == pytest.approx(level, abs=1e-5)


# 7. A changed triple lock rate or index moves the projection.


def test_a_changed_triple_lock_index_moves_the_projection():
    index = system.parameters.get_child(TRIPLE_LOCK_INDEX)
    level = index("2029-01-01") * 1.1
    reformed = ROUTES["reform-dict"]({TRIPLE_LOCK_INDEX: {"2029": level}})
    parameters = reformed.tax_benefit_system.parameters
    changed = parameters.get_child(TRIPLE_LOCK_INDEX)
    for path in RATES.values():
        for year in (2029, 2030):
            growth = changed(f"{year}-01-01") / changed(f"{year - 1}-01-01") - 1
            previous = weekly(parameters, path, year - 1)
            assert weekly(parameters, path, year) == pytest.approx(
                uprated(previous, growth), abs=1e-9
            )
        assert weekly(parameters, path, 2029) > weekly(system.parameters, path, 2029)


# Each case rebuilds the parameters, so a short list stands in for a
# Hypothesis search: no rise, the floor, the tie case below, and two others.
@pytest.mark.parametrize("rate", [0, 0.025, 0.039, 0.053, 0.15])
def test_a_triple_lock_rate_set_by_reform_is_rounded_into_the_chain(rate):
    reformed = ROUTES["reform-dict"]({TRIPLE_LOCK: {"2028": rate}})
    parameters = reformed.tax_benefit_system.parameters
    for path in RATES.values():
        rates = [weekly(parameters, path, y) for y in range(2027, 2031)]
        assert all(on_grid(r) for r in rates)
        assert rates[1] == pytest.approx(uprated(rates[0], rate), abs=1e-12)
        assert rates[0] == weekly(system.parameters, path, 2027)


def test_a_half_rounds_up_and_the_index_keeps_its_precision():
    """A 3.9% triple lock for April 2028 takes £250.70 to £260.4773, so
    £260.50; 2.5% then gives £267.0125, so £267.00, and £273.675 exactly for
    April 2030, which rounds up to £273.70. In floats that product is
    273.67499999999995, and an index stored to five decimal places gives
    £273.65. £273.675 is 5,473.5 units of 5p, which rounding halves to even
    would also take up, so the last check uses a half above an even count,
    5,474.5 units, which halves up takes to £273.75 and halves to even would
    take down."""
    reformed = ROUTES["reform-dict"]({TRIPLE_LOCK: {"2028": 0.039}})
    parameters = reformed.tax_benefit_system.parameters
    assert [triple_lock(parameters, y) for y in (2029, 2030)] == [0.025, 0.025]
    rates = [weekly(parameters, RATES["new"], y) for y in range(2027, 2031)]
    assert rates == pytest.approx([250.70, 260.50, 267.00, 273.70], abs=1e-12)
    assert round_weekly_rate(Decimal("273.725"), 0.05) == 273.75


def test_a_rate_a_reform_states_is_kept():
    """A reform that states the full rate for one year keeps it, and the
    years after return to prior law's rounded path, as dated reforms fill
    gaps from prior law."""
    reformed = ROUTES["reform-dict"]({RATES["new"]: {"2028": 300}})
    parameters = reformed.tax_benefit_system.parameters
    rates = [weekly(parameters, RATES["new"], y) for y in range(2027, 2031)]
    prior = [weekly(system.parameters, RATES["new"], y) for y in range(2027, 2031)]
    assert rates == [prior[0], 300, prior[2], prior[3]]
    assert all(on_grid(rate) for rate in prior)


# 8. Properties of the rule.

amounts = st.decimals(
    min_value=0, max_value=2_000, places=6, allow_nan=False, allow_infinity=False
)
units = st.sampled_from([0.01, 0.05, 0.10, 1.0])
grid_rates = st.integers(0, 4_000).map(lambda n: n / 20)
rises = st.integers(-50, 200).map(lambda n: n / 1000)


@PROPERTY_SETTINGS
@given(amount=amounts, unit=units)
def test_rounding_lands_on_the_grid_within_half_a_unit(amount, unit):
    rounded = round_weekly_rate(amount, unit)
    step = Decimal(repr(unit))
    assert Decimal(repr(rounded)) % step == 0
    assert abs(Decimal(repr(rounded)) - amount) <= step / 2
    assert round_weekly_rate(Decimal(repr(rounded)), unit) == rounded


@PROPERTY_SETTINGS
@given(a=amounts, b=amounts, unit=units)
def test_rounding_is_monotone(a, b, unit):
    a, b = sorted((a, b))
    assert round_weekly_rate(a, unit) <= round_weekly_rate(b, unit)


@PROPERTY_SETTINGS
@given(previous=grid_rates, rise=rises)
def test_uprating_matches_the_rule_and_a_rise_never_lowers_the_rate(previous, rise):
    rate = uprate_weekly_rate(previous, 1 + Decimal(repr(rise)), 0.05)
    assert rate == uprated(previous, rise)
    if rise >= 0:
        assert rate >= previous
    else:
        assert rate <= previous


@PROPERTY_SETTINGS
@given(
    start=grid_rates,
    path=st.lists(st.integers(0, 150).map(lambda n: n / 1000), min_size=1, max_size=15),
)
def test_a_projected_path_is_the_chained_rule(start, path):
    """For any stated rate and any yearly rises, the projection is the rule
    applied year by year, keeps the stated value and is non-decreasing."""
    levels = {"2026-01-01": 1.0}
    level = 1.0
    for offset, rise in enumerate(path, start=1):
        level *= 1 + rise
        levels[f"{2026 + offset}-01-01"] = level
    root = ParameterNode(
        "",
        data={
            "index": {"values": levels},
            "rounding": {"values": {"2011-01-01": 0.05}},
            "rate": {
                "values": {"2026-04-01": start},
                "metadata": {"uprating": "index"},
            },
        },
    )
    rate = root.rate
    project_weekly_rate(rate, root.index, root.rounding)
    values = {entry.instant_str: entry.value for entry in rate.values_list}
    assert values.pop("2026-04-01") == start
    expected = start
    for offset, rise in enumerate(path, start=1):
        previous = expected
        expected = uprated(expected, rise)
        assert values[f"{2026 + offset}-01-01"] == pytest.approx(expected, abs=1e-12)
        assert expected >= previous
    assert len(values) == len(path)

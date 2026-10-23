"""State Pension components when the model year is not the data year.

basic_state_pension, new_state_pension and additional_state_pension split the
State Pension a person reported in the data year. Survey ages are held fixed
across the years a dataset is projected to, so a record's birth cohort moves
one year later for each year projected, and its State Pension type in the
period can differ from its type in the data year. All three components split
by the period's type, so together they split the reported amount with no
overlap and no gap: the part up to the type's full rate is uprated by the full
rate, and the part above it (additional pension, protected payments) by
September CPI, as the Up-rating Orders raise it (see add_on_uprating).

The YAML runner builds simulations without a dataset, where the data year is
the period by construction, so these cases build simulations from data.
"""

from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system

DATA_YEAR = 2024
YEARS = range(DATA_YEAR, 2031)
WEEKS_IN_YEAR = 52
COMPONENTS = ["basic_state_pension", "new_state_pension", "additional_state_pension"]


def person_table(people: list, ages=None) -> pd.DataFrame:
    ids = np.arange(len(people))
    return pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": [p["age"] for p in people] if ages is None else ages,
            "gender": ["MALE" if p["male"] else "FEMALE" for p in people],
            "months_since_last_birthday": [p["months"] for p in people],
            "state_pension_reported": [p["weekly"] * WEEKS_IN_YEAR for p in people],
        }
    )


def year_dataset(people: list, year: int, ages=None) -> UKSingleYearDataset:
    """One person per household."""
    ids = np.arange(len(people))
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": np.ones(len(people)),
            "region": "LONDON",
            "tenure_type": "OWNED_OUTRIGHT",
            "rent": 0.0,
            "council_tax": 0.0,
        }
    )
    return UKSingleYearDataset(
        person=person_table(people, ages),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=household,
        fiscal_year=year,
    )


def projected_simulation(people: list) -> Microsimulation:
    """Data for 2024-25, projected forward as survey data is: ages held fixed."""
    return Microsimulation(dataset=year_dataset(people, DATA_YEAR))


def flat_rates(sim, year: int) -> dict:
    p = sim.tax_benefit_system.parameters.gov.dwp.state_pension
    return {
        "BASIC": p.basic_state_pension.amount(year),
        "NEW": p.new_state_pension.amount(year),
    }


def flat_uprating(sim, year: int, pension_type: str) -> float:
    """The type's full rate in the year over its full rate in the data year."""
    return (
        flat_rates(sim, year)[pension_type] / flat_rates(sim, DATA_YEAR)[pension_type]
    )


# The rise each Social Security Benefits Up-rating Order gave additional
# pensions in long-term benefits, in April of the year: September CPI of the
# year before, under the Social Security Administration Act 1992 ss.150(1)(c)
# and 151(1). Since 2017 the same Orders raise the amounts of new State
# Pension at the transitional rate above the full rate (protected payments) by
# the same percentage, under s.151A. The 2016 Order (SI 2016/230) raised no
# additional pension: September 2015 CPI was -0.1%. For example, SI 2026/148
# art 4(3)(a) and 6(3)(b) (3.8%) and SI 2025/295 art 4(3)(a) and 6(3)(b)
# (1.7%), against 4.8% and 4.1% for the full rates (arts 4(2) and 6(1)).
UP_RATING_ORDERS = {
    2011: ("SI 2011/821", 0.031),
    2012: ("SI 2012/780", 0.052),
    2013: ("SI 2013/574", 0.022),
    2014: ("SI 2014/516", 0.027),
    2015: ("SI 2015/457", 0.012),
    2016: ("SI 2016/230", 0.0),
    2017: ("SI 2017/260", 0.010),
    2018: ("SI 2018/281", 0.030),
    2019: ("SI 2019/480", 0.024),
    2020: ("SI 2020/234", 0.017),
    2021: ("SI 2021/162", 0.005),
    2022: ("SI 2022/292", 0.031),
    2023: ("SI 2023/316", 0.101),
    2024: ("SI 2024/242", 0.067),
    2025: ("SI 2025/295", 0.017),
    2026: ("SI 2026/148", 0.038),
}
# The model compounds the yearly rises into an index rounded to five decimal
# places each year (create_economic_assumption_indices.py), so it differs from
# the exact product of the rises by under 1e-5 of the amount.
INDEX_ROUNDING = 1e-5


def add_on_rise(sim, year: int) -> float:
    """The April rise in additional pensions and protected payments: the
    Up-rating Order's where one has been made. For later years, the forecast
    September CPI of the year before, as ONS publishes it (to 0.1 percentage
    points), and no rise if prices fall (an Order under SSAA 1992 s.150(2) or
    s.151A(2) is made only if prices rose)."""
    if year in UP_RATING_ORDERS:
        return UP_RATING_ORDERS[year][1]
    parameters = sim.tax_benefit_system.parameters
    inputs = parameters.gov.economic_assumptions.statutory_uprating_inputs
    september = inputs.cpi_september(f"{year - 1}-09-01")
    published = float(
        Decimal(repr(float(september))).quantize(Decimal("0.001"), ROUND_HALF_UP)
    )
    return max(published, 0.0)


def add_on_uprating(sim, year: int) -> float:
    """Uprating of the part above the full rate (additional pension, protected
    payments) from the data year to ``year``: the yearly rises compounded. A
    reference independent of the model's index, which follows the same rises
    whatever the State Pension type (PolicyEngine/policyengine-uk#1941)."""
    factor = 1.0
    for later_year in range(DATA_YEAR + 1, year + 1):
        factor *= 1 + add_on_rise(sim, later_year)
    return factor


def uprated_reported(sim, year: int, pension_type: str, weekly: float) -> float:
    """The data-year amount, its part up to the full rate uprated by the full
    rate and the part above it by September CPI."""
    full = flat_rates(sim, DATA_YEAR)[pension_type]
    return WEEKS_IN_YEAR * (
        min(weekly, full) * flat_uprating(sim, year, pension_type)
        + max(weekly - full, 0) * add_on_uprating(sim, year)
    )


def approx(expected: float):
    """Exact to the penny, allowing for the model index's rounding."""
    return pytest.approx(expected, rel=INDEX_ROUNDING, abs=0.01)


def calculate(sim, variable: str, year: int) -> np.ndarray:
    return np.asarray(sim.calculate(variable, year))


def test_basic_in_data_year_and_new_in_period_is_not_paid_twice():
    """A man aged 75 on 6 October 2024, born 6 July 1949, reached State Pension
    age at 65 in 2014: basic State Pension. Held at 75, the record in 2030-31
    stands for a man born 6 July 1955, who reached it at 66 in 2021: new State
    Pension. His £200 a week, below the new State Pension's full rate, is all
    new State Pension; before the fix, the £30.50 above the basic State
    Pension's full rate was paid again as additional State Pension."""
    person = {"age": 75, "male": True, "months": 3, "weekly": 200}
    sim = projected_simulation([person])
    assert calculate(sim, "state_pension_type", DATA_YEAR)[0] == "BASIC"
    for year in (2027, 2030):
        assert calculate(sim, "state_pension_type", year)[0] == "NEW"
        expected = uprated_reported(sim, year, "NEW", 200)
        assert calculate(sim, "new_state_pension", year)[0] == pytest.approx(
            expected, abs=0.01
        )
        assert calculate(sim, "basic_state_pension", year)[0] == 0
        assert calculate(sim, "additional_state_pension", year)[0] == 0
        assert calculate(sim, "state_pension", year)[0] == pytest.approx(
            expected, abs=0.01
        )


def test_protected_payment_above_new_state_pension_follows_period_type():
    """A woman aged 72 in 2024-25 (born 6 July 1952) reached State Pension age in
    2014 on the basic State Pension; held at 72 she stands, by 2030-31, for a
    woman born in 1958, on the new State Pension. Her £240 a week exceeds the
    new State Pension's full rate, so the excess is additional State Pension
    (a protected payment), uprated by September CPI."""
    person = {"age": 72, "male": False, "months": 3, "weekly": 240}
    sim = projected_simulation([person])
    assert calculate(sim, "state_pension_type", DATA_YEAR)[0] == "BASIC"
    assert calculate(sim, "state_pension_type", 2030)[0] == "NEW"
    rates, data_rates = flat_rates(sim, 2030), flat_rates(sim, DATA_YEAR)
    assert calculate(sim, "new_state_pension", 2030)[0] == pytest.approx(
        rates["NEW"] * WEEKS_IN_YEAR, abs=0.01
    )
    assert calculate(sim, "additional_state_pension", 2030)[0] == approx(
        (240 - data_rates["NEW"]) * WEEKS_IN_YEAR * add_on_uprating(sim, 2030)
    )


@pytest.mark.parametrize(
    "person, pension_type",
    [
        # Aged 90: born 1934 in the data year, 1940 by 2030-31.
        ({"age": 90, "male": True, "months": 3, "weekly": 250}, "BASIC"),
        # Aged 70: born 1954 in the data year, 1960 by 2030-31; both reached
        # State Pension age after 5 April 2016.
        ({"age": 70, "male": True, "months": 3, "weekly": 240}, "NEW"),
    ],
)
def test_unchanged_type_splits_at_its_own_flat_rate(person, pension_type):
    sim = projected_simulation([person])
    for year in YEARS:
        assert calculate(sim, "state_pension_type", year)[0] == pension_type
        total = sum(calculate(sim, v, year)[0] for v in COMPONENTS)
        assert total == approx(
            uprated_reported(sim, year, pension_type, person["weekly"])
        )


def test_nothing_is_paid_once_the_record_falls_below_state_pension_age():
    """Aged 66 in 2024-25 (born 6 July 1958) is over State Pension age on the new
    State Pension; aged 66 in 2027-28 (born 6 July 1961) attains it at 67."""
    person = {"age": 66, "male": True, "months": 3, "weekly": 230}
    sim = projected_simulation([person])
    assert calculate(sim, "state_pension_type", DATA_YEAR)[0] == "NEW"
    assert calculate(sim, "state_pension_type", 2027)[0] == "NONE"
    for variable in COMPONENTS + ["state_pension"]:
        assert calculate(sim, variable, 2027)[0] == 0


def test_new_in_data_year_and_basic_in_period_is_paid_in_full():
    """Held-fixed ages only move cohorts later, so a record never goes from new
    to basic State Pension when projected. A dataset may still carry other ages
    in later years; the band between the two flat rates must still be paid."""
    people = [
        # New State Pension at 70 in 2024-25; 85 in 2030-31 is basic.
        {"age": 70, "male": True, "months": 3, "weekly": 240},
        # Below State Pension age at 60 in 2024-25; 70 in 2030-31 is new.
        {"age": 60, "male": True, "months": 3, "weekly": 230},
    ]
    dataset = UKMultiYearDataset(
        datasets=[
            year_dataset(people, DATA_YEAR),
            year_dataset(people, 2030, ages=[85, 70]),
        ]
    )
    sim = Microsimulation(dataset=dataset)
    assert list(calculate(sim, "state_pension_type", DATA_YEAR)) == ["NEW", "NONE"]
    assert list(calculate(sim, "state_pension_type", 2030)) == ["BASIC", "NEW"]
    total = sum(calculate(sim, v, 2030) for v in COMPONENTS)
    assert total[0] == approx(uprated_reported(sim, 2030, "BASIC", 240))
    assert total[1] == approx(uprated_reported(sim, 2030, "NEW", 230))


# The add-on rises with prices (PolicyEngine/policyengine-uk#1941). Records are
# built from 2024-25 data, where the full rates are £169.50 (basic State
# Pension, Social Security Benefits Up-rating Order 2024 art 4(2)) and £221.20
# (new State Pension, art 6(1)).


def test_additional_pension_rises_with_september_cpi_not_the_basic_rate():
    """A man aged 90 in 2024-25 reached State Pension age in 1999, on the basic
    State Pension, as does a man aged 90 in any later year. He reports £200 a
    week, £30.50 above the 2024-25 full basic rate. The Up-rating Orders raised
    the basic State Pension by 4.1% and 4.8% and additional pensions by 1.7%
    and 3.8% (SI 2025/295 and SI 2026/148, arts 4(2) and 4(3)(a)), so in
    2026-27 he gets £184.90 a week of basic State Pension and £30.50 x 1.017 x
    1.038 of additional State Pension."""
    person = {"age": 90, "male": True, "months": 3, "weekly": 200}
    sim = projected_simulation([person])
    for year in (DATA_YEAR, 2025, 2026):
        assert calculate(sim, "state_pension_type", year)[0] == "BASIC"
    additional_2025 = (200 - 169.50) * WEEKS_IN_YEAR * 1.017
    additional_2026 = (200 - 169.50) * WEEKS_IN_YEAR * 1.017 * 1.038
    assert calculate(sim, "additional_state_pension", DATA_YEAR)[0] == approx(
        (200 - 169.50) * WEEKS_IN_YEAR
    )
    assert calculate(sim, "additional_state_pension", 2025)[0] == approx(
        additional_2025
    )
    assert calculate(sim, "additional_state_pension", 2026)[0] == approx(
        additional_2026
    )
    assert calculate(sim, "basic_state_pension", 2026)[0] == approx(
        184.90 * WEEKS_IN_YEAR
    )
    assert calculate(sim, "state_pension", 2026)[0] == approx(
        184.90 * WEEKS_IN_YEAR + additional_2026
    )


def test_protected_payment_rises_with_september_cpi_not_the_new_rate():
    """A man aged 70 in 2024-25 reached State Pension age in 2020, on the new
    State Pension, as does a man aged 70 in 2026-27. He reports £240 a week,
    £18.80 above the 2024-25 full rate: a protected payment. The Up-rating
    Orders raised the full rate by 4.1% and 4.8% and protected payments by
    1.7% and 3.8% (SI 2025/295 and SI 2026/148, arts 6(1) and 6(3)(b)), so in
    2026-27 he gets £241.30 a week of new State Pension and £18.80 x 1.017 x
    1.038 of protected payment."""
    person = {"age": 70, "male": True, "months": 3, "weekly": 240}
    sim = projected_simulation([person])
    for year in (DATA_YEAR, 2025, 2026):
        assert calculate(sim, "state_pension_type", year)[0] == "NEW"
    protected_2026 = (240 - 221.20) * WEEKS_IN_YEAR * 1.017 * 1.038
    assert calculate(sim, "additional_state_pension", 2025)[0] == approx(
        (240 - 221.20) * WEEKS_IN_YEAR * 1.017
    )
    assert calculate(sim, "additional_state_pension", 2026)[0] == approx(protected_2026)
    assert calculate(sim, "new_state_pension", 2026)[0] == approx(
        241.30 * WEEKS_IN_YEAR
    )
    assert calculate(sim, "state_pension", 2026)[0] == approx(
        241.30 * WEEKS_IN_YEAR + protected_2026
    )


@pytest.mark.parametrize(
    "person",
    [
        {"age": 90, "male": True, "months": 3, "weekly": 250},
        {"age": 70, "male": True, "months": 3, "weekly": 240},
    ],
    ids=["additional_pension", "protected_payment"],
)
def test_add_on_grows_each_year_by_that_years_september_cpi_rise(person):
    """Each April the add-on rises by the September CPI of the year before:
    the Orders' 1.7% and 3.8%, then the forecast."""
    sim = projected_simulation([person])
    for year in YEARS[1:]:
        growth = (
            calculate(sim, "additional_state_pension", year)[0]
            / calculate(sim, "additional_state_pension", year - 1)[0]
        )
        assert growth == pytest.approx(1 + add_on_rise(sim, year), abs=INDEX_ROUNDING)


def test_september_cpi_uprating_matches_the_up_rating_orders():
    """The index the add-on follows rises each April by the percentage the
    Up-rating Order gave additional pensions that year, 0% in April 2016."""
    parameters = system.parameters
    indices = parameters.gov.economic_assumptions.indices
    yoy_growth = parameters.gov.economic_assumptions.yoy_growth
    for year, (order, rise) in UP_RATING_ORDERS.items():
        assert yoy_growth.september_cpi_uprating(year) == pytest.approx(rise), order
        growth = indices.september_cpi_uprating(year) / indices.september_cpi_uprating(
            year - 1
        )
        assert growth == pytest.approx(1 + rise, abs=INDEX_ROUNDING), order


@pytest.mark.parametrize(
    "change",
    [
        # Full rates set by reform from 2026-27: the add-on is not scaled with
        # them.
        {
            "reform": {
                "gov.dwp.state_pension.basic_state_pension.amount": {
                    "2026-01-01.2100-12-31": 300.0
                },
                "gov.dwp.state_pension.new_state_pension.amount": {
                    "2026-01-01.2100-12-31": 300.0
                },
            }
        },
        # A 10% triple-lock floor from April 2027 raises the full rates, not
        # the add-on.
        {
            "scenario": Scenario(
                parameter_changes={
                    "gov.dwp.state_pension.triple_lock.minimum_rate": {
                        "year:2027-01-01:100": 0.1
                    },
                },
                applied_before_data_load=True,
            )
        },
    ],
    ids=["full_rates", "triple_lock_floor"],
)
def test_full_rate_reforms_leave_the_add_on_alone(change):
    people = [
        {"age": 90, "male": True, "months": 3, "weekly": 250},
        {"age": 70, "male": True, "months": 3, "weekly": 240},
    ]
    baseline = projected_simulation(people)
    reformed = Microsimulation(dataset=year_dataset(people, DATA_YEAR), **change)
    for year in (2027, 2028, 2030):
        assert calculate(reformed, "state_pension", year).sum() != pytest.approx(
            calculate(baseline, "state_pension", year).sum()
        )
        assert calculate(reformed, "additional_state_pension", year) == pytest.approx(
            calculate(baseline, "additional_state_pension", year), abs=0.01
        )


def test_a_september_cpi_scenario_moves_the_add_on():
    """The index is read from the simulation's own parameters: with September
    2027 CPI set to 1%, the add-on rises 1% in April 2028, while the full
    rates rise by at least the triple lock's 2.5%."""
    person = {"age": 90, "male": True, "months": 3, "weekly": 250}
    scenario = Scenario(
        parameter_changes={
            "gov.economic_assumptions.statutory_uprating_inputs.cpi_september": {
                "2027": 0.01
            },
        },
        applied_before_data_load=True,
    )
    sim = Microsimulation(dataset=year_dataset([person], DATA_YEAR), scenario=scenario)
    growth = (
        calculate(sim, "additional_state_pension", 2028)[0]
        / calculate(sim, "additional_state_pension", 2027)[0]
    )
    assert growth == pytest.approx(1.01, abs=INDEX_ROUNDING)
    assert flat_uprating(sim, 2028, "BASIC") / flat_uprating(sim, 2027, "BASIC") >= (
        1.025 - INDEX_ROUNDING
    )


# Each example builds a microsimulation, so examples are slow to generate.
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


PEOPLE = st.lists(
    st.fixed_dictionaries(
        {
            "age": st.integers(min_value=55, max_value=100),
            "male": st.booleans(),
            "months": st.floats(min_value=0, max_value=12, exclude_max=True),
            # Include each data-year flat rate, where the split changes.
            "weekly": st.one_of(
                st.floats(min_value=0, max_value=600),
                st.sampled_from([0, 169.5, 221.2]),
            ),
        }
    ),
    min_size=1,
    max_size=30,
)


def by_type(pension_type: np.ndarray, basic, new) -> np.ndarray:
    return np.select([pension_type == "BASIC", pension_type == "NEW"], [basic, new], 0)


def assert_components_add_up(sim, people: list, years) -> None:
    """For each person and year: below State Pension age, no component and type
    NONE. Over it, only the period type's flat-rate component, which is the
    reported amount up to the type's full rate, uprated by the full rate; and,
    deflating each component by its own uprating, the three components add up
    to exactly the reported amount, with no overlap and no gap."""
    weekly = np.array([p["weekly"] for p in people])
    for year in years:
        pension_type = calculate(sim, "state_pension_type", year).astype(str)
        over_spa = calculate(sim, "is_SP_age", year).astype(bool)
        basic, new, additional = (calculate(sim, v, year) for v in COMPONENTS)
        rates, data_rates = flat_rates(sim, year), flat_rates(sim, DATA_YEAR)
        full = by_type(pension_type, data_rates["BASIC"], data_rates["NEW"])
        flat_up = by_type(
            pension_type,
            flat_uprating(sim, year, "BASIC"),
            flat_uprating(sim, year, "NEW"),
        )
        add_up = add_on_uprating(sim, year)
        reported = weekly * WEEKS_IN_YEAR
        assert np.array_equal(pension_type == "NONE", ~over_spa), year
        flat = basic + new
        expected_flat = over_spa * np.minimum(reported, full * WEEKS_IN_YEAR) * flat_up
        assert np.allclose(flat, expected_flat, rtol=1e-5, atol=0.01)
        deflated = np.where(
            over_spa,
            flat / np.where(over_spa, flat_up, 1) + additional / add_up,
            0,
        )
        assert np.allclose(deflated, over_spa * reported, rtol=1e-5, atol=0.01)
        assert np.all(additional[~over_spa] == 0)
        assert np.all(basic[pension_type != "BASIC"] == 0)
        assert np.all(new[pension_type != "NEW"] == 0)
        assert np.all(additional >= 0)
        assert np.all(basic <= rates["BASIC"] * WEEKS_IN_YEAR * (1 + 1e-6))
        assert np.all(new <= rates["NEW"] * WEEKS_IN_YEAR * (1 + 1e-6))


@PROPERTY_SETTINGS
@given(people=PEOPLE)
def test_components_add_up_to_uprated_reported_amount(people):
    """Data projected with ages held fixed, every year from 2024-25 to 2030-31."""
    sim = projected_simulation(people)
    assert_components_add_up(sim, people, YEARS)


@PROPERTY_SETTINGS
@given(
    people=PEOPLE,
    period=st.integers(min_value=DATA_YEAR + 1, max_value=2030),
    data=st.data(),
)
def test_components_add_up_whatever_ages_the_period_carries(people, period, data):
    """Any age in the period, so every pair of data-year and period types occurs,
    including new to basic and none to either."""
    ages = data.draw(
        st.lists(
            st.integers(min_value=55, max_value=100),
            min_size=len(people),
            max_size=len(people),
        )
    )
    dataset = UKMultiYearDataset(
        datasets=[
            year_dataset(people, DATA_YEAR),
            year_dataset(people, period, ages=ages),
        ]
    )
    sim = Microsimulation(dataset=dataset)
    assert_components_add_up(sim, people, (DATA_YEAR, period))


def main_components(sim, weekly: np.ndarray, year: int) -> tuple:
    """basic, new and additional State Pension as policyengine-uk main computed
    them before #1941 (6d89338a), with the add-on uprated by the type's full
    rate. A reference for the differential test."""
    pension_type = calculate(sim, "state_pension_type", year).astype(str)
    over_spa = calculate(sim, "is_SP_age", year).astype(bool)
    rates, data_rates = flat_rates(sim, year), flat_rates(sim, DATA_YEAR)
    full = by_type(pension_type, data_rates["BASIC"], data_rates["NEW"])
    full_now = by_type(pension_type, rates["BASIC"], rates["NEW"])
    has_rate = full > 0
    safe_full = np.where(has_rate, full, 1)
    share = np.where(has_rate, np.minimum(weekly, full) / safe_full, 0)
    basic = np.where(pension_type == "BASIC", share * rates["BASIC"], 0)
    new = np.where(pension_type == "NEW", share * rates["NEW"], 0)
    above = np.where(pension_type != "NONE", np.maximum(weekly - full, 0), 0)
    additional = over_spa * above * np.where(has_rate, full_now / safe_full, 1)
    return tuple(WEEKS_IN_YEAR * x for x in (basic, new, additional))


# The model computes in float32 and the reference in float64.
FLOAT32 = dict(rtol=1e-6, atol=0.01)


def paired(people: list, extra: list) -> list:
    """Each person, then the same person reporting ``extra`` more a week."""
    return people + [
        {**person, "weekly": person["weekly"] + more}
        for person, more in zip(people, extra)
    ]


@PROPERTY_SETTINGS
@given(people=PEOPLE, data=st.data())
def test_add_on_follows_september_cpi_and_nothing_else_changes(people, data):
    """For every record and year from 2024-25 to 2030-31:

    - the add-on is never negative, and never falls as the reported amount rises;
    - from one year to the next, with the type unchanged, it grows by that
      year's September CPI rise;
    - differential against main: the flat-rate parts are unchanged, the add-on
      is unchanged in the data year, and otherwise differs only by uprating with
      September CPI instead of the full rate."""
    extra = data.draw(
        st.lists(
            st.floats(min_value=0, max_value=300),
            min_size=len(people),
            max_size=len(people),
        )
    )
    records = paired(people, extra)
    sim = projected_simulation(records)
    weekly = np.array([p["weekly"] for p in records])
    n = len(people)
    previous = None
    for year in YEARS:
        pension_type = calculate(sim, "state_pension_type", year).astype(str)
        basic, new, additional = (calculate(sim, v, year) for v in COMPONENTS)
        assert np.all(additional >= 0)
        assert np.all(additional[n:] >= additional[:n] - 1e-9)
        main_basic, main_new, main_additional = main_components(sim, weekly, year)
        assert np.allclose(basic, main_basic, **FLOAT32)
        assert np.allclose(new, main_new, **FLOAT32)
        if year == DATA_YEAR:
            assert np.allclose(additional, main_additional, **FLOAT32)
        flat_up = by_type(
            pension_type,
            flat_uprating(sim, year, "BASIC"),
            flat_uprating(sim, year, "NEW"),
        )
        flat_up = np.where(pension_type == "NONE", 1, flat_up)
        assert np.allclose(
            additional * flat_up,
            main_additional * add_on_uprating(sim, year),
            rtol=INDEX_ROUNDING,
            atol=0.01,
        )
        if previous is not None:
            previous_type, previous_additional = previous
            same = (pension_type == previous_type) & (previous_additional > 0)
            rise = 1 + add_on_rise(sim, year)
            assert np.allclose(
                additional[same],
                previous_additional[same] * rise,
                rtol=INDEX_ROUNDING,
                atol=1e-6,
            )
        previous = (pension_type, additional)


RATE = st.floats(min_value=0, max_value=500)


@PROPERTY_SETTINGS
@given(
    people=PEOPLE,
    basic_rate=RATE,
    new_rate=RATE,
    from_year=st.sampled_from([None, 2025, 2027]),
)
def test_full_rate_reforms_never_move_the_add_on(
    people, basic_rate, new_rate, from_year
):
    """Differential: the same records with and without a reform to the full
    rates, undated (so also in the data year) or from a later year. In law the
    add-on rises with prices whatever the full rates do, and the reported amount
    is still split at the legislated data-year rates, so the add-on is the same
    in every year."""
    period = (
        "2000-01-01.2100-12-31"
        if from_year is None
        else f"{from_year}-01-01.2100-12-31"
    )
    reform = {BSP: {period: basic_rate}, NSP: {period: new_rate}}
    baseline = projected_simulation(people)
    reformed = Microsimulation(dataset=year_dataset(people, DATA_YEAR), reform=reform)
    for year in YEARS:
        assert np.allclose(
            calculate(reformed, "additional_state_pension", year),
            calculate(baseline, "additional_state_pension", year),
            rtol=1e-12,
            atol=1e-9,
        ), year


# Rate reforms (PolicyEngine/policyengine-uk#2122). The reported amount is
# split at the legislated (baseline) data-year rate; the flat-rate part then
# follows the reformed period rate. The part above the legislated rate rises
# with September CPI, whatever the full rates (#1941): a reform to the full
# rates no longer scales it. To abolish State Pension altogether, use
# gov.contrib.abolish_state_pension.

NSP = "gov.dwp.state_pension.new_state_pension.amount"
BSP = "gov.dwp.state_pension.basic_state_pension.amount"
# Legislated full rates, 2024-25 and 2026-27 (Social Security Benefits
# Up-rating Orders 2024 and 2026).
LEGISLATED = {
    (2024, "BASIC"): 169.50,
    (2024, "NEW"): 221.20,
    (2026, "BASIC"): 184.90,
    (2026, "NEW"): 241.30,
}


def expected_under_rate(
    weekly: float, legislated: float, reformed: float, add_on_up: float = 1
) -> dict:
    """Annual flat-rate and add-on amounts for a record reporting ``weekly`` in
    a data year whose legislated full rate is ``legislated``, in a period whose
    reformed full rate is ``reformed`` and whose September CPI is ``add_on_up``
    times the data year's (1 without a dataset, where the data year is the
    period)."""
    share = min(weekly, legislated) / legislated
    add_on = max(weekly - legislated, 0) * add_on_up
    return {
        "flat": share * reformed * WEEKS_IN_YEAR,
        "additional": add_on * WEEKS_IN_YEAR,
    }


def situation(age: int, pension_type: str, weekly: float, year: int) -> dict:
    return {
        "people": {
            "person": {
                "age": {year: age},
                "state_pension_type": {year: pension_type},
                "state_pension_reported": {year: weekly * WEEKS_IN_YEAR},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def situation_components(sit: dict, reform, year: int) -> dict:
    from policyengine_uk import Simulation

    sim = Simulation(situation=sit, reform=reform)
    return {v: float(sim.calculate(v, year)[0]) for v in COMPONENTS + ["state_pension"]}


@pytest.mark.parametrize("reformed", [250.0, 230.0, 0.0])
def test_situation_new_state_pension_follows_a_dated_rate_reform(reformed):
    """Without a dataset the data year is the period, so a dated reform also
    sets the data year's rate. A pensioner reporting exactly the full rate must
    get the reformed rate, not the reported amount with the difference booked as
    additional State Pension."""
    year = 2026
    weekly = LEGISLATED[(year, "NEW")]
    sit = situation(70, "NEW", weekly, year)
    baseline = situation_components(sit, None, year)
    assert baseline["state_pension"] == pytest.approx(weekly * WEEKS_IN_YEAR, abs=0.01)
    assert baseline["additional_state_pension"] == 0
    reform = {NSP: {f"{year}-01-01.{year}-12-31": reformed}}
    result = situation_components(sit, reform, year)
    assert result["new_state_pension"] == pytest.approx(
        reformed * WEEKS_IN_YEAR, abs=0.01
    )
    assert result["additional_state_pension"] == 0
    assert result["state_pension"] == pytest.approx(reformed * WEEKS_IN_YEAR, abs=0.01)


def test_situation_basic_state_pension_follows_a_dated_rate_reform():
    year = 2026
    weekly = LEGISLATED[(year, "BASIC")]
    sit = situation(90, "BASIC", weekly, year)
    reform = {BSP: {f"{year}-01-01.{year}-12-31": 170.0}}
    result = situation_components(sit, reform, year)
    assert result["basic_state_pension"] == pytest.approx(170 * WEEKS_IN_YEAR, abs=0.01)
    assert result["additional_state_pension"] == 0
    assert result["state_pension"] == pytest.approx(170 * WEEKS_IN_YEAR, abs=0.01)


def test_situation_protected_payment_stays_additional_under_a_rate_reform():
    """£10 a week above the legislated full rate is a protected payment. The
    flat-rate part follows the reform; the protected payment stays £10 a week,
    as it rises with prices, not with the full rate (SI 2026/148 art 6(3)(b))."""
    year = 2026
    legislated = LEGISLATED[(year, "NEW")]
    weekly = legislated + 10
    sit = situation(70, "NEW", weekly, year)
    reform = {NSP: {f"{year}-01-01.{year}-12-31": 250.0}}
    result = situation_components(sit, reform, year)
    expected = expected_under_rate(weekly, legislated, 250.0)
    assert result["new_state_pension"] == pytest.approx(expected["flat"], abs=0.01)
    assert result["additional_state_pension"] == pytest.approx(
        expected["additional"], abs=0.01
    )
    assert result["state_pension"] == pytest.approx(
        expected["flat"] + expected["additional"], abs=0.01
    )


@pytest.mark.parametrize("reformed", [300.0, 200.0, 0.0])
@pytest.mark.parametrize(
    "person, pension_type, parameter",
    [
        ({"age": 70, "male": True, "months": 3, "weekly": 240}, "NEW", NSP),
        ({"age": 90, "male": True, "months": 3, "weekly": 250}, "BASIC", BSP),
    ],
)
def test_undated_rate_reform_moves_only_the_flat_rate_part(
    person, pension_type, parameter, reformed
):
    """An undated reform rewrites the data year's rate too. The record is still
    split at the legislated 2024-25 rate, so the flat-rate part rises with a
    higher rate, falls with a lower one and is nil at a rate of zero, while the
    add-on keeps rising with September CPI: at a rate of zero the record keeps
    its additional pension or protected payment. This is a deliberate change
    from before #1941, when the add-on was scaled with the full rate and a rate
    of zero removed all State Pension."""
    sim = Microsimulation(
        dataset=year_dataset([person], DATA_YEAR), reform={parameter: reformed}
    )
    year = 2027
    assert calculate(sim, "state_pension_type", year)[0] == pension_type
    expected = expected_under_rate(
        person["weekly"],
        LEGISLATED[(DATA_YEAR, pension_type)],
        reformed,
        add_on_uprating(sim, year),
    )
    flat_variable = (
        "new_state_pension" if pension_type == "NEW" else "basic_state_pension"
    )
    assert calculate(sim, flat_variable, year)[0] == pytest.approx(
        expected["flat"], abs=0.01
    )
    assert calculate(sim, "additional_state_pension", year)[0] == approx(
        expected["additional"]
    )
    assert calculate(sim, "state_pension", year)[0] == approx(
        expected["flat"] + expected["additional"]
    )


def test_abolishing_state_pension_still_removes_the_add_on():
    """gov.contrib.abolish_state_pension removes the whole State Pension,
    additional pension and protected payments included."""
    people = [
        {"age": 70, "male": True, "months": 3, "weekly": 240},
        {"age": 90, "male": True, "months": 3, "weekly": 250},
    ]
    sim = Microsimulation(
        dataset=year_dataset(people, DATA_YEAR),
        reform={"gov.contrib.abolish_state_pension": True},
    )
    for year in (DATA_YEAR, 2027, 2030):
        assert np.all(calculate(sim, "state_pension", year) == 0)


def test_dated_reform_after_the_data_year_is_unchanged_by_the_baseline_split():
    """A reform dated after the data year leaves the data year's rate alone, so
    splitting at the baseline rate changes nothing: the existing behaviour."""
    person = {"age": 70, "male": True, "months": 3, "weekly": 240}
    sim = Microsimulation(
        dataset=year_dataset([person], DATA_YEAR),
        reform={NSP: {"2026-01-01.2100-12-31": 300.0}},
    )
    expected = expected_under_rate(
        240, LEGISLATED[(DATA_YEAR, "NEW")], 300.0, add_on_uprating(sim, 2027)
    )
    assert calculate(sim, "state_pension", 2027)[0] == approx(
        expected["flat"] + expected["additional"]
    )


@pytest.mark.parametrize("composition", ["singletons", "married_pairs"])
@pytest.mark.parametrize("cap", [2.261527994036541e-210, 0.0], ids=["tiny", "zero"])
def test_tiny_new_cap_constructor_preserves_public_components(cap, composition):
    """A finite cap must stay finite through public counterfactual construction.

    These are the original finite records from the rate-reform property failure,
    also paired into lawful married benefit units. All are below State Pension
    age; changing the flat rate must leave the seven-year add-on oracle intact.
    """
    people = [
        {"age": 55, "weekly": 200.0, "male": True, "months": 1.5848689724912486e-117},
        {"age": 58, "weekly": 0.0, "male": True, "months": 0.0},
        {"age": 55, "weekly": 0.0, "male": False, "months": 0.0},
        {"age": 55, "weekly": 0.0, "male": False, "months": 0.0},
    ]

    def dataset():
        person = person_table(people)
        ids = np.arange(len(people))
        if composition == "married_pairs":
            person["person_benunit_id"] = [0, 0, 1, 1]
            person["person_household_id"] = [0, 0, 1, 1]
            person["marital_status"] = "MARRIED"
            ids = np.arange(2)
        benunit = pd.DataFrame({"benunit_id": ids})
        if composition == "married_pairs":
            benunit["is_married"] = True
        household = pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": np.ones(len(ids)),
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
            }
        )
        return UKSingleYearDataset(
            person=person, benunit=benunit, household=household, fiscal_year=DATA_YEAR
        )

    baseline = Microsimulation(dataset=dataset())
    reform = {
        BSP: {"2000-01-01.2100-12-31": 0.0},
        NSP: {"2000-01-01.2100-12-31": cap},
    }
    reformed = Microsimulation(dataset=dataset(), reform=reform)
    for year in YEARS:
        assert np.allclose(
            calculate(reformed, "additional_state_pension", year),
            calculate(baseline, "additional_state_pension", year),
            rtol=1e-12,
            atol=1e-9,
        ), year
        for variable in COMPONENTS + ["state_pension", "net_income"]:
            assert np.all(np.isfinite(calculate(reformed, variable, year))), variable
        assert np.all(calculate(reformed, "state_pension", year) == 0)
        spouses = calculate(reformed, "is_marriage_allowance_spouse", year)
        assert np.all(spouses == (composition == "married_pairs"))


@pytest.mark.parametrize("cap", [2.261527994036541e-210, 0.0], ids=["tiny", "zero"])
def test_tiny_basic_cap_constructor_preserves_positive_add_on(cap):
    """A BASIC pensioner's positive add-on survives a tiny or zero flat rate.

    The £80.50 a week above the legislated 2024 basic rate follows September
    CPI, including when a finite reform cap is below float32's range.
    """
    person = {"age": 90, "male": True, "months": 3, "weekly": 250}
    baseline = projected_simulation([person])
    reformed = Microsimulation(
        dataset=year_dataset([person], DATA_YEAR),
        reform={BSP: {"2000-01-01.2100-12-31": cap}},
    )
    for year in YEARS:
        additional = calculate(reformed, "additional_state_pension", year)
        assert np.all(additional > 0)
        assert np.allclose(
            additional,
            calculate(baseline, "additional_state_pension", year),
            rtol=1e-12,
            atol=1e-9,
        ), year
        assert additional[0] == approx(
            (250 - LEGISLATED[(DATA_YEAR, "BASIC")])
            * WEEKS_IN_YEAR
            * add_on_uprating(reformed, year)
        )
        for variable in COMPONENTS + ["state_pension", "net_income"]:
            assert np.all(np.isfinite(calculate(reformed, variable, year))), variable
        assert calculate(reformed, "new_state_pension", year)[0] == 0
        assert calculate(reformed, "basic_state_pension", year)[0] == pytest.approx(
            cap * WEEKS_IN_YEAR, abs=0.01
        )

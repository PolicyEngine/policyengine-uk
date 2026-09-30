"""State Pension components when the model year is not the data year.

basic_state_pension, new_state_pension and additional_state_pension split the
State Pension a person reported in the data year. Survey ages are held fixed
across the years a dataset is projected to, so a record's birth cohort moves
one year later for each year projected, and its State Pension type in the
period can differ from its type in the data year. All three components split
by the period's type, so together they split the reported amount with no
overlap and no gap: the part up to the type's full rate is uprated by the full
rate, and the part above it by the add-on's uprating (see add_on_uprating).

The YAML runner builds simulations without a dataset, where the data year is
the period by construction, so these cases build simulations from data.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

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


def add_on_uprating(sim, year: int, pension_type: str) -> float:
    """Uprating of the part above the full rate (additional pension, protected
    payments). The model uprates it by the full rate; in law these rise with
    prices (Social Security Benefits Up-rating Order 2026 arts 4(3) and 6(3)),
    tracked in PolicyEngine/policyengine-uk#1941. Change it here with the model."""
    return flat_uprating(sim, year, pension_type)


def uprated_reported(sim, year: int, pension_type: str, weekly: float) -> float:
    """The data-year amount, its part up to the full rate uprated by the full
    rate and the part above it by the add-on's uprating."""
    full = flat_rates(sim, DATA_YEAR)[pension_type]
    return WEEKS_IN_YEAR * (
        min(weekly, full) * flat_uprating(sim, year, pension_type)
        + max(weekly - full, 0) * add_on_uprating(sim, year, pension_type)
    )


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
    (a protected payment), uprated as the model uprates add-ons."""
    person = {"age": 72, "male": False, "months": 3, "weekly": 240}
    sim = projected_simulation([person])
    assert calculate(sim, "state_pension_type", DATA_YEAR)[0] == "BASIC"
    assert calculate(sim, "state_pension_type", 2030)[0] == "NEW"
    rates, data_rates = flat_rates(sim, 2030), flat_rates(sim, DATA_YEAR)
    assert calculate(sim, "new_state_pension", 2030)[0] == pytest.approx(
        rates["NEW"] * WEEKS_IN_YEAR, abs=0.01
    )
    assert calculate(sim, "additional_state_pension", 2030)[0] == pytest.approx(
        (240 - data_rates["NEW"]) * WEEKS_IN_YEAR * add_on_uprating(sim, 2030, "NEW"),
        abs=0.01,
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
        assert total == pytest.approx(
            uprated_reported(sim, year, pension_type, person["weekly"]), abs=0.01
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
    assert total[0] == pytest.approx(
        uprated_reported(sim, 2030, "BASIC", 240), abs=0.01
    )
    assert total[1] == pytest.approx(uprated_reported(sim, 2030, "NEW", 230), abs=0.01)


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
        add_up = by_type(
            pension_type,
            add_on_uprating(sim, year, "BASIC"),
            add_on_uprating(sim, year, "NEW"),
        )
        reported = weekly * WEEKS_IN_YEAR
        assert np.array_equal(pension_type == "NONE", ~over_spa), year
        flat = basic + new
        expected_flat = over_spa * np.minimum(reported, full * WEEKS_IN_YEAR) * flat_up
        assert np.allclose(flat, expected_flat, rtol=1e-5, atol=0.01)
        deflated = np.where(
            over_spa,
            flat / np.where(over_spa, flat_up, 1)
            + additional / np.where(over_spa, add_up, 1),
            0,
        )
        assert np.allclose(deflated, over_spa * reported, rtol=1e-5, atol=0.01)
        assert np.all(additional[~over_spa] == 0)
        assert np.all(basic[pension_type != "BASIC"] == 0)
        assert np.all(new[pension_type != "NEW"] == 0)
        assert np.all(additional >= 0)
        assert np.all(basic <= rates["BASIC"] * WEEKS_IN_YEAR * (1 + 1e-6))
        assert np.all(new <= rates["NEW"] * WEEKS_IN_YEAR * (1 + 1e-6))


@settings(max_examples=25, deadline=None)
@given(people=PEOPLE)
def test_components_add_up_to_uprated_reported_amount(people):
    """Data projected with ages held fixed, every year from 2024-25 to 2030-31."""
    sim = projected_simulation(people)
    assert_components_add_up(sim, people, YEARS)


@settings(max_examples=25, deadline=None)
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

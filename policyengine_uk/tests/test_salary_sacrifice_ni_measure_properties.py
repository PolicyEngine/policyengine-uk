"""Property-based tests: the salary sacrifice NI measures equal the change in
the complete Class 1 liability.

From 6 April 2029 the salary sacrifice above the £2,000 cap returns to
employment income (salary_sacrifice_returned_to_income), where Class 1
National Insurance charges it. salary_sacrifice_pension_ni_employee and
salary_sacrifice_pension_ni_employer report how much of the employee and
employer liability is due to the amount returned.

Every test builds the same people twice: as they are, and with nothing
returned (salary_sacrifice_returned_to_income set to zero, all else equal).
The second simulation gives the liability without the amount returned from
the model's own liability variables, so it does not depend on the formulas
under test.

Invariants, for any pay, salary sacrifice, age, statutory sick pay and
employer pension contribution:

1. Difference of complete liabilities: the employee measure equals
   ni_class_1_employee with the amount returned less ni_class_1_employee
   without it, and the employer measure equals the same difference in
   ni_class_1_employer.
2. Bounds: each measure lies between zero and the amount returned times the
   highest rate that can apply to it.
3. Exact zeros: a measure is exactly zero when nothing is returned (so in
   every year before the cap), for a person not liable to primary
   contributions (employee) and for an earner on whom no secondary
   contributions are due (employer).
4. One band, one rate: when the earnings with and without the amount
   returned lie in the same band, the measure is that band's rate times the
   amount returned. This is where the earlier single-rate formulas were
   right.
5. Monotonicity: a measure never falls when the sacrifice rises.

The invariants are checked under current law (2028, before the cap, and 2029
and 2030 under it) and in a second world where the employee rates and the
upper earnings limit change within 2041 and employer pension contributions
are charged (invariant 4 under current law only: it needs one rate for the
year). Fiscal-year conversion gives every parameter one value for each year
from 2015 to 2040, so a year after 2040 is needed for rates that differ
between months; ni_class_1_employee is a monthly variable.

Comparisons allow float32 rounding: the model stores values as float32.
"""

from collections import namedtuple

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import MONTHS_IN_YEAR, WEEKS_IN_YEAR

CLASS_1 = "gov.hmrc.national_insurance.class_1"
# name: (parameter changes, years)
WORLDS = {
    "current law": (None, [2028, 2029, 2030]),
    "rates change within the year": (
        {
            f"{CLASS_1}.rates.employee.main": {"2041-07-01.2041-12-31": 0.12},
            f"{CLASS_1}.rates.employee.additional": {"2041-10-01.2041-12-31": 0.05},
            f"{CLASS_1}.thresholds.upper_earnings_limit": {
                "2041-04-01.2041-12-31": 1_300
            },
            "gov.contrib.policyengine.employer_ni."
            "exempt_employer_pension_contributions": False,
        },
        [2030, 2041],
    ),
}
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Pounds. Liabilities are float32 sums of up to about £50,000.
TOLERANCE = 0.03

Row = namedtuple("Row", "pay sacrifice more_sacrifice age sick_pay employer_pension")

# People the properties must always cover, whatever is drawn. With the £2,000
# cap: an amount returned that crosses the upper earnings limit, one that
# crosses the primary threshold, one that crosses the secondary threshold, one
# below every threshold, a person over State Pension age, a person under 16,
# one whose statutory sick pay takes them over the upper earnings limit, and
# one with nothing returned.
KNOWN_CASES = [
    Row(48_000, 6_000, 10_000, 40, 0, 0),
    Row(11_000, 5_000, 3_000, 40, 0, 0),
    Row(3_000, 5_000, 4_000, 40, 0, 2_000),
    Row(1_000, 3_000, 500, 40, 0, 0),
    Row(45_000, 5_000, 20_000, 70, 0, 0),
    Row(20_000, 5_000, 5_000, 15, 0, 0),
    Row(46_000, 5_000, 0, 40, 3_000, 0),
    Row(60_000, 1_500, 0, 40, 0, 0),
]


def _amount(maximum):
    return st.floats(0, maximum, allow_nan=False, allow_infinity=False)


# Annual thresholds in the years tested lie near these amounts (secondary
# threshold, primary threshold, upper earnings limit), so pay near them makes
# the amount returned cross a threshold often.
near_a_threshold = st.builds(
    lambda threshold, offset: max(threshold + offset, 0.0),
    st.sampled_from([5_000.0, 6_000.0, 12_570.0, 15_100.0, 50_270.0, 60_600.0]),
    st.floats(-12_000, 6_000, allow_nan=False, allow_infinity=False),
)
rows = st.lists(
    st.builds(
        Row,
        pay=st.one_of(st.just(0.0), _amount(200_000), near_a_threshold),
        sacrifice=st.one_of(st.just(0.0), _amount(60_000), _amount(6_000)),
        more_sacrifice=_amount(30_000),
        age=st.one_of(
            st.sampled_from([15, 16, 17, 64, 65, 66, 67, 68, 69, 70]),
            st.integers(10, 95),
        ),
        sick_pay=st.one_of(st.just(0.0), _amount(8_000)),
        employer_pension=st.one_of(st.just(0.0), _amount(20_000)),
    ),
    min_size=1,
    max_size=40,
)


def _simulate(people, world, nothing_returned=False):
    """One single-person household for each of the people."""
    changes, years = WORLDS[world]
    names = [f"person_{i}" for i in range(len(people))]

    def each_year(value):
        return {str(year): value for year in years}

    situation = {
        "people": {
            name: {
                "age": each_year(row.age),
                "employment_income": each_year(row.pay),
                "pension_contributions_via_salary_sacrifice": each_year(row.sacrifice),
                "statutory_sick_pay": each_year(row.sick_pay),
                "employer_pension_contributions": each_year(row.employer_pension),
            }
            for name, row in zip(names, people)
        },
        "benunits": {f"benunit_{i}": {"members": [n]} for i, n in enumerate(names)},
        "households": {f"household_{i}": {"members": [n]} for i, n in enumerate(names)},
    }
    simulation = Simulation(situation=situation, reform=changes)
    if nothing_returned:
        for year in years:
            simulation.set_input(
                "salary_sacrifice_returned_to_income",
                year,
                np.zeros(len(people), dtype=np.float32),
            )
    return simulation


def _values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def _class_1(simulation, instant):
    parameters = simulation.tax_benefit_system.parameters(instant)
    return parameters.gov.hmrc.national_insurance.class_1


def _check_one_band_one_rate(simulation, year, returned):
    """Invariant 4, for a year whose rates and thresholds do not change."""
    class_1 = _class_1(simulation, f"{year}-01-01")
    thresholds = class_1.thresholds
    primary_threshold = thresholds.primary_threshold * WEEKS_IN_YEAR
    upper_earnings_limit = thresholds.upper_earnings_limit * WEEKS_IN_YEAR
    secondary_threshold = thresholds.secondary_threshold * WEEKS_IN_YEAR
    earnings = _values(simulation, "ni_class_1_income", year)
    without = earnings - returned
    # A pound clear of each threshold, so float32 rounding cannot move a
    # person across it.
    margin = 1
    bands = [
        ("employee", "ni_liable", earnings < primary_threshold - margin, 0),
        (
            "employee",
            "ni_liable",
            (without > primary_threshold + margin)
            & (earnings < upper_earnings_limit - margin),
            class_1.rates.employee.main,
        ),
        (
            "employee",
            "ni_liable",
            without > upper_earnings_limit + margin,
            class_1.rates.employee.additional,
        ),
        (
            "employer",
            "ni_class_1_secondary_liable",
            earnings < secondary_threshold - margin,
            0,
        ),
        (
            "employer",
            "ni_class_1_secondary_liable",
            without > secondary_threshold + margin,
            class_1.rates.employer,
        ),
    ]
    for side, liable, in_band, rate in bands:
        applies = in_band & simulation.calculate(liable, year)
        measure = _values(simulation, f"salary_sacrifice_pension_ni_{side}", year)
        np.testing.assert_allclose(
            measure[applies], rate * returned[applies], rtol=0, atol=TOLERANCE
        )


@pytest.mark.parametrize("world", list(WORLDS))
@PROPERTY_SETTINGS
@example(KNOWN_CASES)
@given(rows)
def test_measures_equal_the_difference_of_complete_liabilities(world, drawn):
    # The people as drawn, then the same people sacrificing more.
    people = drawn + [
        row._replace(sacrifice=row.sacrifice + row.more_sacrifice) for row in drawn
    ]
    n = len(drawn)
    with_returned = _simulate(people, world)
    without_returned = _simulate(people, world, nothing_returned=True)
    for year in WORLDS[world][1]:
        returned = _values(with_returned, "salary_sacrifice_returned_to_income", year)
        assert np.all(
            _values(without_returned, "salary_sacrifice_returned_to_income", year) == 0
        )
        months = [
            _class_1(with_returned, f"{year}-{month:02d}-01")
            for month in range(1, MONTHS_IN_YEAR + 1)
        ]
        highest_rate = {
            "employee": max(
                max(month.rates.employee.main, month.rates.employee.additional)
                for month in months
            ),
            # ni_class_1_employer is a yearly variable: it reads the rate at
            # the start of the year.
            "employer": months[0].rates.employer,
        }
        for side, liable in (
            ("employee", "ni_liable"),
            ("employer", "ni_class_1_secondary_liable"),
        ):
            measure = _values(
                with_returned, f"salary_sacrifice_pension_ni_{side}", year
            )
            liability = f"ni_class_1_{side}"
            # 1. Difference of complete liabilities.
            np.testing.assert_allclose(
                measure,
                _values(with_returned, liability, year)
                - _values(without_returned, liability, year),
                rtol=0,
                atol=TOLERANCE,
            )
            # 2. Bounds.
            assert np.all(measure >= 0)
            assert np.all(measure <= highest_rate[side] * returned + TOLERANCE)
            # 3. Exact zeros.
            assert np.all(measure[returned == 0] == 0)
            assert np.all(measure[~with_returned.calculate(liable, year)] == 0)
            # 5. Monotonicity.
            assert np.all(measure[n:] >= measure[:n] - TOLERANCE)
        # 4. One band, one rate.
        if world == "current law":
            _check_one_band_one_rate(with_returned, year, returned)


def test_known_cases_cross_each_threshold_and_age_condition():
    """The pinned people are the cases their comment says they are."""
    simulation = _simulate(KNOWN_CASES, "current law")
    year = 2029
    thresholds = _class_1(simulation, f"{year}-01-01").thresholds
    returned = _values(simulation, "salary_sacrifice_returned_to_income", year)
    earnings = _values(simulation, "ni_class_1_income", year)
    without = earnings - returned

    def crosses(threshold):
        return (without < threshold * WEEKS_IN_YEAR) & (
            earnings > threshold * WEEKS_IN_YEAR
        )

    assert crosses(thresholds.upper_earnings_limit).tolist() == [
        True,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
    ]
    assert crosses(thresholds.primary_threshold)[1]
    assert crosses(thresholds.secondary_threshold)[2]
    assert returned[3] > 0
    assert earnings[3] < thresholds.secondary_threshold * WEEKS_IN_YEAR
    liable = simulation.calculate("ni_liable", year)
    secondary_liable = simulation.calculate("ni_class_1_secondary_liable", year)
    assert not liable[4] and secondary_liable[4]
    assert not liable[5] and not secondary_liable[5]
    assert returned[7] == 0


def test_rates_change_within_the_year_in_the_second_world():
    """The second world keeps the changes dated within 2041.

    If fiscal-year conversion came to cover 2041, the changes would be
    replaced by one value for the year and the property above would no longer
    test a liability whose rates differ between months.
    """
    simulation = _simulate(KNOWN_CASES[:1], "rates change within the year")
    january, december = (
        _class_1(simulation, f"2041-{month}-01") for month in ("01", "12")
    )
    assert january.rates.employee.main != december.rates.employee.main
    assert january.rates.employee.additional != december.rates.employee.additional
    assert (
        january.thresholds.upper_earnings_limit
        != december.thresholds.upper_earnings_limit
    )


def test_measures_are_deterministic():
    """Two builds of the same people give identical measures."""
    world = "current law"
    first, second = _simulate(KNOWN_CASES, world), _simulate(KNOWN_CASES, world)
    for year in WORLDS[world][1]:
        for side in ("employee", "employer"):
            variable = f"salary_sacrifice_pension_ni_{side}"
            assert np.array_equal(
                _values(first, variable, year), _values(second, variable, year)
            )

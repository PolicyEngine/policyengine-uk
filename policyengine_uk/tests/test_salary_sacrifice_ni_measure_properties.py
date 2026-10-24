"""Property-based tests: the salary sacrifice NI measures equal the change in
the complete Class 1 liability.

From 6 April 2029 salary sacrifice above the £2,000 cap enters only NIC
earnings (salary_sacrifice_pension_ni_excess), where Class 1 National
Insurance charges it. salary_sacrifice_pension_ni_employee and
salary_sacrifice_pension_ni_employer report how much of the employee and
employer liability is due to that excess.

Every test builds the same people twice: as they are, and with the NIC-only
excess removed (salary_sacrifice_pension_ni_excess set to zero, all else equal).
The second simulation gives the liability without the excess from
the model's own liability variables, so it does not depend on the formulas
under test.

Invariants, for any pay, salary sacrifice, age, statutory sick pay and
employer pension contribution:

1. Difference of complete liabilities: the employee measure equals
   ni_class_1_employee with the excess less ni_class_1_employee
   without it, and the employer measure equals the same difference in
   ni_class_1_employer.
2. Bounds: each measure lies between zero and the excess times the
   highest rate that can apply to it.
3. Exact zeros: a measure is exactly zero when there is no excess (so under
   current law before the cap), for a person not liable to primary
   contributions (employee) and for an earner on whom no secondary
   contributions are due (employer).
4. One band, one rate: when the earnings with and without the excess
   lie in the same band, the measure is that band's rate times the
   excess. This is where the earlier single-rate formulas were
   right.
5. Monotonicity: a measure never falls when the sacrifice rises.

The invariants are checked under current law (2028, before the cap, and 2029
and 2030 under it), with a hypothetical cap in 2022 to exercise the annual
full-year Category A director schedule, and in a world where the employee
rates and the upper earnings limit change within 2041 and employer pension
contributions are charged (invariant 4 under current law only: it needs one
rate and schedule for the year). Fiscal-year conversion gives every parameter
one value for each year from 2015 to 2040, so a year after 2040 is needed for
rates that differ between months; ni_class_1_employee is a monthly variable.

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
            f"{CLASS_1}.employee_scale[1].rate": {"2041-07-01.2041-12-31": 0.12},
            f"{CLASS_1}.employee_scale[2].rate": {"2041-10-01.2041-12-31": 0.05},
            f"{CLASS_1}.employee_scale[2].threshold": {"2041-04-01.2041-12-31": 1_300},
            "gov.contrib.policyengine.employer_ni."
            "exempt_employer_pension_contributions": False,
        },
        [2030, 2041],
    ),
    "full-year Category A directors": (
        {"gov.hmrc.national_insurance.salary_sacrifice_pension_cap": {"2022": 2_000}},
        [2022],
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

Row = namedtuple(
    "Row",
    "pay sacrifice more_sacrifice age sick_pay employer_pension director",
    defaults=[False],
)

# People the properties must always cover, whatever is drawn. With the £2,000
# cap: an excess that crosses the upper earnings limit, one that
# crosses the primary threshold, one that crosses the secondary threshold, one
# below every threshold, a person over State Pension age, a person under 16,
# one whose statutory sick pay takes them over the upper earnings limit,
# one with no excess, and a full-year Category A director crossing the upper
# earnings limit.
KNOWN_CASES = [
    Row(48_000, 6_000, 10_000, 40, 0, 0),
    Row(11_000, 5_000, 3_000, 40, 0, 0),
    Row(3_000, 5_000, 4_000, 40, 0, 2_000),
    Row(1_000, 3_000, 500, 40, 0, 0),
    Row(45_000, 5_000, 20_000, 70, 0, 0),
    Row(20_000, 5_000, 5_000, 15, 0, 0),
    Row(46_000, 5_000, 0, 40, 3_000, 0),
    Row(60_000, 1_500, 0, 40, 0, 0),
    Row(48_000, 6_000, 10_000, 40, 0, 0, True),
]


def _amount(maximum):
    return st.floats(0, maximum, allow_nan=False, allow_infinity=False)


# Annual thresholds in the years tested lie near these amounts (secondary
# threshold, primary threshold, upper earnings limit), so pay near them makes
# the excess cross a threshold often.
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
        director=st.booleans(),
    ),
    min_size=1,
    max_size=40,
)


def _simulate(people, world, no_excess=False):
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
                "is_full_year_category_a_director": each_year(row.director),
            }
            for name, row in zip(names, people)
        },
        "benunits": {f"benunit_{i}": {"members": [n]} for i, n in enumerate(names)},
        "households": {f"household_{i}": {"members": [n]} for i, n in enumerate(names)},
    }
    simulation = Simulation(situation=situation, reform=changes)
    if no_excess:
        for year in years:
            simulation.set_input(
                "salary_sacrifice_pension_ni_excess",
                year,
                np.zeros(len(people), dtype=np.float32),
            )
    return simulation


def _values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def _class_1(simulation, instant):
    parameters = simulation.tax_benefit_system.parameters(instant)
    return parameters.gov.hmrc.national_insurance.class_1


def _check_one_band_one_rate(simulation, year, excess):
    """Invariant 4, for a year whose rates and thresholds do not change."""
    class_1 = _class_1(simulation, f"{year}-01-01")
    employee = class_1.employee_scale.components
    employer = class_1.employer_scale.components
    primary_threshold = employee[1].threshold * WEEKS_IN_YEAR
    upper_earnings_limit = employee[2].threshold * WEEKS_IN_YEAR
    secondary_threshold = employer[1].threshold * WEEKS_IN_YEAR
    earnings = _values(simulation, "ni_class_1_income", year)
    without = earnings - excess
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
            employee[1].rate,
        ),
        (
            "employee",
            "ni_liable",
            without > upper_earnings_limit + margin,
            employee[2].rate,
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
            employer[1].rate,
        ),
    ]
    for side, liable, in_band, rate in bands:
        applies = in_band & simulation.calculate(liable, year)
        measure = _values(simulation, f"salary_sacrifice_pension_ni_{side}", year)
        np.testing.assert_allclose(
            measure[applies], rate * excess[applies], rtol=0, atol=TOLERANCE
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
    with_excess = _simulate(people, world)
    without_excess = _simulate(people, world, no_excess=True)
    for year in WORLDS[world][1]:
        excess = _values(with_excess, "salary_sacrifice_pension_ni_excess", year)
        assert np.all(
            _values(without_excess, "salary_sacrifice_pension_ni_excess", year) == 0
        )
        months = [
            _class_1(with_excess, f"{year}-{month:02d}-01")
            for month in range(1, MONTHS_IN_YEAR + 1)
        ]
        employee_rates = [
            component.rate
            for month in months
            for component in month.employee_scale.components
        ]
        for month in months:
            directors = month.directors.full_year_category_a_2022_23
            if directors.in_effect:
                employee_rates.extend(directors.employee_scale.rates)
        highest_rate = {
            "employee": max(employee_rates),
            # ni_class_1_employer is a yearly variable: it reads the rate at
            # the start of the year.
            "employer": months[0].employer_scale.components[1].rate,
        }
        for side, liable in (
            ("employee", "ni_liable"),
            ("employer", "ni_class_1_secondary_liable"),
        ):
            measure = _values(with_excess, f"salary_sacrifice_pension_ni_{side}", year)
            liability = f"ni_class_1_{side}"
            # 1. Difference of complete liabilities.
            np.testing.assert_allclose(
                measure,
                _values(with_excess, liability, year)
                - _values(without_excess, liability, year),
                rtol=0,
                atol=TOLERANCE,
            )
            # 2. Bounds.
            assert np.all(measure >= 0)
            assert np.all(measure <= highest_rate[side] * excess + TOLERANCE)
            # 3. Exact zeros.
            assert np.all(measure[excess == 0] == 0)
            assert np.all(measure[~with_excess.calculate(liable, year)] == 0)
            # 5. Monotonicity.
            assert np.all(measure[n:] >= measure[:n] - TOLERANCE)
        # 4. One band, one rate.
        if world == "current law":
            _check_one_band_one_rate(with_excess, year, excess)


def test_known_cases_cross_each_threshold_and_age_condition():
    """The pinned people are the cases their comment says they are."""
    simulation = _simulate(KNOWN_CASES, "current law")
    year = 2029
    class_1 = _class_1(simulation, f"{year}-01-01")
    employee = class_1.employee_scale.components
    secondary_threshold = class_1.employer_scale.components[1].threshold
    excess = _values(simulation, "salary_sacrifice_pension_ni_excess", year)
    earnings = _values(simulation, "ni_class_1_income", year)
    without = earnings - excess

    def crosses(threshold):
        return (without < threshold * WEEKS_IN_YEAR) & (
            earnings > threshold * WEEKS_IN_YEAR
        )

    assert crosses(employee[2].threshold).tolist() == [
        True,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        True,
    ]
    assert crosses(employee[1].threshold)[1]
    assert crosses(secondary_threshold)[2]
    assert excess[3] > 0
    assert earnings[3] < secondary_threshold * WEEKS_IN_YEAR
    liable = simulation.calculate("ni_liable", year)
    secondary_liable = simulation.calculate("ni_class_1_secondary_liable", year)
    assert not liable[4] and secondary_liable[4]
    assert not liable[5] and not secondary_liable[5]
    assert excess[7] == 0
    assert simulation.calculate("is_full_year_category_a_director", year)[8]


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
    assert (
        january.employee_scale.components[1].rate
        != december.employee_scale.components[1].rate
    )
    assert (
        january.employee_scale.components[2].rate
        != december.employee_scale.components[2].rate
    )
    assert (
        january.employee_scale.components[2].threshold
        != december.employee_scale.components[2].threshold
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

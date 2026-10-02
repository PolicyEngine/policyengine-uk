"""Property-based tests: a salary sacrifice is limited to the pay behind it.

From 6 April 2029 the salary sacrifice above the £2,000 cap returns to
employment income (salary_sacrifice_returned_to_income). The sacrifice is
first limited to the person's pay
(pension_contributions_via_salary_sacrifice_from_pay), so an input sacrifice
with no pay behind it cannot create pay.

Invariants, for any generated pay and salary sacrifice, in a year before the
cap (2028) and two years under it (2029, 2030):

1. Bounds: the sacrifice from pay equals min(max(sacrifice, 0), max(pay, 0)).
2. Conservation: the capped sacrifice plus the amount returned to income
   equals the sacrifice from pay.
3. No pay, no gain: a person without pay has no employment income, nothing
   returned and no National Insurance charge on a returned amount, whatever
   their sacrifice input.
4. Nothing is returned before the cap starts.
5. Accounting: employment income equals pay plus the amount returned plus
   the broad-base haircut.
6. Unchanged within pay: when the sacrifice is within pay, the amount
   returned is the sacrifice above the cap, as before the limit.
7. Monotonicity: the amount returned never falls when the sacrifice or the
   pay rises.

The simulations go through policyengine_uk.Simulation, which moves an
employment_income input to employment_income_before_lsr as it does for a
dataset or a household calculation.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEARS = [2028, 2029, 2030]
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Zero pay and a zero sacrifice are the cases the limit exists for, so they
# are drawn often.
pay = st.one_of(
    st.just(0.0), st.floats(0, 200_000, allow_nan=False, allow_infinity=False)
)
sacrifice = st.one_of(
    st.just(0.0), st.floats(0, 100_000, allow_nan=False, allow_infinity=False)
)
increase = st.floats(0, 50_000, allow_nan=False, allow_infinity=False)
people = st.lists(st.tuples(pay, sacrifice, increase, increase), min_size=1, max_size=8)


def _simulate(pays, sacrifices):
    """One single-adult household per (pay, sacrifice) pair."""
    names = [f"person_{i}" for i in range(len(pays))]
    situation = {
        "people": {
            name: {
                "age": {str(year): 40 for year in YEARS},
                "employment_income": {str(year): pays[i] for year in YEARS},
                "pension_contributions_via_salary_sacrifice": {
                    str(year): sacrifices[i] for year in YEARS
                },
            }
            for i, name in enumerate(names)
        },
        "benunits": {f"benunit_{i}": {"members": [n]} for i, n in enumerate(names)},
        "households": {f"household_{i}": {"members": [n]} for i, n in enumerate(names)},
    }
    return Simulation(situation=situation)


def _values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def _cap(simulation, year):
    parameters = simulation.tax_benefit_system.parameters(year)
    return parameters.gov.hmrc.national_insurance.salary_sacrifice_pension_cap


@PROPERTY_SETTINGS
@given(people)
def test_salary_sacrifice_is_limited_to_pay(rows):
    pays = np.array([row[0] for row in rows])
    sacrifices = np.array([row[1] for row in rows])
    simulation = _simulate(pays, sacrifices)
    for year in YEARS:
        from_pay = _values(
            simulation, "pension_contributions_via_salary_sacrifice_from_pay", year
        )
        adjusted = _values(
            simulation, "pension_contributions_via_salary_sacrifice_adjusted", year
        )
        returned = _values(simulation, "salary_sacrifice_returned_to_income", year)
        employment_income = _values(simulation, "employment_income", year)
        haircut = _values(simulation, "salary_sacrifice_broad_base_haircut", year)
        cap = _cap(simulation, year)

        # 1. Bounds.
        np.testing.assert_allclose(
            from_pay, np.minimum(sacrifices, pays), rtol=1e-6, atol=1e-2
        )
        assert np.all(returned >= 0)
        # 2. Conservation.
        np.testing.assert_allclose(adjusted + returned, from_pay, rtol=1e-6, atol=1e-2)
        # 3. No pay, no gain.
        unpaid = pays <= 0
        assert np.all(employment_income[unpaid] == 0)
        assert np.all(returned[unpaid] == 0)
        for charge in (
            "salary_sacrifice_pension_ni_employee",
            "salary_sacrifice_pension_ni_employer",
        ):
            assert np.all(_values(simulation, charge, year)[unpaid] == 0)
        # 4. Nothing is returned before the cap starts.
        if np.isinf(cap):
            assert np.all(returned == 0)
        # 5. Accounting.
        np.testing.assert_allclose(
            employment_income, pays + returned + haircut, rtol=1e-6, atol=1e-2
        )
        # 6. Unchanged within pay.
        within = sacrifices <= pays
        if not np.isinf(cap):
            np.testing.assert_allclose(
                returned[within],
                np.maximum(sacrifices[within] - cap, 0),
                rtol=1e-6,
                atol=1e-2,
            )


@PROPERTY_SETTINGS
@given(people)
def test_returned_income_never_falls_with_sacrifice_or_pay(rows):
    n = len(rows)
    pays = np.array([row[0] for row in rows])
    sacrifices = np.array([row[1] for row in rows])
    more_sacrifice = np.array([row[2] for row in rows])
    more_pay = np.array([row[3] for row in rows])
    # The same people three times: as drawn, with a larger sacrifice, and
    # with more pay.
    simulation = _simulate(
        np.concatenate([pays, pays, pays + more_pay]),
        np.concatenate([sacrifices, sacrifices + more_sacrifice, sacrifices]),
    )
    for year in YEARS:
        returned = _values(simulation, "salary_sacrifice_returned_to_income", year)
        base, larger_sacrifice, larger_pay = (
            returned[:n],
            returned[n : 2 * n],
            returned[2 * n :],
        )
        assert np.all(larger_sacrifice >= base - 1e-2)
        assert np.all(larger_pay >= base - 1e-2)

"""Only people with pay have salary sacrifice and its NIC-only excess.

The capped exempt amount plus NIC-only excess conserves the full employer
contribution. Ordinary employment income remains cash pay plus the existing
broad-base haircut. Generated pay, no-pay and whole-bonus inputs retain the
existing UKSimulation input convention and branch/reset compatibility.
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
def test_only_people_with_pay_have_a_salary_sacrifice(rows):
    pays = np.array([row[0] for row in rows])
    sacrifices = np.array([row[1] for row in rows])
    drawn_pays = pays
    simulation = _simulate(drawn_pays, sacrifices)
    for year in YEARS:
        # The pay the model stores (float32: tiny draws round to zero). It
        # must be the pay put in: Simulation moves employment_income there.
        pays = _values(simulation, "employment_income_before_lsr", year)
        np.testing.assert_allclose(pays, drawn_pays, rtol=1e-6, atol=1e-2)
        from_pay = _values(
            simulation, "pension_contributions_via_salary_sacrifice_from_pay", year
        )
        adjusted = _values(
            simulation, "pension_contributions_via_salary_sacrifice_adjusted", year
        )
        returned = _values(simulation, "salary_sacrifice_pension_ni_excess", year)
        employment_income = _values(simulation, "employment_income", year)
        haircut = _values(simulation, "salary_sacrifice_broad_base_haircut", year)
        cap = _cap(simulation, year)

        # 1. Definition.
        np.testing.assert_allclose(
            from_pay, np.where(pays > 0, sacrifices, 0), rtol=1e-6, atol=1e-2
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
        # 5. Ordinary cash-pay accounting; the excess is NIC-only.
        np.testing.assert_allclose(
            employment_income, pays + haircut, rtol=1e-6, atol=1e-2
        )
        # 6. Unchanged with pay.
        paid = pays > 0
        if not np.isinf(cap):
            np.testing.assert_allclose(
                returned[paid],
                np.maximum(sacrifices[paid] - cap, 0),
                rtol=1e-6,
                atol=1e-2,
            )


@PROPERTY_SETTINGS
@given(people)
def test_ni_excess_never_falls_with_sacrifice_or_pay(rows):
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
        returned = _values(simulation, "salary_sacrifice_pension_ni_excess", year)
        base, larger_sacrifice, larger_pay = (
            returned[:n],
            returned[n : 2 * n],
            returned[2 * n :],
        )
        assert np.all(larger_sacrifice >= base - 1e-2)
        assert np.all(larger_pay >= base - 1e-2)


def test_pay_set_after_construction_keeps_the_sacrifice():
    """Branches that reset employment_income keep the pay the sacrifice needs.

    The marginal tax rate branches and the participation response set
    employment_income on a simulation built with pay; the original pay stays
    in employment_income_before_lsr, so the sacrifice is still recognised.
    """
    simulation = _simulate(np.array([30_000.0]), np.array([6_000.0]))
    simulation.set_input("employment_income", 2030, np.array([0.0]))
    assert _values(
        simulation, "pension_contributions_via_salary_sacrifice_from_pay", 2030
    ) == [6_000]
    assert _values(simulation, "salary_sacrifice_pension_ni_excess", 2030) == [4_000]

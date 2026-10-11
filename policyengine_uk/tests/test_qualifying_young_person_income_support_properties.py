"""Income Support in a young person's own right and qualifying young person
status.

A person receiving Income Support is not a qualifying young person for
Pension Credit (SPC Regs 2002 reg. 4A(5)), Child Benefit (Child Benefit
(General) Regulations 2006 reg. 8(2)(a)) or Child Tax Credit (CTC Regs 2002
reg. 5(4)(c)). Universal Credit's list (UC Regs 2013 reg. 5(5)) does not
include Income Support.

Invariants:

1. Over every combination of age, education, training, the other own-right
   benefits and the 16th-birthday fact: with Income Support in their own
   right, nobody is a Pension Credit, Child Benefit or Child Tax Credit
   qualifying young person.
2. Without it, each of those three statuses is exactly what it is when the
   input is left alone, so nothing else changes.
3. Universal Credit status never depends on it.
4. Without it, Pension Credit and Universal Credit agree on every combination;
   with it, Pension Credit is the narrower.
5. By default the input is the person's own reported Income Support while
   Income Support is in payment (to 2025-26), and false after.
"""

from itertools import product
from unittest.mock import patch

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

YEAR = 2025
_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
SIXTEEN = "is_before_first_september_following_16th_birthday"
INCOME_SUPPORT = "receives_income_support_in_own_right"
EXCLUDING = ("pension_credit", "child_benefit", "child_tax_credit")
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def simulate(people, year=YEAR):
    """Each person alone in a benefit unit: the status tests are personal."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i in range(len(people)):
        situation["people"][f"p{i}"] = {}
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {"members": [f"p{i}"]}
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    variables = people[0].keys()
    assert all(p.keys() == variables for p in people)
    for variable in variables:
        sim.set_input(variable, year, [p[variable] for p in people])
    sim.input_variables = list(variables)
    sim.reset_calculations()
    return sim


def status(sim, programme, year=YEAR):
    return sim.calculate(f"is_qualifying_young_person_for_{programme}", year)


BASE = [
    {
        "age": age,
        "current_education": education,
        "is_in_approved_training": training,
        "receives_benefits_in_own_right": own_right,
        "age_started_or_accepted_current_education_or_training": 17,
        SIXTEEN: sixteen,
    }
    for age, education, training, own_right, sixteen in product(
        range(14, 22), EDUCATIONS, (False, True), (False, True), (False, True)
    )
]


def test_income_support_ends_three_statuses_and_not_universal_credit():
    untouched = simulate(BASE)
    without = simulate([dict(p, **{INCOME_SUPPORT: False}) for p in BASE])
    with_it = simulate([dict(p, **{INCOME_SUPPORT: True}) for p in BASE])
    for programme in EXCLUDING:
        before = status(untouched, programme)
        # Not vacuous: there is a status to lose.
        assert before.any(), programme
        # Invariant 1.
        assert not status(with_it, programme).any(), programme
        # Invariant 2.
        np.testing.assert_array_equal(status(without, programme), before)
    # Invariant 3.
    universal_credit = status(untouched, "universal_credit")
    np.testing.assert_array_equal(status(with_it, "universal_credit"), universal_credit)
    np.testing.assert_array_equal(status(without, "universal_credit"), universal_credit)
    # Invariant 4.
    np.testing.assert_array_equal(status(without, "pension_credit"), universal_credit)
    assert (status(with_it, "pension_credit") <= universal_credit).all()
    assert universal_credit.any()


@SETTINGS
@given(
    st.lists(
        st.tuples(st.integers(0, 60), st.sampled_from([0, 0, 1, 2_500, 9_000])),
        min_size=1,
        max_size=40,
    ),
    st.sampled_from([2021, 2024, 2025, 2026, 2028]),
)
def test_default_follows_reported_income_support_while_it_is_paid(rows, year):
    # Invariant 5. Income Support paid its last awards on 31 March 2026.
    people = [{"age": age, "income_support_reported": amount} for age, amount in rows]
    sim = simulate(people, year)
    expected = [year <= 2025 and amount > 0 for _, amount in rows]
    np.testing.assert_array_equal(sim.calculate(INCOME_SUPPORT, year), expected)

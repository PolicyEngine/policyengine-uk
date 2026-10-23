"""Property-based test of the fixed employer cost response to an employer NI
reform.

With full employee incidence (the default), employer_ni_fixed_employer_cost_change
moves pay so that the employer's cost is unchanged by the reform. For a person
with pay P (including the salary sacrifice cap's broad-base haircut), statutory
pay S, employer pension contributions E and salary sacrifice above the cap X
(NIC earnings only, from 2029), the cost under a schedule with employer rate r
and secondary threshold T (the secondary threshold, or the UST or AUST where
SSCBA 1992 s.9A or s.9B zero-rates the earner) is

    cost = P + S + E + r * max(P + S + X + E - E_exempt - T, 0)

with E_exempt = E when employer pension contributions are NI-exempt. The cost is
continuous and increasing in P, so for any reform of r, T or the zero-rate
thresholds, and any person with pay before the reform:

1. Agreement: baseline_employer_cost equals the baseline simulation's
   employer_cost, and adjusted_employer_cost the reformed simulation's.
2. Conservation: if the reformed pay is positive, adjusted_employer_cost equals
   baseline_employer_cost.
3. The zero-pay floor: if holding cost fixed would need negative pay, because
   statutory pay, pension contributions and the excess alone cost more under
   the reform, reformed pay is zero, so the reformed cost is at least the
   baseline cost.

The population mixes earners under 21, relevant apprentices under 25 and other
earners, each with statutory pay that can carry NIC earnings over a threshold
that pay alone is below, and a salary sacrifice that the 2029 cap can make
partly NIC-able.

Comparisons allow float32 rounding: the model stores values as float32.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

CLASS_1 = "gov.hmrc.national_insurance.class_1"
YEARS = [2026, 2027, 2028, 2029, 2030]
# (age, is_apprentice): zero-rated under 21 (s.9A), zero-rated relevant
# apprentices under 25 (s.9B), and earners with the ordinary threshold.
AGE_GROUPS = [
    (18, False),
    (20, False),
    (21, False),
    (24, True),
    (25, True),
    (40, False),
]
STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def tolerance(*amounts):
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


@st.composite
def populations(draw):
    year = draw(st.sampled_from(YEARS))
    # The reform always sets the employer rate (a reform is needed for the
    # baseline employer cost; a rate equal to the baseline's leaves cost
    # unchanged). None keeps the baseline threshold. Thresholds are weekly, as
    # the parameters store them, and apply from the year drawn.
    period = f"{year}-01-01.2100-12-31"
    reform = {
        f"{CLASS_1}.employer_scale[1].rate": {
            period: draw(st.floats(0, 0.3, allow_nan=False))
        }
    }
    secondary = draw(st.one_of(st.none(), st.floats(0, 1_500, allow_nan=False)))
    if secondary is not None:
        reform[f"{CLASS_1}.employer_scale[1].threshold"] = {period: secondary}
    relief = draw(st.one_of(st.none(), st.floats(0, 2_000, allow_nan=False)))
    if relief is not None:
        for name in [
            "upper_secondary_threshold",
            "apprentice_upper_secondary_threshold",
        ]:
            reform[f"{CLASS_1}.thresholds.{name}"] = {period: relief}
    people = draw(
        st.lists(
            st.tuples(
                st.sampled_from(AGE_GROUPS),
                st.floats(1, 150_000, allow_nan=False),
                st.sampled_from(STATUTORY_PAY),
                st.floats(0, 10_000, allow_nan=False),
                st.floats(0, 10_000, allow_nan=False),
                st.floats(0, 10_000, allow_nan=False),
            ),
            min_size=1,
            max_size=12,
        )
    )
    return year, reform, people


def simulate(year, reform, people):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, (
        (age, apprentice),
        pay,
        statutory,
        statutory_pay,
        pension,
        sacrifice,
    ) in enumerate(people):
        name = f"person_{i}"
        situation["people"][name] = {
            "age": {year: age},
            "is_apprentice": {year: apprentice},
            "employment_income": {year: pay},
            statutory: {year: statutory_pay},
            "employer_pension_contributions": {year: pension},
            "pension_contributions_via_salary_sacrifice": {year: sacrifice},
        }
        situation["benunits"][f"benunit_{i}"] = {"members": [name]}
        situation["households"][f"household_{i}"] = {"members": [name]}
    return Simulation(situation=situation, reform=reform)


@PROPERTY_SETTINGS
@given(populations())
def test_fixed_employer_cost_is_conserved_or_pay_is_floored(population):
    year, reform, people = population
    simulation = simulate(year, reform, people)
    pay = np.asarray(simulation.calculate("employment_income", year), dtype=float)
    baseline_cost = np.asarray(
        simulation.calculate("baseline_employer_cost", year), dtype=float
    )
    adjusted_cost = np.asarray(
        simulation.calculate("adjusted_employer_cost", year), dtype=float
    )
    actual_baseline_cost = np.asarray(
        simulation.baseline.calculate("employer_cost", year), dtype=float
    )
    actual_cost = np.asarray(simulation.calculate("employer_cost", year), dtype=float)
    for i in range(len(people)):
        tol = tolerance(baseline_cost[i], adjusted_cost[i])
        assert abs(baseline_cost[i] - actual_baseline_cost[i]) <= tol, (
            people[i],
            reform,
            baseline_cost[i],
            actual_baseline_cost[i],
        )
        assert abs(adjusted_cost[i] - actual_cost[i]) <= tol, (
            people[i],
            reform,
            adjusted_cost[i],
            actual_cost[i],
        )
        assert pay[i] >= -tol
        if pay[i] > tol:
            assert abs(adjusted_cost[i] - baseline_cost[i]) <= tol, (
                people[i],
                reform,
                pay[i],
                baseline_cost[i],
                adjusted_cost[i],
            )
        else:
            assert adjusted_cost[i] >= baseline_cost[i] - tol, (
                people[i],
                reform,
                pay[i],
                baseline_cost[i],
                adjusted_cost[i],
            )

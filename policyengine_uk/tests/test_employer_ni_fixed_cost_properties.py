"""Property-based test of the fixed employer cost response to an employer NI
reform.

With full employee incidence (the default), employer_ni_fixed_employer_cost_change
moves pay so that the employer's cost is unchanged by the reform. For a person
with pay P (including salary sacrifice returned to ordinary pay and the salary
sacrifice cap's broad-base haircut), statutory pay S, employer pension
contributions E and salary sacrifice above the cap X (NIC earnings only, from
2029), the cost under a schedule with employer rate r and secondary threshold T
(the secondary threshold, or the UST or AUST where SSCBA 1992 s.9A or s.9B
zero-rates the earner) is

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
that pay alone is below, a salary sacrifice that the 2029 cap can make partly
NIC-able, and pay returned from salary sacrifice. Explicit examples make sure
every run covers a sacrifice above the cap in 2029 and 2030, returned pay and
the zero-pay floor, which 25 drawn examples need not reach.

Comparisons allow float32 rounding: the model stores values as float32.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
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


def rate_reform(year, rate, secondary=None):
    period = f"{year}-01-01.2100-12-31"
    reform = {f"{CLASS_1}.employer_scale[1].rate": {period: rate}}
    if secondary is not None:
        reform[f"{CLASS_1}.employer_scale[1].threshold"] = {period: secondary}
    return reform


# Each person: (age, is_apprentice), pay, statutory pay variable and amount,
# employer pension contributions, salary sacrifice, returned pay.
EXAMPLES = [
    # A sacrifice above the £2,000 cap in 2029: María's case (aged 20,
    # zero-rated up to the UST) and an earner aged 40.
    (
        2029,
        rate_reform(2029, 0.16),
        [
            ((20, False), 49_000.0, "statutory_sick_pay", 0.0, 2_000.0, 5_000.0, 0.0),
            ((40, False), 60_000.0, "statutory_sick_pay", 0.0, 2_000.0, 8_000.0, 0.0),
        ],
    ),
    # 2030, with returned pay and a new secondary threshold of £100 a week.
    (
        2030,
        rate_reform(2030, 0.2, 100.0),
        [
            (
                (24, True),
                45_000.0,
                "statutory_paternity_pay",
                1_000.0,
                3_000.0,
                6_000.0,
                1_500.0,
            ),
            (
                (21, False),
                30_000.0,
                "statutory_sick_pay",
                0.0,
                0.0,
                4_000.0,
                2_500.0,
            ),
        ],
    ),
    # The zero-pay floor: £1 of pay with £10,000 each of statutory maternity
    # pay and employer pension, at 30% from a zero threshold. In 2026 the
    # baseline cost is 20,001 + 0.15 x (10,001 - 5,000) = £20,751.15, and at
    # zero pay the reformed cost is 20,000 + 0.3 x 10,000 = £23,000. In 2029 a
    # £10,000 sacrifice adds an £8,000 excess, and returned pay is floored too.
    (
        2026,
        rate_reform(2026, 0.3, 0.0),
        [((40, False), 1.0, "statutory_maternity_pay", 10_000.0, 10_000.0, 0.0, 0.0)],
    ),
    (
        2029,
        rate_reform(2029, 0.3, 0.0),
        [
            (
                (40, False),
                1.0,
                "statutory_maternity_pay",
                10_000.0,
                10_000.0,
                10_000.0,
                0.0,
            ),
            (
                (40, False),
                1.0,
                "statutory_maternity_pay",
                10_000.0,
                10_000.0,
                10_000.0,
                500.0,
            ),
        ],
    ),
]


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
                st.one_of(st.just(0.0), st.floats(0, 10_000, allow_nan=False)),
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
        returned,
    ) in enumerate(people):
        name = f"person_{i}"
        situation["people"][name] = {
            "age": {year: age},
            "is_apprentice": {year: apprentice},
            "employment_income": {year: pay},
            statutory: {year: statutory_pay},
            "employer_pension_contributions": {year: pension},
            "pension_contributions_via_salary_sacrifice": {year: sacrifice},
            "salary_sacrifice_returned_to_income": {year: returned},
        }
        situation["benunits"][f"benunit_{i}"] = {"members": [name]}
        situation["households"][f"household_{i}"] = {"members": [name]}
    return Simulation(situation=situation, reform=reform)


@PROPERTY_SETTINGS
@given(populations())
@example(population=EXAMPLES[0])
@example(population=EXAMPLES[1])
@example(population=EXAMPLES[2])
@example(population=EXAMPLES[3])
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

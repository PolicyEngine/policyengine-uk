"""Property-based tests for the age conditions on Class 1 National Insurance.

SSCBA 1992 s.6(1) makes primary and secondary Class 1 contributions payable on
earnings of an earner over 16. s.6(3) ends primary contributions at
pensionable age "without prejudice to any liability to pay secondary Class 1
contributions". So, for any secondary threshold ST >= 0, employer rate r >= 0,
earnings e >= 0 and age a:

1. Secondary Class 1 ignores age above 16: for a >= 16, ni_class_1_employer
   equals r * max(e - 52 * ST, 0), computed exactly. That holds above state
   pension age too, so it equals the amount for a working-age earner with the
   same earnings.
2. Nothing under 16: for a < 16, both ni_class_1_employer and
   ni_class_1_employee are zero.
3. Primary Class 1 stops at state pension age: when is_SP_age holds,
   ni_class_1_employee is zero.

Comparisons allow float32 rounding: the model stores values as float32.
"""

from fractions import Fraction

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

CLASS_1 = "gov.hmrc.national_insurance.class_1"
YEARS = list(range(2016, 2031))
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
    policy = dict(
        year=draw(st.sampled_from(YEARS)),
        # None keeps the baseline threshold and rate for that year.
        secondary_threshold=draw(
            st.one_of(st.none(), st.floats(0, 1_000, allow_nan=False))
        ),
        employer_rate=draw(st.one_of(st.none(), st.floats(0, 0.3, allow_nan=False))),
    )
    people = draw(
        st.lists(
            st.tuples(
                st.integers(0, 100),
                st.one_of(
                    st.just(0.0),
                    st.floats(0, 500_000, allow_nan=False, allow_infinity=False),
                    st.integers(0, 500_000).map(float),
                ),
            ),
            min_size=1,
            max_size=12,
        )
    )
    return policy, people


def simulate(policy, people):
    year = policy["year"]
    situation = {
        "people": {
            f"p{i}": {
                "age": {year: age},
                "employment_income": {year: earnings},
            }
            for i, (age, earnings) in enumerate(people)
        },
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(people))},
        "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(people))},
    }
    # A bare reform value only applies from 2023, so give an explicit range.
    all_years = "2000-01-01.2100-12-31"
    reform = {}
    if policy["secondary_threshold"] is not None:
        reform[f"{CLASS_1}.thresholds.secondary_threshold"] = {
            all_years: policy["secondary_threshold"]
        }
    if policy["employer_rate"] is not None:
        reform[f"{CLASS_1}.rates.employer"] = {all_years: policy["employer_rate"]}
    sim = Simulation(situation=situation, reform=reform or None)
    values = {
        variable: sim.calculate(variable, year)
        for variable in [
            "age",
            "is_SP_age",
            "ni_class_1_income",
            "ni_class_1_employee",
            "ni_class_1_employer",
        ]
    }
    class_1 = sim.tax_benefit_system.parameters(
        f"{year}-01-01"
    ).gov.hmrc.national_insurance.class_1
    values["secondary_threshold"] = class_1.thresholds.secondary_threshold
    values["employer_rate"] = class_1.rates.employer
    return values


def statutory_secondary(earnings, weekly_threshold, rate):
    """Secondary Class 1 on annual earnings, in exact arithmetic.

    The model annualises the weekly secondary threshold as 52 weeks.
    """
    threshold = 52 * Fraction(float(weekly_threshold))
    return Fraction(float(rate)) * max(Fraction(float(earnings)) - threshold, 0)


@PROPERTY_SETTINGS
@given(populations())
def test_secondary_class_1_ignores_age_above_16(population):
    policy, people = population
    values = simulate(policy, people)
    for i, (age, _) in enumerate(people):
        model = float(values["ni_class_1_employer"][i])
        earnings = float(values["ni_class_1_income"][i])
        if age < 16:
            assert model == 0
            continue
        expected = statutory_secondary(
            earnings, values["secondary_threshold"], values["employer_rate"]
        )
        assert abs(model - float(expected)) <= tolerance(expected, earnings), (
            policy,
            age,
            earnings,
            model,
            float(expected),
        )


@PROPERTY_SETTINGS
@given(populations())
def test_primary_class_1_stops_at_state_pension_age(population):
    policy, people = population
    values = simulate(policy, people)
    for i, (age, _) in enumerate(people):
        if age < 16 or values["is_SP_age"][i]:
            assert float(values["ni_class_1_employee"][i]) == 0, (policy, age)

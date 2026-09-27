"""Property-based tests for Class 4 National Insurance (#1878).

Invariants, for any thresholds 0 <= LPL < UPL, rates >= 0, and profits >= 0:

1. Statute when the maximum cannot bind: with no primary Class 1 or Class 2
   contributions payable, regulation 100 does not apply, so ni_class_4 equals
   main * clamp(p - LPL, 0, UPL - LPL) + additional * max(p - UPL, 0).
2. Differential: for everyone, ni_class_4 equals an exact-rational
   implementation of s.15(3) SSCBA 1992 capped by the literal regulation 100
   steps (with the Case 1 comparison done exactly). The one exception is a
   Case 1 tie that holds in real numbers but not in binary (before April
   2024: 53 x weekly Class 2 = 2 x (Class 1 + Class 2), UPL below the small
   profits threshold); the model then follows the real-valued tie.
3. The maximum only ever reduces liability: 0 <= ni_class_4 <= the
   pre-maximum amount.
4. Monotonicity: with employment income held fixed, ni_class_4 is
   non-decreasing in self-employment profits wherever Class 2 does not
   change. Before April 2024 regulation 100 subtracts Class 2, so crossing
   the small profits threshold can lower Class 4; Class 2 + Class 4 is then
   still non-decreasing when the main rate is at least the additional rate.

Class 2 counts in regulation 100 only before 6 April 2024 (SI 2024/377).

Comparisons allow float32 rounding: the model stores values as float32.
"""

from fractions import Fraction

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

CLASS_4 = "gov.hmrc.national_insurance.class_4"
CLASS_2_FLAT_RATE = "gov.hmrc.national_insurance.class_2.flat_rate"
YEARS = [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def tolerance(*amounts):
    # float32 has a 24-bit significand: a few ulps of the largest amount
    # involved, plus a penny.
    return 0.01 + 4e-7 * max(abs(float(a)) for a in amounts)


@st.composite
def class_4_policies(draw):
    lpl = draw(st.floats(0, 60_000, allow_nan=False, allow_infinity=False))
    band = draw(
        st.one_of(
            st.floats(1, 150_000, allow_nan=False, allow_infinity=False),
            st.just(37_700.0),
        )
    )
    main_rate = draw(st.one_of(st.just(0.0), st.floats(0.001, 0.2)))
    additional_rate = draw(st.one_of(st.just(0.0), st.floats(0.001, 0.2)))
    # None keeps the baseline Class 2 rate (zero from April 2024).
    class_2_flat_rate = draw(st.one_of(st.none(), st.floats(0.01, 10)))
    return dict(
        year=draw(st.sampled_from(YEARS)),
        lpl=lpl,
        upl=lpl + band,
        main_rate=main_rate,
        additional_rate=additional_rate,
        class_2_flat_rate=class_2_flat_rate,
    )


def profit_values(policy):
    lpl, upl = policy["lpl"], policy["upl"]
    near_limits = [
        lpl,
        upl,
        float(np.nextafter(np.float32(upl), np.float32(np.inf))),
        upl + 0.7,
        upl + 1,
        np.ceil(upl),
    ]
    return st.one_of(
        st.floats(0, 2_000_000, allow_nan=False, allow_infinity=False),
        st.integers(0, 2_000_000).map(float),
        st.sampled_from(near_limits),
    )


@st.composite
def populations(draw):
    policy = draw(class_4_policies())
    people = draw(
        st.lists(
            st.tuples(
                profit_values(policy),
                st.one_of(
                    st.just(0.0),
                    st.floats(0, 200_000, allow_nan=False, allow_infinity=False),
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
                "age": {year: 40},
                "self_employment_income": {year: profits},
                "employment_income": {year: employment},
            }
            for i, (profits, employment) in enumerate(people)
        },
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(people))},
        "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(people))},
    }
    # A bare reform value only applies from 2023, so give an explicit range.
    all_years = "2000-01-01.2100-12-31"
    reform = {
        f"{CLASS_4}.thresholds.lower_profits_limit": {all_years: policy["lpl"]},
        f"{CLASS_4}.thresholds.upper_profits_limit": {all_years: policy["upl"]},
        f"{CLASS_4}.rates.main": {all_years: policy["main_rate"]},
        f"{CLASS_4}.rates.additional": {all_years: policy["additional_rate"]},
    }
    if policy.get("class_2_flat_rate") is not None:
        reform[CLASS_2_FLAT_RATE] = {all_years: policy["class_2_flat_rate"]}
    sim = Simulation(situation=situation, reform=reform)
    values = {
        variable: sim.calculate(variable, year)
        for variable in [
            "ni_class_4",
            "self_employment_income",
            "ni_class_1_employee",
            "ni_class_1_employee_primary",
            "ni_class_2",
        ]
    }
    ni = sim.tax_benefit_system.parameters(f"{year}-01-01").gov.hmrc.national_insurance
    assert ni.class_4.thresholds.lower_profits_limit == policy["lpl"]
    assert ni.class_4.thresholds.upper_profits_limit == policy["upl"]
    assert ni.class_4.rates.main == policy["main_rate"]
    assert ni.class_4.rates.additional == policy["additional_rate"]
    values["class_2_flat_rate"] = ni.class_2.flat_rate
    values["year"] = year
    return values


def exact(x):
    return Fraction(float(x))


def statutory_class_4(profits, lpl, upl, main_rate, additional_rate):
    """s.15(3) SSCBA 1992 in exact arithmetic."""
    return main_rate * min(max(profits - lpl, 0), upl - lpl) + additional_rate * max(
        profits - upl, 0
    )


def reference_class_4(policy, values, i):
    """Class 4 liability: s.15(3) capped by regulation 100, exactly.

    Class 4 profits are self-employment income less employee Class 1 NI, as
    the model defines them; regulation 100 Steps Six and Nine use
    self-employment income, as the model does.
    """
    lpl, upl = exact(policy["lpl"]), exact(policy["upl"])
    main_rate = exact(policy["main_rate"])
    additional_rate = exact(policy["additional_rate"])
    self_employment_income = exact(values["self_employment_income"][i])
    employee_ni = exact(values["ni_class_1_employee"][i])
    class_1 = exact(values["ni_class_1_employee_primary"][i])
    class_2 = exact(values["ni_class_2"][i])
    profits = self_employment_income - employee_ni

    main_band = main_rate * min(max(profits - lpl, 0), upl - lpl)
    pre_maximum = main_band + additional_rate * max(profits - upl, 0)
    # SI 2024/377 removed Class 2 from regulation 100 from 6 April 2024.
    class_2_counts = values["year"] < 2024
    if not class_2_counts:
        class_2 = 0
    if not (employee_ni > 0 or class_2 > 0):
        # Regulation 100(1): no Class 1 (or counted Class 2), no maximum.
        return max(pre_maximum, 0)

    step_2 = (upl - lpl) * main_rate
    step_3 = step_2 + 53 * exact(values["class_2_flat_rate"]) * class_2_counts
    step_4 = step_3 - class_2 - class_1
    if step_4 >= 0 and step_4 > class_1 + class_2 + main_band:
        maximum = step_4
    else:
        step_4 = max(step_4, 0)
        step_6 = min(upl, self_employment_income) - lpl
        if main_rate > 0:
            step_7 = max(step_6 - step_4 / main_rate, 0)
        else:
            step_7 = 0
        step_8 = step_7 * additional_rate
        step_9 = max(self_employment_income - upl, 0) * additional_rate
        maximum = step_4 + step_8 + step_9
    return max(min(pre_maximum, maximum), 0)


@PROPERTY_SETTINGS
@given(populations())
def test_class_4_matches_statute_and_exact_regulation_100(population):
    policy, people = population
    values = simulate(policy, people)
    lpl, upl = policy["lpl"], policy["upl"]
    for i in range(len(people)):
        model = float(values["ni_class_4"][i])
        profits = float(values["self_employment_income"][i])
        tol = tolerance(profits, upl, model)

        reference = float(reference_class_4(policy, values, i))
        assert abs(model - reference) <= tol, (i, model, reference)

        class_4_profits = profits - float(values["ni_class_1_employee"][i])
        pre_maximum = float(
            statutory_class_4(
                exact(class_4_profits),
                exact(lpl),
                exact(upl),
                exact(policy["main_rate"]),
                exact(policy["additional_rate"]),
            )
        )
        assert -tol <= model <= pre_maximum + tol, (i, model, pre_maximum)

        if values["ni_class_1_employee"][i] == 0 and values["ni_class_2"][i] == 0:
            assert abs(model - pre_maximum) <= tol, (i, model, pre_maximum)


@PROPERTY_SETTINGS
@given(
    class_4_policies(),
    st.lists(
        st.floats(0, 1_000_000, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=15,
    ),
    st.one_of(
        st.just(0.0),
        st.floats(0, 200_000, allow_nan=False, allow_infinity=False),
    ),
)
def test_class_4_is_non_decreasing_in_profits(policy, profits, employment):
    upl = policy["upl"]
    near_limits = [upl - 1, upl, upl + 0.7, upl + 1, np.ceil(upl), 2 * upl]
    ordered = sorted(profits + near_limits)
    values = simulate(policy, [(p, employment) for p in ordered])
    class_4 = values["ni_class_4"].astype(np.float64)
    class_2 = values["ni_class_2"].astype(np.float64)
    total = class_2 + class_4
    for i, p in enumerate(ordered[1:], start=1):
        tol = tolerance(p, upl, class_4[i])
        if class_2[i] == class_2[i - 1]:
            assert class_4[i] >= class_4[i - 1] - tol, (p, class_4[i - 1], class_4[i])
        if policy["main_rate"] >= policy["additional_rate"]:
            assert total[i] >= total[i - 1] - tol, (p, total[i - 1], total[i])

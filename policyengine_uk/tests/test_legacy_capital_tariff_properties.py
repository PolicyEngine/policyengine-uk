"""Property tests for tariff income from capital in the legacy means tests.

Income Support (IS Regs 1987 reg 53), income-based JSA (JSA Regs 1996 reg
116) and income-related ESA (ESA Regs 2008 reg 118), and the same regulations
of the Northern Ireland rules, treat capital above a lower threshold as a
weekly income of £1 for each complete £250 and £1 for any part of £250 left
over. The lower threshold is £6,000, or £10,000 where the claimant lives
permanently in prescribed accommodation (IS reg 53(1A)-(1C), JSA reg
116(1A)-(1C), ESA reg 118(2)-(4)). Working-age Housing Benefit (HB Regs 2006
reg 52) uses the same figures, with its own residential circumstances.

Invariants, for any capital on a penny grid and either exception status:

1. Reference: each programme's tariff income is 52 x ceil(max(0, capital -
   threshold) / 250) x £1, with the threshold the regulation gives.
2. Monotone: tariff income never falls as capital rises.
3. Bounded: tariff income with the prescribed accommodation exception never
   exceeds the ordinary tariff income on the same capital.
4. Differential: the four programmes whose tariff parameters match give the
   same tariff income at every capital level (Housing Benefit with its own
   exception set the same way).
"""

from math import ceil
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

WEEKS_IN_YEAR = 52
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
PARAMETERS = Path(__file__).resolve().parents[1] / "parameters/gov/dwp"

# Each programme: its tariff income variable, the capital it reads, the
# exception input that selects the higher threshold, and its parameters.
PROGRAMMES = {
    "esa_income": (
        "esa_income_tariff_income",
        "esa_income_assessable_capital",
        "legacy_prescribed_accommodation_capital_exception",
        lambda p: p.gov.dwp.ESA.income.capital,
    ),
    "jsa_income": (
        "jsa_income_tariff_income",
        "jsa_income_assessable_capital",
        "legacy_prescribed_accommodation_capital_exception",
        lambda p: p.gov.dwp.JSA.income.capital,
    ),
    "income_support": (
        "income_support_tariff_income",
        "income_support_assessable_capital",
        "legacy_prescribed_accommodation_capital_exception",
        lambda p: p.gov.dwp.income_support.means_test.capital,
    ),
    "housing_benefit": (
        "housing_benefit_tariff_income",
        "housing_benefit_assessable_capital",
        "housing_benefit_residential_capital_exception",
        lambda p: p.gov.dwp.housing_benefit.means_test.capital.working_age,
    ),
}
LEGACY = ("esa_income", "jsa_income", "income_support")

# The statutory figures, read from the regulations rather than the model.
ORDINARY_THRESHOLD = 6_000
PRESCRIBED_ACCOMMODATION_THRESHOLD = 10_000
STEP = 250
WEEKLY_AMOUNT = 1

# Capital in pence, so every value is a sum of money; biased towards the
# thresholds and the upper capital limit, where the branches meet.
BOUNDARIES = [0, 6_000, 6_250, 10_000, 10_250, 16_000]
PENCE = st.one_of(
    st.integers(0, 4_000_000),
    st.builds(
        lambda pounds, offset: max(0, pounds * 100 + offset),
        st.sampled_from(BOUNDARIES),
        st.integers(-300, 300),
    ),
)
YEARS = st.sampled_from([2015, 2020, 2024, 2025, 2026, 2029])


def statutory_tariff(capital, exception):
    """Annual tariff income the regulations give for one capital amount."""
    threshold = PRESCRIBED_ACCOMMODATION_THRESHOLD if exception else ORDINARY_THRESHOLD
    return WEEKS_IN_YEAR * WEEKLY_AMOUNT * ceil(max(0, capital - threshold) / STEP)


# One simulation serves every example: each example enters its capital
# amounts as inputs and recalculates tariff income, which reads only inputs.
SLOTS = 64


@pytest.fixture(scope="module")
def simulation(cloned_uk_tax_benefit_system):
    people = {f"person_{i}": {"age": {2025: 40}} for i in range(SLOTS)}
    benunits = {f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(SLOTS)}
    households = {f"household_{i}": {"members": [f"person_{i}"]} for i in range(SLOTS)}
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


def tariffs(simulation, capitals, exceptions, year):
    """Each programme's tariff income for one benefit unit per capital."""
    n = len(capitals)
    capital = np.zeros(SLOTS)
    capital[:n] = capitals
    exception = np.zeros(SLOTS, dtype=bool)
    exception[:n] = exceptions
    for _, capital_variable, exception_variable, _ in PROGRAMMES.values():
        simulation.set_input(capital_variable, year, capital)
        simulation.set_input(exception_variable, year, exception)
    # Working-age Housing Benefit rules, no Pension Credit passport.
    for variable in (
        "housing_benefit_pension_age_regulations_apply",
        "in_receipt_of_guarantee_credit",
        "in_receipt_of_savings_credit_only",
    ):
        simulation.set_input(variable, year, np.zeros(SLOTS, dtype=bool))
    result = {}
    for name, (variable, _, _, _) in PROGRAMMES.items():
        simulation.delete_arrays(variable)
        result[name] = simulation.calculate(variable, year)[:n]
    return result


def parameter_key(simulation, name, year):
    """The tariff figures a programme uses in a year."""
    parameters = simulation.tax_benefit_system.parameters(f"{year}-01-01")
    p = PROGRAMMES[name][3](parameters)
    return (
        p.tariff_income.threshold,
        p.residential_threshold,
        p.tariff_income.step,
        p.tariff_income.amount,
    )


def test_prescribed_accommodation_uses_higher_threshold(simulation):
    # £10,001 is £4,001 over £6,000 (17 steps) but £1 over £10,000 (1 step).
    result = tariffs(simulation, [10_001, 10_001], [False, True], 2025)
    for name in LEGACY:
        assert result[name].tolist() == [884, 52], name


@pytest.mark.parametrize(
    "path, start",
    [
        # IS Regs 1987 reg 53(1A), inserted by SI 1996/462 reg 12(1)(b).
        ("income_support/means_test/capital/residential_threshold.yaml", "1996-04-08"),
        # JSA Regs 1996 reg 116(1A), inserted by SI 1996/1516 reg 12(b).
        ("JSA/income/capital/residential_threshold.yaml", "1996-10-07"),
        # ESA Regs 2008 reg 118(2), in force with the regulations.
        ("ESA/income/capital/residential_threshold.yaml", "2008-10-27"),
    ],
)
def test_prescribed_accommodation_threshold_starts_with_the_regulation(path, start):
    data = yaml.safe_load((PARAMETERS / path).read_text())
    values = {str(date): entry["value"] for date, entry in data["values"].items()}
    assert values == {start: PRESCRIBED_ACCOMMODATION_THRESHOLD}


@PROPERTY_SETTINGS
@given(
    pence=st.lists(PENCE, min_size=1, max_size=8),
    increments=st.lists(st.integers(0, 1_500_000), min_size=8, max_size=8),
    year=YEARS,
)
def test_tariff_income_properties(simulation, pence, increments, year):
    lower = [p / 100 for p in pence]
    higher = [(p + d) / 100 for p, d in zip(pence, increments)]
    capitals = lower + lower + higher + higher
    exceptions = [False] * len(lower) + [True] * len(lower)
    exceptions = exceptions + exceptions
    result = tariffs(simulation, capitals, exceptions, year)
    n = len(lower)
    # The model stores capital as float32; the reference reads the same value.
    stored = np.asarray(capitals, dtype=np.float32).astype(float)
    expected = [statutory_tariff(c, e) for c, e in zip(stored, exceptions)]

    for name in PROGRAMMES:
        tariff = result[name]
        # 1. Reference: the regulation's formula.
        np.testing.assert_allclose(tariff, expected, atol=0.01, err_msg=name)
        ordinary_low, excepted_low = tariff[:n], tariff[n : 2 * n]
        ordinary_high, excepted_high = tariff[2 * n : 3 * n], tariff[3 * n :]
        # 2. Monotone: more capital never lowers tariff income.
        assert np.all(ordinary_high >= ordinary_low), name
        assert np.all(excepted_high >= excepted_low), name
        # 3. Bounded: the exception never raises tariff income.
        assert np.all(excepted_low <= ordinary_low), name
        assert np.all(excepted_high <= ordinary_high), name

    # 4. Differential: programmes with the same figures agree everywhere.
    groups = {}
    for name in PROGRAMMES:
        groups.setdefault(parameter_key(simulation, name, year), []).append(name)
    shared = [names for names in groups.values() if len(names) > 1]
    assert shared, f"no two programmes share tariff parameters in {year}"
    for names in shared:
        for name in names[1:]:
            np.testing.assert_array_equal(
                result[name], result[names[0]], err_msg=f"{name} vs {names[0]}"
            )

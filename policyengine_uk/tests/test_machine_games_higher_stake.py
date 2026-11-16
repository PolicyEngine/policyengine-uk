"""Machine Games Duty on higher-stake machines from 1 April 2027.

Budget 2026 (OOTLAR paragraph 1.50) moves machines with a maximum charge to
play above GBP 1 or a maximum prize above GBP 100 from the standard rate (20%)
to the higher rate (25%) from 1 April 2027. The household input
`machine_games_standard_rate_higher_stake_net_takings` is the part of
`machine_games_standard_rate_net_takings` from those machines.

Invariants, over generated households and model years 2024 to 2030:

1. Closed form: the duty equals the statutory duty without the change plus
   min(max(H, 0), max(S, 0)) * (25% - 20%) * f, where S is the standard-rate
   input, H the higher-stake input and f the share of the 6 April to 5 April
   model year on or after 1 April 2027 (0 to FY2025, 5/365 in FY2026, 1
   after). The reference uses Finance Act 2012 Schedule 24 paragraph 9's
   rates and its own date arithmetic, not `fiscal_year_segments`.
2. Zero takings in the class give the old duty, in every year.
3. Before FY2026 the split of the standard-rate base does not change the duty.
4. Monotonicity: moving takings into the class (raising H with S fixed) never
   lowers the duty, given a higher rate at least the standard rate, as in law.
5. Bounds: old duty <= duty <= old duty + max(S, 0) * 5% * f, and duty >= 0.
6. Counterfactual: switching the reclassification off gives the old duty.

Comparisons allow for the engine's float32 arithmetic (RTOL, ATOL).
"""

from datetime import date
from functools import cache

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.utils.excise import fiscal_year_segments

SWITCH = "gov.hmrc.gambling_duty.machine_games.higher_stake_machines_at_higher_rate"
# Finance Act 2012, Schedule 24, paragraph 9.
LOWER, STANDARD, HIGHER = 0.05, 0.20, 0.25
CHANGE = date(2027, 4, 1)  # OOTLAR paragraph 1.50.
INPUTS = (
    "machine_games_lower_rate_net_takings",
    "machine_games_standard_rate_net_takings",
    "machine_games_higher_rate_net_takings",
    "machine_games_standard_rate_higher_stake_net_takings",
)
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
CAPACITY = 24  # Households in each shared simulation.
# The engine computes in float32, about seven significant digits.
RTOL, ATOL = 2e-6, 1e-3
takings = st.integers(min_value=-20_000, max_value=5_000_000)
households = st.lists(
    st.tuples(takings, takings, takings, takings), min_size=1, max_size=8
)


def share_after_change(year):
    start, end = date(year, 4, 6), date(year + 1, 4, 6)
    return max((end - max(start, CHANGE)).days, 0) / (end - start).days


def slack(values):
    return RTOL * np.abs(values) + ATOL


def old_duty(lower, standard, higher):
    return max(lower, 0) * LOWER + max(standard, 0) * STANDARD + max(higher, 0) * HIGHER


def reference_duty(year, lower, standard, higher, higher_stake):
    moved = min(max(higher_stake, 0), max(standard, 0))
    return old_duty(lower, standard, higher) + moved * (
        HIGHER - STANDARD
    ) * share_after_change(year)


def simulation(changes=None, households=CAPACITY):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i in range(households):
        situation["people"][f"p{i}"] = {"age": {2026: 40}}
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {"members": [f"p{i}"]}
    return Simulation(
        situation=situation, scenario=Scenario(parameter_changes=changes or {})
    )


@cache
def shared_simulation(switched_off):
    """One simulation per scenario, reused across examples: building one
    takes seconds, while resetting its inputs takes milliseconds."""
    return simulation(
        {SWITCH: {"2013-02-01.2099-12-31": False}} if switched_off else {}
    )


@pytest.fixture(scope="module", autouse=True)
def release_shared_simulations():
    yield
    shared_simulation.cache_clear()


def duties(year, rows, switched_off=False, sim=None):
    """Machine Games Duty for each row of the four inputs."""
    sim = sim or shared_simulation(switched_off)
    size = sim.populations["household"].count
    assert len(rows) <= size
    padded = list(rows) + [(0, 0, 0, 0)] * (size - len(rows))
    for name, column in zip(INPUTS, zip(*padded)):
        sim.set_input(name, year, np.array(column, dtype=float))
    sim.delete_arrays("machine_games_duty")
    return np.asarray(sim.calculate("machine_games_duty", year))[: len(rows)]


def test_statutory_rates_hold_across_the_tested_years():
    """The references assume para 9's rates through the tested window."""
    rates = CountryTaxBenefitSystem().parameters.gov.hmrc.gambling_duty.machine_games
    for day in ["2024-04-06", "2027-04-01", "2031-04-05"]:
        assert rates.rates.lower(day) == LOWER
        assert rates.rates.standard(day) == STANDARD
        assert rates.rates.higher(day) == HIGHER


def test_switch_changes_on_the_statutory_date():
    switch = CountryTaxBenefitSystem().parameters.get_child(SWITCH)
    assert not switch("2027-03-31")
    assert switch("2027-04-01")


def test_share_after_change_matches_the_fiscal_calendar():
    assert share_after_change(2025) == 0
    assert share_after_change(2026) == pytest.approx(5 / 365)
    assert share_after_change(2027) == 1


@SETTINGS
@given(year=st.integers(min_value=2024, max_value=2030), rows=households)
def test_duty_matches_the_closed_form(year, rows):
    rows = rows + [(0, 0, 0, 0)]
    expected = [reference_duty(year, *row) for row in rows]
    assert duties(year, rows) == pytest.approx(expected, rel=RTOL, abs=ATOL)


@SETTINGS
@given(
    year=st.integers(min_value=2024, max_value=2030),
    rows=households,
    extra=st.lists(st.integers(min_value=0, max_value=5_000_000), max_size=8),
)
def test_moving_takings_into_the_class_never_lowers_duty(year, rows, extra):
    base = [(*row[:3], max(row[3], 0)) for row in rows]
    raised = [
        (*row[:3], row[3] + bump) for row, bump in zip(base, extra + [0] * len(base))
    ]
    zero = [(*row[:3], 0) for row in base]
    result = duties(year, zero + base + raised)
    n = len(base)
    old, low, high = result[:n], result[n : 2 * n], result[2 * n :]
    expected_old = [old_duty(*row[:3]) for row in base]
    assert old == pytest.approx(expected_old, rel=RTOL, abs=ATOL)
    assert np.all(low >= old - slack(old))
    assert np.all(high >= low - slack(low))
    ceiling = [
        old_duty(*row[:3])
        + max(row[1], 0) * (HIGHER - STANDARD) * share_after_change(year)
        for row in base
    ]
    assert np.all(high <= np.asarray(ceiling) + slack(high))
    assert np.all(result >= 0)
    if year <= 2025:
        assert high == pytest.approx(old, rel=RTOL, abs=ATOL)


@SETTINGS
@given(year=st.integers(min_value=2024, max_value=2030), rows=households)
def test_switching_the_change_off_gives_the_old_duty(year, rows):
    expected = [old_duty(*row[:3]) for row in rows]
    off = duties(year, rows, switched_off=True)
    assert off == pytest.approx(expected, rel=RTOL, abs=ATOL)


def test_annual_reform_applies_to_the_whole_fiscal_year():
    """A reform naming FY2026 covers all 365 days, not only 1 to 5 April."""
    row = (0, 36_500, 0, 36_500)
    annual = simulation({SWITCH: {"2026": True}}, households=1)
    assert duties(2026, [row])[0] == pytest.approx(7_325)
    assert duties(2026, [row], sim=annual)[0] == pytest.approx(9_125)


def test_dated_delay_splits_the_fiscal_year_by_day():
    """Delaying the change to 1 April 2028 leaves 5 of FY2027's 366 days."""
    row = (0, 36_600, 0, 36_600)
    delay = simulation({SWITCH: {"2027-04-01.2028-03-31": False}}, households=1)
    # 36,600 * 20% + 36,600 * 5% * 5 / 366.
    assert duties(2027, [row], sim=delay)[0] == pytest.approx(7_345)


def test_segments_split_at_dates_from_every_mapped_leaf():
    rates = ParameterNode(
        "rates", data={"rate": {"values": {"2020-01-01": 1, "2026-10-01": 2}}}
    )
    switch = ParameterNode(
        "switch", data={"on": {"values": {"2020-01-01": False, "2027-04-01": True}}}
    )
    segments = list(
        fiscal_year_segments({**rates.children, "on": switch.children["on"]}, 2026)
    )
    assert [(p.rate, p.on) for p, share in segments] == [
        (1, False),
        (2, False),
        (2, True),
    ]
    assert [share for p, share in segments] == pytest.approx(
        [178 / 365, 182 / 365, 5 / 365]
    )


def test_mapped_segments_reject_nodes():
    rates = ParameterNode("rates", data={"rate": {"values": {"2020-01-01": 1}}})
    with pytest.raises(TypeError):
        list(fiscal_year_segments({"rates": rates}, 2026))

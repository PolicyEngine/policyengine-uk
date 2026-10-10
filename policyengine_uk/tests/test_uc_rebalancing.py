import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Simulation

YEARS = range(2025, 2030)


def _uc_claimant(age_2025: int) -> dict:
    return {
        "people": {
            "person": {
                "age": {year: age_2025 + year - 2025 for year in YEARS},
                "employment_income": {year: 0 for year in YEARS},
                "uc_limited_capability_for_WRA": {year: True for year in YEARS},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


class _FixedRng:
    def __init__(self, values):
        self.values = np.array(values, dtype=float)

    def random(self, size):
        assert size == len(self.values)
        return self.values


def _force_uc_seed(monkeypatch, values):
    monkeypatch.setattr(
        uc_reform.np.random, "default_rng", lambda seed: _FixedRng(values)
    )


# UC Regs 2013 reg. 36 table, monthly: 2025-26 as up-rated in April 2025, and
# 2026-27 as SI 2026/113 reg. 3(3) substitutes it
# (https://www.legislation.gov.uk/uksi/2026/113/made).
STANDARD_ALLOWANCE_2025 = {
    "SINGLE_YOUNG": 316.98,
    "SINGLE_OLD": 400.14,
    "COUPLE_YOUNG": 497.55,
    "COUPLE_OLD": 628.10,
}
STANDARD_ALLOWANCE_2026 = {
    "SINGLE_YOUNG": 338.58,
    "SINGLE_OLD": 424.90,
    "COUPLE_YOUNG": 528.34,
    "COUPLE_OLD": 666.97,
}
LCWRA_2025 = 423.27
PROTECTED_LCWRA_2026 = 429.80
# Relevant CPI percentage for 2026-27: CPI rose 3.8% in the year to September
# 2025, the rate the 2026-27 up-rating applied.
CPI_FACTOR_2026 = 1.038


def _standard_allowances(sim: Simulation, year: int) -> dict:
    amounts = sim.tax_benefit_system.parameters(
        str(year)
    ).gov.dwp.universal_credit.standard_allowance.amount
    return {
        claimant_type: float(amounts[claimant_type])
        for claimant_type in uc_reform.STANDARD_ALLOWANCE_TYPES
    }


def _cpi_factor(sim: Simulation, year: int) -> float:
    parameters = sim.tax_benefit_system.parameters
    return float(parameters(str(year)).gov.benefit_uprating_cpi) / float(
        parameters(str(year - 1)).gov.benefit_uprating_cpi
    )


@pytest.mark.parametrize("age_2025", [20, 30])
def test_pre_2026_claimants_get_the_legislated_2026_27_amount(monkeypatch, age_2025):
    # SI 2026/113 reg. 3(3)(b) sets one amount, £429.80, for every pre-2026
    # claimant, whatever their age.
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(situation=_uc_claimant(age_2025))

    assert sim.calculate("uc_LCWRA_element", 2026)[0] == pytest.approx(
        PROTECTED_LCWRA_2026 * 12
    )


@pytest.mark.parametrize("age_2025", [20, 30])
def test_projected_years_take_the_section_4_floor(monkeypatch, age_2025):
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(situation=_uc_claimant(age_2025))

    previous = sim.calculate("uc_LCWRA_element", 2026)[0] / 12
    for year in range(2027, 2030):
        amount = sim.calculate("uc_LCWRA_element", year)[0] / 12
        factor = max(_cpi_factor(sim, year), 1.0)
        before = _standard_allowances(sim, year - 1)
        now = _standard_allowances(sim, year)
        shortfalls = [
            (previous + before[t]) * factor - (amount + now[t])
            for t in uc_reform.STANDARD_ALLOWANCE_TYPES
        ]
        # Simulation outputs are float32, so compare to a tenth of a penny.
        # s. 4(2): every pairing keeps up with CPI, and the amount never falls.
        assert max(shortfalls) <= 1e-3
        assert amount >= previous - 1e-3
        # The lowest such amount: it stayed put, or some pairing binds.
        assert amount == pytest.approx(previous, abs=1e-3) or max(
            shortfalls
        ) == pytest.approx(0, abs=1e-3)
        previous = amount


def test_section_4_floor_reproduces_the_legislated_2026_27_amount():
    # Differential against the published figure: the s. 4 floor from the
    # 2025-26 amounts at the 3.8% relevant CPI percentage is SI 2026/113's
    # £429.80.
    floor = uc_reform.protected_lcwra_floor(
        LCWRA_2025, STANDARD_ALLOWANCE_2025, STANDARD_ALLOWANCE_2026, CPI_FACTOR_2026
    )
    assert round(floor, 2) == PROTECTED_LCWRA_2026


money = st.floats(min_value=0, max_value=5_000, allow_nan=False)
allowances = st.fixed_dictionaries(
    {claimant_type: money for claimant_type in uc_reform.STANDARD_ALLOWANCE_TYPES}
)
factors = st.floats(min_value=0.8, max_value=1.3, allow_nan=False)


@settings(max_examples=300, deadline=None)
@given(previous=money, before=allowances, now=allowances, factor=factors)
def test_section_4_floor_properties(previous, before, now, factor):
    floor = uc_reform.protected_lcwra_floor(previous, before, now, factor)
    growth = max(factor, 1.0)
    shortfalls = [
        (previous + before[t]) * growth - (floor + now[t])
        for t in uc_reform.STANDARD_ALLOWANCE_TYPES
    ]
    tolerance = 1e-9 * max(1.0, previous + max(before.values()))
    assert max(shortfalls) <= tolerance
    assert floor >= previous
    assert floor == pytest.approx(previous) or max(shortfalls) == pytest.approx(
        0, abs=tolerance
    )


@settings(max_examples=200, deadline=None)
@given(previous=money, before=allowances, now=allowances, factor=st.floats(0.5, 1.0))
def test_section_4_floor_treats_a_cpi_fall_as_zero(previous, before, now, factor):
    assert uc_reform.protected_lcwra_floor(
        previous, before, now, factor
    ) == uc_reform.protected_lcwra_floor(previous, before, now, 1.0)


@settings(max_examples=200, deadline=None)
@given(
    previous=money,
    extra=st.floats(0, 1_000),
    before=allowances,
    now=allowances,
    factor=factors,
)
def test_section_4_floor_rises_with_the_previous_amount(
    previous, extra, before, now, factor
):
    assert uc_reform.protected_lcwra_floor(
        previous + extra, before, now, factor
    ) >= uc_reform.protected_lcwra_floor(previous, before, now, factor)


def test_new_claimants_use_fixed_health_element(monkeypatch):
    _force_uc_seed(monkeypatch, [0.0])
    sim = Simulation(situation=_uc_claimant(30))

    for year in range(2026, 2030):
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        expected_health = float(
            sim.tax_benefit_system.parameters(
                str(year)
            ).gov.dwp.universal_credit.rebalancing.new_claimant_health_element
        )

        assert health_element == pytest.approx(expected_health)


def test_standard_allowance_reforms_still_change_standard_allowance(monkeypatch):
    _force_uc_seed(monkeypatch, [0.99])
    baseline = Simulation(situation=_uc_claimant(30))
    reformed = Simulation(
        situation=_uc_claimant(30),
        reform={
            "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": {
                "2025-01-01.2100-12-31": 800
            }
        },
    )

    baseline_standard_allowance = baseline.calculate("uc_standard_allowance", 2026)[0]
    reformed_standard_allowance = reformed.calculate("uc_standard_allowance", 2026)[0]

    assert reformed_standard_allowance / baseline_standard_allowance > 1.5

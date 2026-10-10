import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Scenario, Simulation

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
    # s. 4(4)(a): the CPI 12-month rate in the September before the tax year.
    inputs = sim.tax_benefit_system.parameters.gov.economic_assumptions.statutory_uprating_inputs
    return 1 + float(inputs.cpi_september(f"{year - 1}-09-01"))


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
        assert amount == pytest.approx(previous, rel=0, abs=1e-3) or max(
            shortfalls
        ) == pytest.approx(0, rel=0, abs=1e-3)
        previous = amount


def test_section_4_floor_reproduces_the_legislated_2026_27_amount():
    # Differential against the published figure: the s. 4 floor from the
    # 2025-26 amounts at the 3.8% relevant CPI percentage is SI 2026/113's
    # £429.80.
    floor = uc_reform.protected_lcwra_floor(
        LCWRA_2025, STANDARD_ALLOWANCE_2025, STANDARD_ALLOWANCE_2026, CPI_FACTOR_2026
    )
    assert round(floor, 2) == PROTECTED_LCWRA_2026


CPI_SEPTEMBER = "gov.economic_assumptions.statutory_uprating_inputs.cpi_september"
PROTECTED = "gov.dwp.universal_credit.rebalancing.protected_health_element"


def _protected_monthly(sim: Simulation, year: int) -> float:
    return sim.calculate("uc_LCWRA_element", year)[0] / 12


def test_projection_uses_the_september_cpi_rate(monkeypatch):
    # s. 4(4)(a): September 2026 CPI sets the 2027-28 floor. A 9% September
    # 2026 rate, far above any standard allowance growth, must lift the
    # protected amount by exactly the floor.
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(
        situation=_uc_claimant(30),
        # The rebalancing modifier runs when the simulation is built, so the
        # change must apply before then.
        scenario=Scenario(
            parameter_changes={CPI_SEPTEMBER: {"2026-09-01": 0.09}},
            applied_before_data_load=True,
        ),
    )
    expected = uc_reform.protected_lcwra_floor(
        PROTECTED_LCWRA_2026,
        _standard_allowances(sim, 2026),
        _standard_allowances(sim, 2027),
        1.09,
    )
    assert expected > PROTECTED_LCWRA_2026 * 1.05
    assert _protected_monthly(sim, 2027) == pytest.approx(expected, rel=0, abs=1e-3)


def test_a_one_year_override_is_projected_from(monkeypatch):
    # A reform that sets 2027-28 only: 2028-29 is not legislated and takes the
    # floor from the reformed £500, not the carried £429.80.
    _force_uc_seed(monkeypatch, [0.99])
    sim = Simulation(
        situation=_uc_claimant(30),
        scenario=Scenario(
            parameter_changes={PROTECTED: {"2027": 500}},
            applied_before_data_load=True,
        ),
    )
    assert _protected_monthly(sim, 2027) == pytest.approx(500, rel=0, abs=1e-3)
    expected = uc_reform.protected_lcwra_floor(
        500,
        _standard_allowances(sim, 2027),
        _standard_allowances(sim, 2028),
        _cpi_factor(sim, 2028),
    )
    assert _protected_monthly(sim, 2028) == pytest.approx(expected, rel=0, abs=1e-3)
    assert _protected_monthly(sim, 2028) >= 500 - 1e-3


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
    assert floor == pytest.approx(previous, rel=0, abs=tolerance) or max(
        shortfalls
    ) == pytest.approx(0, rel=0, abs=tolerance)


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


def _new_claimant_rate(sim: Simulation, year: int) -> float:
    return float(
        sim.tax_benefit_system.parameters(
            str(year)
        ).gov.dwp.universal_credit.rebalancing.new_claimant_health_element
    )


def test_new_claimants_use_fixed_health_element():
    situation = _uc_claimant(30)
    situation["benunits"]["benunit"]["uc_receives_new_claimant_health_element"] = {
        year: True for year in YEARS
    }
    sim = Simulation(situation=situation)

    for year in range(2026, 2030):
        health_element = sim.calculate("uc_LCWRA_element", year)[0] / 12
        assert health_element == pytest.approx(_new_claimant_rate(sim, year))


def _many_uc_claimants(count: int) -> dict:
    people = {
        f"person_{i}": {
            "age": {year: 30 for year in YEARS},
            "employment_income": {year: 0 for year in YEARS},
            "uc_limited_capability_for_WRA": {year: True for year in YEARS},
        }
        for i in range(count)
    }
    return {
        "people": people,
        "benunits": {
            f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(count)
        },
        "households": {
            f"household_{i}": {"members": [f"person_{i}"]} for i in range(count)
        },
    }


def test_household_award_does_not_depend_on_its_position():
    # Before the fix, a seeded draw over the benefit units in the simulation
    # gave about 11% of these identical households the new-claimant rate in
    # 2026, depending only on their position.
    sim = Simulation(situation=_many_uc_claimants(40))
    alone = Simulation(situation=_uc_claimant(30))

    for year in range(2026, 2030):
        health_elements = sim.calculate("uc_LCWRA_element", year)
        assert np.all(health_elements == health_elements[0])
        assert health_elements[0] == pytest.approx(
            alone.calculate("uc_LCWRA_element", year)[0]
        )
        assert health_elements[0] / 12 > _new_claimant_rate(sim, year)


def _dataset(new_claimant_status=None):
    from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
    import pandas as pd

    benunit = {"benunit_id": [1, 2]}
    if new_claimant_status is not None:
        benunit["uc_receives_new_claimant_health_element"] = new_claimant_status
    single_year = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [30, 30],
                "uc_limited_capability_for_WRA": [True, True],
            }
        ),
        benunit=pd.DataFrame(benunit),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "household_weight": [1.0, 1.0],
                "region": ["NORTH_EAST", "NORTH_EAST"],
            }
        ),
        fiscal_year=2026,
    )
    return UKMultiYearDataset(datasets=[single_year])


def test_data_without_a_status_keeps_the_seeded_draw(monkeypatch):
    _force_uc_seed(monkeypatch, [0.0, 0.99])
    sim = Simulation(dataset=_dataset())

    health_elements = np.asarray(sim.calculate("uc_LCWRA_element", 2026)) / 12
    assert health_elements[0] == pytest.approx(_new_claimant_rate(sim, 2026))
    assert health_elements[1] == pytest.approx(429.80)
    assert list(sim.calculate("uc_receives_new_claimant_health_element", 2026)) == [
        True,
        False,
    ]


def test_data_that_supplies_the_status_overrides_the_draw(monkeypatch):
    _force_uc_seed(monkeypatch, [0.0, 0.99])
    sim = Simulation(dataset=_dataset(new_claimant_status=[False, True]))

    health_elements = np.asarray(sim.calculate("uc_LCWRA_element", 2026)) / 12
    assert health_elements[0] == pytest.approx(429.80)
    assert health_elements[1] == pytest.approx(_new_claimant_rate(sim, 2026))


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

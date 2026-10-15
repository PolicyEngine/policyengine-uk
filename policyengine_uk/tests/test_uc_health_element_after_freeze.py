"""Universal Credit LCWRA element from 2030-31 (issue #2282).

Universal Credit Act 2025 s. 2 relabels the reg. 36 rows for good: the
new-claimant amount and the protected amount (pre-2026, severe conditions
criteria and terminally ill claimants) both continue. s. 3 disapplies the
SSAA 1992 s. 150 up-rating only in the tax years ending 5 April 2026 to
5 April 2029, and s. 4's floor for the protected amount covers only 2026-27 to
2029-30. So from 2030-31 both amounts are uprated again under s. 150.

The rebalancing scenario used to set the element only to 2029-30; from
2030-31 every claimant fell to the new-claimant amount, a protected claimant
from £457.15 to £235.86 a month.

Invariants:

1. No drop: from 2026-27 to the end of the data's projection, neither a
   protected nor a new claimant's element falls from one year to the next,
   for any CPI path; with non-negative CPI their Universal Credit does not
   fall either (the standard allowance follows CPI down when it falls).
2. From 2030-31 the protected amount is the year before's times the growth
   of the element's uprating index, the index the new-claimant amount
   follows.
3. Reforms take effect: a 2030-31 change to either amount moves that
   claimant's element and Universal Credit by the same amount. The
   scenario projects a protected amount from the changed one; a one-year
   change to the new-claimant amount, an uprated parameter, gives way to
   prior law's path the next year (``policyengine_uk.utils.dated_reforms``).
   The new-claimant share is a parameter the draw reads in every year it
   sets.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Scenario, Simulation

YEARS = range(uc_reform.FIRST_REBALANCING_YEAR, uc_reform.LAST_SET_YEAR + 1)
FIRST_UPRATED_YEAR = uc_reform.SECTION_4_LAST_YEAR + 1
REBALANCING = "gov.dwp.universal_credit.rebalancing"
PROTECTED = f"{REBALANCING}.protected_health_element"
NEW_CLAIMANT = f"{REBALANCING}.new_claimant_health_element"
SHARE = f"{REBALANCING}.new_claimant_share"
OBR_CPI = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"


def at(year: int) -> str:
    return f"{year}-04-30"


def claimant(new_claimant: bool) -> dict:
    """A single claimant aged 30 with LCWRA and no income, stating whether
    they are a new claimant."""
    return {
        "people": {
            "person": {
                "age": {year: 30 for year in YEARS},
                "employment_income": {year: 0 for year in YEARS},
                "uc_limited_capability_for_WRA": {year: True for year in YEARS},
            }
        },
        "benunits": {
            "benunit": {
                "members": ["person"],
                "uc_receives_new_claimant_health_element": {
                    year: new_claimant for year in YEARS
                },
            }
        },
        "households": {"household": {"members": ["person"]}},
    }


def monthly(sim: Simulation, variable: str, year: int) -> float:
    return float(sim.calculate(variable, year)[0]) / 12


def index_growth(sim: Simulation, year: int) -> float:
    index = sim.tax_benefit_system.parameters.gov.dwp.universal_credit.elements.disabled.uprating
    return index(at(year)) / index(at(year - 1))


def assert_never_falls(
    sim: Simulation, variables=("uc_LCWRA_element", "universal_credit")
) -> None:
    """Invariant 1."""
    for variable in variables:
        path = [monthly(sim, variable, year) for year in YEARS]
        for year, previous, current in zip(YEARS[1:], path, path[1:]):
            assert current >= previous - 1e-6, (variable, year, path)


@pytest.mark.parametrize("new_claimant", [False, True])
def test_no_drop_from_2029_30_to_2030_31(new_claimant):
    sim = Simulation(situation=claimant(new_claimant))
    assert_never_falls(sim)
    assert monthly(sim, "uc_LCWRA_element", FIRST_UPRATED_YEAR) > monthly(
        sim, "uc_LCWRA_element", FIRST_UPRATED_YEAR - 1
    )


def test_protected_amount_is_uprated_by_the_element_index_from_2030_31():
    """Invariant 2."""
    sim = Simulation(situation=claimant(False))
    assert monthly(sim, "uc_LCWRA_element", 2026) == pytest.approx(429.80, rel=1e-6)
    for year in range(FIRST_UPRATED_YEAR, YEARS[-1] + 1):
        assert monthly(sim, "uc_LCWRA_element", year) == pytest.approx(
            monthly(sim, "uc_LCWRA_element", year - 1) * index_growth(sim, year),
            rel=1e-6,
        )


def test_new_claimant_amount_follows_the_same_index():
    sim = Simulation(situation=claimant(True))
    for year in range(FIRST_UPRATED_YEAR - 3, FIRST_UPRATED_YEAR):
        assert monthly(sim, "uc_LCWRA_element", year) == pytest.approx(217.26, rel=1e-6)
    for year in range(FIRST_UPRATED_YEAR, YEARS[-1] + 1):
        assert monthly(sim, "uc_LCWRA_element", year) == pytest.approx(
            monthly(sim, "uc_LCWRA_element", year - 1) * index_growth(sim, year),
            rel=1e-6,
        )


@pytest.mark.parametrize(
    "new_claimant, parameter, amount",
    [(False, PROTECTED, 500.0), (True, NEW_CLAIMANT, 300.0)],
)
def test_a_2030_31_reform_moves_universal_credit(new_claimant, parameter, amount):
    """Invariant 3: the change reaches the element and Universal Credit, and
    the next year projects from it."""
    baseline = Simulation(situation=claimant(new_claimant))
    reformed = Simulation(
        situation=claimant(new_claimant),
        scenario=Scenario(parameter_changes={parameter: {"2030": amount}}),
    )
    year = FIRST_UPRATED_YEAR
    assert monthly(reformed, "uc_LCWRA_element", year) == pytest.approx(
        amount, rel=1e-6
    )
    change = amount - monthly(baseline, "uc_LCWRA_element", year)
    assert monthly(reformed, "universal_credit", year) - monthly(
        baseline, "universal_credit", year
    ) == pytest.approx(change, rel=1e-5)
    next_year = monthly(reformed, "uc_LCWRA_element", year + 1)
    if parameter == PROTECTED:
        # The scenario projects the protected amount from the changed one.
        assert next_year == pytest.approx(
            amount * index_growth(reformed, year + 1), rel=1e-6
        )
    else:
        # A one-year change to an uprated parameter gives way to prior law.
        assert next_year == pytest.approx(
            monthly(baseline, "uc_LCWRA_element", year + 1), rel=1e-6
        )
    # Earlier years are unchanged.
    assert monthly(reformed, "uc_LCWRA_element", year - 1) == pytest.approx(
        monthly(baseline, "uc_LCWRA_element", year - 1), rel=1e-6
    )


CPI_SETTINGS = settings(
    max_examples=3,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def cpi_path_simulation(new_claimant: bool, growth) -> Simulation:
    """A claimant under an OBR CPI path for 2024 to 2032 (the benefit index
    lags it a year; September CPI drives the s. 4 floor)."""
    changes = {
        OBR_CPI: {f"year:{year}": rate for year, rate in zip(range(2024, 2033), growth)}
    }
    return Simulation(
        situation=claimant(new_claimant),
        scenario=Scenario(parameter_changes=changes, applied_before_data_load=True),
    )


@CPI_SETTINGS
@given(st.lists(st.floats(-0.05, 0.15, allow_nan=False), min_size=9, max_size=9))
def test_the_protected_amount_never_falls_for_any_cpi_path(growth):
    """Invariant 1 for the element: the s. 4 floor never falls, and the
    uprating index never falls."""
    assert_never_falls(cpi_path_simulation(False, growth), ("uc_LCWRA_element",))


@CPI_SETTINGS
@given(st.lists(st.floats(0, 0.15, allow_nan=False), min_size=9, max_size=9))
def test_no_claimant_loses_from_one_year_to_the_next_with_non_negative_cpi(growth):
    """Invariant 1 for the element and Universal Credit."""
    for new_claimant in (False, True):
        assert_never_falls(cpi_path_simulation(new_claimant, growth))


class _FixedDraw:
    def __init__(self, values):
        self.values = np.array(values, dtype=float)

    def random(self, size):
        assert size == len(self.values)
        return self.values


def _two_lcwra_claimants():
    from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
    import pandas as pd

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
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
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


def test_the_draw_reads_the_new_claimant_share_in_every_year_it_sets(monkeypatch):
    """Invariant 3: data without a status takes the seeded draw against
    ``rebalancing.new_claimant_share``, from 2026-27 to the end of the
    projection; the share holds at its 2029-30 value after."""
    monkeypatch.setattr(
        uc_reform.np.random, "default_rng", lambda seed: _FixedDraw([0.2, 0.99])
    )
    baseline = Simulation(dataset=_two_lcwra_claimants())
    status = {
        year: list(baseline.calculate("uc_receives_new_claimant_health_element", year))
        for year in YEARS
    }
    # 0.2 is below the 22% share from 2029-30, above the earlier shares.
    for year in YEARS:
        assert status[year] == [year >= 2029, False], year
    reformed = Simulation(
        dataset=_two_lcwra_claimants(),
        scenario=Scenario(parameter_changes={SHARE: {"2031": 0.1}}),
    )
    assert list(
        reformed.calculate("uc_receives_new_claimant_health_element", 2031)
    ) == [False, False]
    assert list(
        reformed.calculate("uc_receives_new_claimant_health_element", 2032)
    ) == [True, False]

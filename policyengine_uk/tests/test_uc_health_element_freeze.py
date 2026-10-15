"""Universal Credit LCWRA element freeze, Universal Credit Act 2025 s. 3
(issue #2280).

s. 3(1) disapplies the annual up-rating in Social Security Administration Act
1992 s. 150(1) and (2) for the LCWRA element in the tax years ending 5 April
2026 to 5 April 2029. An up-rating order takes effect from the tax year after
the one in which it is made (s. 150(10)), so the rates for 2026-27 to 2029-30
stay at the £217.26 a month that s. 2 sets for 2026-27. From 2030-31 the
element is uprated again from that amount.

Invariants:

1. Freeze: in each tax year in which ``rebalancing.health_element_freeze``
   and ``rebalancing.active`` are true (2026-27 to 2029-30 in law), the
   amount equals the previous year's, for any CPI path, unless an amount is
   stated for that year (as s. 2 states £217.26 for 2026-27).
2. Uprating otherwise: in any other year the amount is the previous year's
   times the growth in the benefit uprating index, floored at no change
   (s. 150(2) provides only for increases). So it never falls, and with
   non-negative CPI it grows exactly with the benefit index.
3. Differential: on the full parameter pipeline, the amount equals an
   independent recursion over the processed benefit index, read at the
   30 April sampling date, including a benefit index value dated after
   30 April.
4. Reforms take effect: a change to the amount is held or uprated from the
   changed value; switching the freeze or the rebalancing reforms off
   restores CPI uprating; a different CPI forecast leaves the frozen years
   alone and moves the later ones.
5. One path: ``rebalancing.new_claimant_health_element``, the copy of the
   amount the rebalancing scenario pays new claimants for 2026-27 to
   2029-30, equals the element amount in every year from 2026-27, under any
   freeze schedule or CPI path. So a lifted freeze reaches a simulated new
   claimant.
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.universal_credit.rebalancing.create_health_element_uprating import (
    add_uc_health_element_uprating,
)
from policyengine_uk.system import system

AMOUNT = "gov.dwp.universal_credit.elements.disabled.amount"
FREEZE = "gov.dwp.universal_credit.rebalancing.health_element_freeze"
ACTIVE = "gov.dwp.universal_credit.rebalancing.active"
NEW_CLAIMANT_AMOUNT = "gov.dwp.universal_credit.rebalancing.new_claimant_health_element"
OBR_CPI = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
# Universal Credit Act 2025 s. 2: the 2026-27 amount, a month.
ACT_AMOUNT = 217.26
FROZEN_YEARS = range(2026, 2030)
FIRST_UPRATED_YEAR = 2030
HORIZON = 2040


def at(year: int) -> str:
    """Fiscal-year conversion reads each tax year at 30 April."""
    return f"{year}-04-30"


def amount_path(parameters, years) -> dict:
    node = parameters.get_child(AMOUNT)
    return {year: node(at(year)) for year in years}


def benefit_index(parameters, year: int) -> float:
    return parameters.gov.benefit_uprating_cpi(at(year))


def assert_one_path(parameters, years) -> None:
    """Invariant 5: the scenario's new-claimant amount equals the element
    amount."""
    new_claimant = parameters.get_child(NEW_CLAIMANT_AMOUNT)
    for year, amount in amount_path(parameters, years).items():
        assert new_claimant(at(year)) == pytest.approx(amount, rel=1e-12)


# A single claimant aged 30 with LCWRA in 2030-31.
SITUATION = {
    "people": {
        "person": {
            "age": {2030: 30},
            "uc_limited_capability_for_WRA": {2030: True},
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def scenario_parameters(parameter_changes: dict):
    simulation = Simulation(
        situation=SITUATION,
        scenario=Scenario(
            parameter_changes=parameter_changes, applied_before_data_load=True
        ),
    )
    return simulation.tax_benefit_system.parameters


# Examples on the full pipeline.


@pytest.mark.parametrize("year", FROZEN_YEARS)
def test_frozen_at_the_act_amount_in_2026_27_to_2029_30(year):
    assert system.parameters.get_child(AMOUNT)(at(year)) == pytest.approx(
        ACT_AMOUNT, abs=1e-9
    )


def test_2030_31_is_uprated_by_one_year_of_the_benefit_index():
    """The first uprating after the freeze starts from £217.26 and adds one
    year's growth, not the frozen years' growth as well."""
    parameters = system.parameters
    growth = benefit_index(parameters, 2030) / benefit_index(parameters, 2029)
    assert parameters.get_child(AMOUNT)(at(2030)) == pytest.approx(
        ACT_AMOUNT * growth, rel=1e-12
    )
    # Main had £217.26 uprated by 2026-27 to 2030-31 CPI.
    four_years = benefit_index(parameters, 2030) / benefit_index(parameters, 2026)
    assert parameters.get_child(AMOUNT)(at(2030)) < ACT_AMOUNT * four_years


def statutory_path(parameters, last_year: int) -> dict:
    """Invariant 3's independent recursion: £217.26 for 2026-27, then each
    year the previous year's amount, held in the frozen years and otherwise
    raised by the processed benefit index's growth, never down."""
    expected = {2026: ACT_AMOUNT}
    for year in range(2027, last_year + 1):
        growth = benefit_index(parameters, year) / benefit_index(parameters, year - 1)
        frozen = year in FROZEN_YEARS
        expected[year] = expected[year - 1] * (1 if frozen else max(1.0, growth))
    return expected


def test_differential_against_the_processed_benefit_index():
    """Invariant 3: an independent recursion over the benefit index as the
    full pipeline uprated it, for the baseline and the unconverted copy."""
    parameters = system.parameters
    expected = statutory_path(parameters, HORIZON)
    actual = amount_path(parameters, range(2026, HORIZON + 1))
    assert actual == pytest.approx(expected, rel=1e-12)
    # parameters.baseline is not fiscal-year converted and keys uprated values
    # to 1 January, so it reads each tax year's amount from 1 January.
    baseline = parameters.baseline.get_child(AMOUNT)
    for year in range(2027, HORIZON + 1):
        assert baseline(f"{year}-01-01") == pytest.approx(expected[year], rel=1e-12)


def test_a_benefit_index_change_after_30_april_reaches_the_next_tax_year():
    """Review round 2: a one-year change to the benefit index from 1 June
    2038 ends on 1 June 2039, when the stated value comes back. That first
    shows in the 30 April 2040 sample, a year after the last uprating entry,
    and the element must follow it there."""
    parameters = scenario_parameters(
        {"gov.benefit_uprating_cpi": {"year:2038-06-01": 57.24}}
    )
    assert benefit_index(parameters, 2039) == pytest.approx(57.24)
    assert benefit_index(parameters, 2040) > benefit_index(parameters, 2039)
    expected = statutory_path(parameters, HORIZON)
    actual = amount_path(parameters, range(2026, HORIZON + 1))
    assert actual == pytest.approx(expected, rel=1e-12)
    assert actual[2040] > actual[2039]
    assert_one_path(parameters, range(2026, HORIZON + 1))


# The same claimant, stated to be a new claimant (#2250).
NEW_CLAIMANT_SITUATION = {
    **SITUATION,
    "benunits": {
        "benunit": {
            "members": ["person"],
            "uc_receives_new_claimant_health_element": {2030: True},
        }
    },
}


def test_household_element_after_the_freeze():
    """In 2030-31 a new claimant with LCWRA gets twelve times the uprated
    monthly amount: the rebalancing scenario pays the new-claimant amount,
    which follows the same index (#2282)."""
    simulation = Simulation(situation=NEW_CLAIMANT_SITUATION)
    monthly = system.parameters.get_child(AMOUNT)(at(2030))
    # The formula returns float32.
    assert float(simulation.calculate("uc_LCWRA_element", 2030)[0]) == pytest.approx(
        12 * monthly, rel=1e-6
    )


def test_the_scenario_pays_new_claimants_the_element_amount():
    """Invariant 5 on the baseline."""
    assert_one_path(system.parameters, range(2026, HORIZON + 1))


# Reforms on the full pipeline (invariant 4).


@pytest.mark.parametrize("parameter", [FREEZE, ACTIVE])
def test_switching_the_freeze_off_restores_cpi_uprating(parameter):
    parameters = scenario_parameters({parameter: False})
    path = amount_path(parameters, range(2026, 2032))
    assert path[2026] == pytest.approx(ACT_AMOUNT)
    for year in range(2027, 2032):
        growth = benefit_index(parameters, year) / benefit_index(parameters, 2026)
        assert path[year] == pytest.approx(ACT_AMOUNT * growth, rel=1e-12)
    assert_one_path(parameters, range(2026, 2032))


def test_unfreezing_one_year_uprates_that_year_and_holds_the_rest():
    parameters = scenario_parameters({FREEZE: {"2028": False}})
    path = amount_path(parameters, range(2026, 2031))
    growth = benefit_index(parameters, 2028) / benefit_index(parameters, 2027)
    assert path[2027] == pytest.approx(ACT_AMOUNT)
    assert path[2028] == pytest.approx(ACT_AMOUNT * growth, rel=1e-12)
    assert path[2029] == pytest.approx(path[2028], rel=1e-12)
    assert_one_path(parameters, range(2026, 2031))


class _NewClaimantDraw:
    """Stands in for the scenario's random draw: every benefit unit draws 0,
    below each year's new-claimant share."""

    def random(self, size):
        return uc_reform.np.zeros(size)


def new_claimant_situation(years) -> dict:
    """A single claimant aged 30 with LCWRA who is a new claimant."""
    benunit = {"members": ["person"]}
    # Where the claim status is an input, state it; the draw then has no say.
    if "uc_receives_new_claimant_health_element" in system.variables:
        benunit["uc_receives_new_claimant_health_element"] = {
            year: True for year in years
        }
    return {
        "people": {
            "person": {
                "age": {year: 30 for year in years},
                "employment_income": {year: 0 for year in years},
                "uc_limited_capability_for_WRA": {year: True for year in years},
            }
        },
        "benunits": {"benunit": benunit},
        "households": {"household": {"members": ["person"]}},
    }


def test_lifting_the_freeze_reaches_a_simulated_new_claimant(monkeypatch):
    """Invariant 5 in a simulation: for 2026-27 to 2029-30 the rebalancing
    scenario sets the element, and a new claimant's follows the freeze."""
    monkeypatch.setattr(
        uc_reform.np.random, "default_rng", lambda seed: _NewClaimantDraw()
    )
    years = range(2026, 2030)
    frozen = Simulation(situation=new_claimant_situation(years))
    for year in years:
        assert frozen.calculate("uc_LCWRA_element", year)[0] == pytest.approx(
            12 * ACT_AMOUNT, rel=1e-6
        )
    lift = {FREEZE: {"2028": False, "2029": False}}
    # Every route that writes the change onto the statutory timeline reaches
    # the award: a scenario applied before or after the data load, and a
    # reform dict keyed by year.
    routes = {
        "scenario before data load": dict(
            scenario=Scenario(parameter_changes=lift, applied_before_data_load=True)
        ),
        "scenario after data load": dict(scenario=Scenario(parameter_changes=lift)),
        "reform dict": dict(reform=lift),
    }
    for route, kwargs in routes.items():
        lifted = Simulation(situation=new_claimant_situation(years), **kwargs)
        parameters = lifted.tax_benefit_system.parameters
        assert float(lifted.calculate("uc_LCWRA_element", 2027)[0]) == pytest.approx(
            12 * ACT_AMOUNT, rel=1e-6
        ), route
        for year in (2028, 2029):
            growth = benefit_index(parameters, year) / benefit_index(parameters, 2027)
            assert growth > 1, route
            assert float(
                lifted.calculate("uc_LCWRA_element", year)[0]
            ) == pytest.approx(12 * ACT_AMOUNT * growth, rel=1e-6), route


def test_a_changed_amount_is_held_through_the_freeze():
    """A one-year change applies to its tax year; the stated amount resumes
    after it and is held, then uprated."""
    parameters = scenario_parameters({AMOUNT: {"2027": 250}})
    path = amount_path(parameters, range(2026, 2031))
    assert path[2026] == pytest.approx(ACT_AMOUNT)
    assert path[2027] == pytest.approx(250)
    assert path[2028] == pytest.approx(ACT_AMOUNT)
    assert path[2029] == pytest.approx(ACT_AMOUNT)
    growth = benefit_index(parameters, 2030) / benefit_index(parameters, 2029)
    assert path[2030] == pytest.approx(ACT_AMOUNT * growth, rel=1e-12)


def test_a_reform_dict_changes_the_year_it_names():
    """The scenario pays a new claimant ``new_claimant_health_element`` in the
    years it sets, so a reform dict on that amount reaches the award."""
    simulation = Simulation(
        situation=NEW_CLAIMANT_SITUATION, reform={NEW_CLAIMANT_AMOUNT: {"2030": 300}}
    )
    assert float(simulation.calculate("uc_LCWRA_element", 2030)[0]) == pytest.approx(
        3_600, rel=1e-6
    )


CPI_GROWTH = st.floats(min_value=-0.05, max_value=0.15, allow_nan=False)


@settings(
    max_examples=4,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(st.lists(CPI_GROWTH, min_size=8, max_size=8))
def test_any_cpi_forecast_leaves_the_frozen_years_alone(growth):
    """Invariants 1 and 2 on the full pipeline, for an OBR CPI path for
    2025 to 2032 (the benefit index lags it a year)."""
    parameters = scenario_parameters(
        {
            OBR_CPI: {
                f"year:{year}": rate for year, rate in zip(range(2025, 2033), growth)
            }
        }
    )
    path = amount_path(parameters, range(2026, 2034))
    assert [path[year] for year in FROZEN_YEARS] == pytest.approx([ACT_AMOUNT] * 4)
    for year in range(FIRST_UPRATED_YEAR, 2034):
        ratio = benefit_index(parameters, year) / benefit_index(parameters, year - 1)
        assert path[year] == pytest.approx(path[year - 1] * max(1.0, ratio), rel=1e-12)
        assert path[year] >= path[year - 1]
    assert_one_path(parameters, range(2026, 2034))


# Properties on a small parameter tree run through the same builder and core
# uprating, which makes many examples cheap.

INDEX_FIRST_YEAR = 2010
INDEX_LAST_YEAR = 2041
YEARS = range(2025, INDEX_LAST_YEAR + 1)


def uprated_tree(
    cpi_growth,
    freeze_values=None,
    active_values=None,
    amount_values=None,
    benefit_values=None,
):
    """A tree with the parameters the builder reads, after the builder and
    core uprating have run. ``cpi_growth`` gives the lagged CPI index's
    growth into each year from 2011; ``benefit_values`` adds stated values
    of the benefit index at any dates."""
    lagged_cpi = {f"{INDEX_FIRST_YEAR}-01-01": 1.0}
    level = 1.0
    for year, rate in zip(range(INDEX_FIRST_YEAR + 1, INDEX_LAST_YEAR + 1), cpi_growth):
        level *= 1 + rate
        lagged_cpi[f"{year}-01-01"] = level
    data = {
        "gov": {
            "benefit_uprating_cpi": {
                "values": {
                    "2005-01-01": 100,
                    "2010-01-01": 114.48,
                    **(benefit_values or {}),
                },
                "metadata": {
                    "uprating": "gov.economic_assumptions.indices.obr.lagged_cpi"
                },
            },
            "economic_assumptions": {
                "indices": {"obr": {"lagged_cpi": {"values": lagged_cpi}}}
            },
            "dwp": {
                "universal_credit": {
                    "rebalancing": {
                        "active": {"values": active_values or {"2025-01-01": True}},
                        "health_element_freeze": {
                            "values": freeze_values
                            or {
                                "2015-01-01": False,
                                "2026-04-06": True,
                                "2030-04-06": False,
                            }
                        },
                        "new_claimant_health_element": {
                            "values": {"2026-01-01": ACT_AMOUNT},
                            "metadata": {
                                "uprating": "gov.economic_assumptions.indices.uc_health_element"
                            },
                        },
                    },
                    "elements": {
                        "disabled": {
                            "amount": {
                                "values": amount_values
                                or {"2025-04-01": 423.27, "2026-04-01": ACT_AMOUNT},
                                "metadata": {
                                    "uprating": "gov.economic_assumptions.indices.uc_health_element"
                                },
                            }
                        }
                    },
                }
            },
        }
    }
    root = ParameterNode("", data=data)
    add_uc_health_element_uprating(root)
    uprate_parameters(root)
    return root


def tree_rule_holds(root, frozen, start_year, start_amount, last_year=None):
    """Each year after ``start_year`` is the previous year's amount, held when
    frozen and otherwise uprated by the benefit index, never down."""
    amount = root.get_child(AMOUNT)
    assert amount(at(start_year)) == pytest.approx(start_amount, rel=1e-12)
    for year in range(start_year + 1, (last_year or INDEX_LAST_YEAR) + 1):
        previous = amount(at(year - 1))
        ratio = benefit_index(root, year) / benefit_index(root, year - 1)
        expected = previous if frozen(year) else previous * max(1.0, ratio)
        assert amount(at(year)) == pytest.approx(expected, rel=1e-12)
        assert amount(at(year)) >= previous * (1 - 1e-12)


TREE_SETTINGS = settings(max_examples=200, deadline=None, derandomize=True)
GROWTH_PATHS = st.lists(
    CPI_GROWTH,
    min_size=INDEX_LAST_YEAR - INDEX_FIRST_YEAR,
    max_size=INDEX_LAST_YEAR - INDEX_FIRST_YEAR,
)


@TREE_SETTINGS
@given(GROWTH_PATHS)
def test_frozen_years_hold_for_any_cpi_path(growth):
    """Invariant 1 with the statutory schedule, including falling prices."""
    root = uprated_tree(growth)
    amount = root.get_child(AMOUNT)
    for year in FROZEN_YEARS:
        assert amount(at(year)) == pytest.approx(ACT_AMOUNT, abs=1e-9)
    tree_rule_holds(root, lambda year: year in FROZEN_YEARS, 2026, ACT_AMOUNT)
    assert_one_path(root, range(2026, INDEX_LAST_YEAR + 1))


@TREE_SETTINGS
@given(st.lists(st.floats(0, 0.15), min_size=31, max_size=31))
def test_after_the_freeze_the_amount_grows_with_non_negative_cpi(growth):
    """Invariant 2: with non-negative CPI, every year from 2030-31 grows by
    exactly the benefit index's growth from the frozen amount."""
    root = uprated_tree(growth)
    amount = root.get_child(AMOUNT)
    for year in range(FIRST_UPRATED_YEAR, INDEX_LAST_YEAR + 1):
        ratio = benefit_index(root, year) / benefit_index(root, 2029)
        assert amount(at(year)) == pytest.approx(ACT_AMOUNT * ratio, rel=1e-12)
        assert amount(at(year)) >= amount(at(year - 1))


@TREE_SETTINGS
@given(
    GROWTH_PATHS,
    st.sets(st.integers(2026, INDEX_LAST_YEAR)),
    st.sets(st.integers(2026, INDEX_LAST_YEAR)),
)
def test_any_freeze_schedule_holds_exactly_its_years(growth, frozen, inactive):
    """Invariants 1 and 2 for any schedule of frozen and inactive years: a
    year is held only when it is frozen and the reforms are active."""
    freeze_values = {"2015-01-01": False}
    active_values = {"2015-01-01": True}
    for year in YEARS:
        freeze_values[f"{year}-04-06"] = year in frozen
        active_values[f"{year}-04-06"] = year not in inactive
    root = uprated_tree(growth, freeze_values, active_values)
    tree_rule_holds(
        root,
        lambda year: year in frozen and year not in inactive,
        2026,
        ACT_AMOUNT,
    )
    assert_one_path(root, range(2026, INDEX_LAST_YEAR + 1))


@TREE_SETTINGS
@given(
    GROWTH_PATHS,
    st.integers(2026, 2035),
    st.floats(0, 1_000, allow_nan=False),
)
def test_a_reformed_amount_is_held_or_uprated_from_its_value(growth, year, value):
    """Invariant 4: an amount stated from any year is used in that year and
    projected from with the same rule."""
    amount_values = {
        "2025-04-01": 423.27,
        "2026-04-01": ACT_AMOUNT,
        f"{year}-04-06": value,
    }
    root = uprated_tree(growth, amount_values=amount_values)
    tree_rule_holds(root, lambda y: y in FROZEN_YEARS, year, value)
    # Core uprating projects only from a parameter's latest stated value, so a
    # value stated from a later year leaves the earlier years at the last
    # stated amount (£217.26) rather than uprating them. This is core's rule
    # for every uprated parameter, not the statutory path for 2030-31 on.
    for earlier in range(2026, year):
        assert root.get_child(AMOUNT)(at(earlier)) == pytest.approx(ACT_AMOUNT)


BENEFIT_INDEX_ENTRIES = st.dictionaries(
    st.builds(
        lambda year, month, day: f"{year}-{month:02d}-{day:02d}",
        st.integers(2026, INDEX_LAST_YEAR + 1),
        st.integers(1, 12),
        st.integers(1, 28),
    ),
    st.floats(50, 300, allow_nan=False),
    max_size=3,
)


@TREE_SETTINGS
@given(GROWTH_PATHS, BENEFIT_INDEX_ENTRIES)
def test_any_dated_benefit_index_values_are_followed(growth, benefit_values):
    """Invariants 1 to 3 when the benefit index has stated values on any
    date, including after 30 April and after the last uprating entry: the
    amount follows the processed index, read at 30 April, to the first tax
    year that sees the last value."""
    root = uprated_tree(growth, benefit_values=benefit_values)
    tree_rule_holds(
        root,
        lambda year: year in FROZEN_YEARS,
        2026,
        ACT_AMOUNT,
        last_year=INDEX_LAST_YEAR + 3,
    )
    assert_one_path(root, range(2026, INDEX_LAST_YEAR + 4))

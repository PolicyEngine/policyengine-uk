"""Pension-age forecasts follow main's reformed guarantee and maximum.

Invariants, for the Savings Credit threshold and protected pension-age Housing
Benefit allowance forecast indices:

1. Guarantee reforms move forecast thresholds and protected allowances along
   the guarantee's uprated path. The live phase-in rate determines the
   threshold; zero preserves the previous threshold, as on main.
2. No reform to a base-year allowance or threshold stops the parameter tree
   being built; only an enacted allowance below its guarantee raises.
3. A reformed allowance below its guarantee is projected whole by the
   guarantee's earnings path, continuously with an allowance equal to it.
4. Each allowance has its own index: a reform to one leaves the others.
5. A reform to the maximum Savings Credit, from the base year or a later
   year, reaches the projected threshold and higher allowances through every
   reform route: each forecast year's threshold is the guarantee less the
   reformed maximum / phase-in, and each allowance the guarantee plus it.
   A threshold or allowance whose own base is reformed keeps projecting its
   own reformed gap.
"""

from math import isfinite

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import instant
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation, system
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.housing_benefit.allowances.create_pension_age_allowances import (
    ALLOWANCE_GUARANTEES,
    protected_allowance_index_values,
)
from policyengine_uk.tax_benefit_system import (
    CountryTaxBenefitSystem,
    process_parameter_tree,
)


GUARANTEE = "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee"
HB_ALLOWANCES = "gov.dwp.housing_benefit.allowances"
SAVINGS_CREDIT = "gov.dwp.pension_credit.savings_credit"
YEARS = range(2026, 2041)
PROJECTION_PATHS = (
    *(f"{HB_ALLOWANCES}.{name}.aged" for name in ("single", "lone_parent", "couple")),
    *(
        f"{HB_ALLOWANCES}.protected_pension_age_uprating.{name}"
        for name in ALLOWANCE_GUARANTEES
    ),
    *(
        f"{SAVINGS_CREDIT}.{name}.{relationship}"
        for name in ("threshold", "threshold_uprating")
        for relationship in ("SINGLE", "COUPLE")
    ),
)


def _situation(couple, years):
    names = ["claimant", "partner"] if couple else ["claimant"]
    return {
        "people": {
            name: {
                "age": {year: 70 for year in years},
                "state_pension": {year: 0 for year in years},
                "is_claimant_or_partner": {year: True for year in years},
            }
            for name in names
        },
        "benunits": {
            "benunit": {
                "members": names,
                "claims_all_entitled_benefits": {year: True for year in years},
                "would_claim_pc": {year: True for year in years},
                "would_claim_uc": {year: False for year in years},
            }
        },
        "households": {
            "household": {
                "members": names,
                "country": {year: "ENGLAND" for year in years},
                "local_authority": {year: "MAIDSTONE" for year in years},
                "savings": {year: 0 for year in years},
            }
        },
    }


def _simulation(couple, changes, years, route="reform"):
    options = (
        {"reform": changes}
        if route == "reform"
        else {
            "scenario": Scenario(
                parameter_changes=changes,
                applied_before_data_load=True,
            )
        }
    )
    return Simulation(situation=_situation(couple, years), **options)


def _modifier_simulation(couple, changes, start="2026-04-01", stop=None, dated_changes=None):
    """Reload YAML, apply open or bounded updates, then reprocess it."""

    def modify(simulation):
        tax_benefit_system = simulation.tax_benefit_system
        tax_benefit_system.reset_parameters()
        for path, value in changes.items():
            tax_benefit_system.parameters.get_child(path).update(
                start=instant(start), stop=instant(stop) if stop else None, value=value
            )
        tax_benefit_system.process_parameters()

    return Simulation(
        situation=_situation(couple, range(2026, 2031)),
        scenario=Scenario(simulation_modifier=modify, applied_before_data_load=True),
        reform=dated_changes,
    )


@pytest.mark.parametrize(
    "path,value",
    [
        (f"{GUARANTEE}.SINGLE", 250),
        (f"{SAVINGS_CREDIT}.threshold.SINGLE", 200),
        (f"{HB_ALLOWANCES}.single.aged", 260),
    ],
)
@pytest.mark.parametrize(
    "start,stop",
    [
        ("2026-04-01", "2100-12-31"),
        ("2027-04-01", "2100-12-31"),
        ("2027-04-01", None),
    ],
)
def test_reprocessing_modifier_keeps_the_yaml_base_and_its_explicit_update(
    path, value, start, stop
):
    parameters = _modifier_simulation(
        False, {path: value}, start, stop
    ).tax_benefit_system.parameters
    assert parameters.get_child(path)(f"{start[:4]}-04-30") == value
    for index in (
        f"{SAVINGS_CREDIT}.threshold_uprating.SINGLE",
        f"{HB_ALLOWANCES}.protected_pension_age_uprating.single",
    ):
        assert parameters.get_child(index)("2026-04-30") == 1
        assert parameters.get_child(index)("2028-04-30") > 0


@pytest.mark.parametrize(
    "path,value",
    [(f"{GUARANTEE}.SINGLE", 250), (f"{SAVINGS_CREDIT}.threshold.SINGLE", 200), (f"{HB_ALLOWANCES}.single.aged", 260)],
)
def test_reprocessing_modifier_composes_with_dated_projection_reforms(path, value):
    parameters = _modifier_simulation(
        False, {path: value}, "2027-04-01", "2100-12-31",
        dated_changes={f"{HB_ALLOWANCES}.lone_parent.aged": {"2028": 280}},
    ).tax_benefit_system.parameters
    assert parameters.get_child(path)("2027-04-30") == value
    assert parameters.gov.dwp.housing_benefit.allowances.lone_parent.aged("2028-04-30") == 280


def _assert_projections_follow_main(simulation):
    """Main's forecast algebra, preserving independently rounded enacted rates."""
    parameters = simulation.tax_benefit_system.parameters
    pc = parameters.gov.dwp.pension_credit
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for path in PROJECTION_PATHS:
        assert parameters.get_child(path)("2026-04-30") == system.parameters.get_child(
            path
        )("2026-04-30")
    for year in range(2027, 2041):
        at = f"{year}-04-30"
        for relationship, kinds in {
            "SINGLE": ("single", "lone_parent"),
            "COUPLE": ("couple",),
        }.items():
            guarantee = getattr(pc.guarantee_credit.minimum_guarantee, relationship)(at)
            maximum = getattr(pc.savings_credit.maximum, relationship)(at)
            threshold = getattr(pc.savings_credit.threshold, relationship)
            phase_in = pc.savings_credit.rate.phase_in(at)
            expected_threshold = (
                max(0, guarantee - maximum / phase_in)
                if phase_in > 0
                else threshold(f"{year - 1}-04-30")
            )
            assert threshold(at) == pytest.approx(expected_threshold), (
                relationship,
                year,
            )
            base_threshold = threshold("2026-04-30")
            assert getattr(pc.savings_credit.threshold_uprating, relationship)(
                at
            ) == pytest.approx(expected_threshold / base_threshold)
            for kind in kinds:
                allowance = getattr(allowances, kind).aged
                expected = guarantee + maximum
                assert allowance(at) == pytest.approx(expected), (kind, year)
                assert allowance(at) >= guarantee - abs(guarantee) * 1e-12
                assert getattr(allowances.protected_pension_age_uprating, kind)(
                    at
                ) == pytest.approx(expected / allowance("2026-04-30"))
        for path in PROJECTION_PATHS:
            if "_uprating." in path:
                assert parameters.get_child(path)(at) > 0, (path, year)


@pytest.mark.parametrize("route", ["reform", "scenario"])
@pytest.mark.parametrize("couple,expected", [(False, 15_600), (True, 23_868)])
def test_2026_guarantee_reform_pays_the_reformed_credit_and_moves_forecasts(
    couple, expected, route
):
    changes = {
        f"{GUARANTEE}.SINGLE": 300,
        f"{GUARANTEE}.COUPLE": 459,
    }
    simulation = _simulation(couple, changes, [2026], route)

    assert simulation.calculate("pension_credit", 2026)[0] == pytest.approx(expected)
    _assert_projections_follow_main(simulation)


@pytest.mark.parametrize("route", ["reform", "scenario"])
@pytest.mark.parametrize("couple,expected", [(False, 15_600), (True, 23_868)])
def test_simultaneous_calendar_guarantee_reforms_follow_main(couple, expected, route):
    """Rebuilding prior law for either dated change must tolerate the other."""
    changes = {
        f"{GUARANTEE}.SINGLE": {"year:2026-01-01:1": 300},
        f"{GUARANTEE}.COUPLE": {"year:2026-01-01:1": 459},
    }
    simulation = _simulation(couple, changes, [2026], route)

    assert simulation.calculate("pension_credit", 2026)[0] == pytest.approx(expected)
    _assert_projections_follow_main(simulation)


@pytest.mark.parametrize("route", ["reform", "scenario"])
@pytest.mark.parametrize("calendar_year", [False, True])
@pytest.mark.parametrize("couple", [False, True])
def test_joint_guarantee_and_hb_cuts_use_consistent_reformed_components(
    couple, calendar_year, route
):
    guarantees = {"SINGLE": 200, "COUPLE": 300}
    allowances = {"single": 220, "lone_parent": 220, "couple": 330}
    values = {
        **{f"{GUARANTEE}.{name}": value for name, value in guarantees.items()},
        **{f"{HB_ALLOWANCES}.{name}.aged": value for name, value in allowances.items()},
    }
    changes = {
        path: {"year:2026-01-01:1": value} if calendar_year else value
        for path, value in values.items()
    }
    simulation = _simulation(couple, changes, [2026], route)
    parameters = simulation.tax_benefit_system.parameters
    expected_credit = guarantees["COUPLE" if couple else "SINGLE"] * 52

    assert simulation.calculate("pension_credit", 2026)[0] == pytest.approx(
        expected_credit
    )
    for name, amount in allowances.items():
        allowance = parameters.get_child(f"{HB_ALLOWANCES}.{name}.aged")
        assert allowance("2026-04-30") == pytest.approx(amount)

    for name, relationship in ALLOWANCE_GUARANTEES.items():
        path = f"{HB_ALLOWANCES}.protected_pension_age_uprating.{name}"
        index = parameters.get_child(path)
        assumptions = parameters.gov.economic_assumptions
        earnings = assumptions.indices.earnings_uprating
        earnings_growth = earnings("2027-04-30") / earnings("2026-04-30")
        cpi_growth = (
            assumptions.indices.september_cpi_uprating("2027-04-30")
            / assumptions.indices.september_cpi_uprating("2026-04-30")
            - 1
        )
        guarantee = guarantees[relationship]
        base = allowances[name]
        expected = (
            guarantee * earnings_growth + (base - guarantee) * (1 + cpi_growth)
        ) / base
        assert index("2027-04-30") == pytest.approx(expected)


@pytest.mark.parametrize("calendar_year", [False, True])
def test_joint_guarantee_and_savings_threshold_cuts_use_reformed_components(
    calendar_year,
):
    guarantees = {"SINGLE": 200, "COUPLE": 300}
    thresholds = {"SINGLE": 180, "COUPLE": 280}
    values = {
        **{f"{GUARANTEE}.{name}": value for name, value in guarantees.items()},
        **{
            f"{SAVINGS_CREDIT}.threshold.{name}": value
            for name, value in thresholds.items()
        },
    }
    changes = {
        path: {"year:2026-01-01:1": value} if calendar_year else value
        for path, value in values.items()
    }
    simulation = _simulation(False, changes, [2026])
    parameters = simulation.tax_benefit_system.parameters
    for relationship, base_threshold in thresholds.items():
        threshold = parameters.get_child(f"{SAVINGS_CREDIT}.threshold.{relationship}")
        assert threshold("2026-04-30") == pytest.approx(base_threshold)
        path = f"{SAVINGS_CREDIT}.threshold_uprating.{relationship}"
        index = parameters.get_child(path)
        assumptions = parameters.gov.economic_assumptions
        earnings = assumptions.indices.earnings_uprating
        earnings_growth = earnings("2027-04-30") / earnings("2026-04-30")
        cpi_growth = (
            assumptions.indices.september_cpi_uprating("2027-04-30")
            / assumptions.indices.september_cpi_uprating("2026-04-30")
            - 1
        )
        # These reformed gaps imply exact £12 maxima at the 60% phase-in rate.
        expected_threshold = guarantees[relationship] * earnings_growth - 20 * (
            1 + cpi_growth
        )
        assert index("2027-04-30") == pytest.approx(expected_threshold / base_threshold)


@settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    year=st.integers(2026, 2040),
    weekly_guarantee=st.floats(min_value=0, allow_nan=False, allow_infinity=False),
    couple=st.booleans(),
    route=st.sampled_from(["reform", "scenario"]),
    calendar_year=st.booleans(),
)
@example(
    year=2026, weekly_guarantee=0, couple=False, route="reform", calendar_year=False
)
@example(
    year=2026,
    weekly_guarantee=100_000_000,
    couple=True,
    route="scenario",
    calendar_year=True,
)
@example(
    year=2040, weekly_guarantee=0, couple=True, route="scenario", calendar_year=False
)
@example(
    year=2040, weekly_guarantee=1e300, couple=False, route="reform", calendar_year=True
)
def test_nonnegative_guarantee_reforms_never_break_pension_age_projections(
    year, weekly_guarantee, couple, route, calendar_year
):
    # Generate across the finite non-negative domain. Reading the weekly
    # rate avoids overflowing the model's float32 annual-award variables.
    relationship = "COUPLE" if couple else "SINGLE"
    path = f"{GUARANTEE}.{relationship}"
    period = f"year:{year}-01-01:1" if calendar_year else str(year)
    simulation = _simulation(
        couple,
        {path: {period: weekly_guarantee}},
        [year],
        route,
    )

    guarantee = simulation.tax_benefit_system.parameters.get_child(path)
    assert guarantee(f"{year}-04-30") == weekly_guarantee
    parameters = simulation.tax_benefit_system.parameters
    # Keep the full finite input domain for buildability. At its upper end,
    # earnings uprating can overflow amounts on main too; exact algebra is
    # covered separately by the bounded differential property.
    for path in PROJECTION_PATHS:
        parameter = parameters.get_child(path)
        for forecast_year in YEARS:
            value = parameter(f"{forecast_year}-04-30")
            assert value >= 0, (path, forecast_year)
            if "_uprating." in path:
                assert isfinite(value) and value > 0, (path, forecast_year)
    for name, relationship in ALLOWANCE_GUARANTEES.items():
        allowance = parameters.get_child(f"{HB_ALLOWANCES}.{name}.aged")
        guarantee = parameters.get_child(f"{GUARANTEE}.{relationship}")
        for forecast_year in range(2027, 2041):
            at = f"{forecast_year}-04-30"
            if isfinite(guarantee(at)):
                assert allowance(at) >= guarantee(at) - abs(guarantee(at)) * 1e-12


@pytest.mark.parametrize("couple", [False, True])
def test_earnings_path_guarantee_reform_moves_dependent_forecasts(couple):
    """Match uk-triple-lock's annual overrides from the 2026-27 guarantee."""
    changes = {}
    for relationship in ("SINGLE", "COUPLE"):
        base = float(
            system.parameters.get_child(f"{GUARANTEE}.{relationship}")("2026-04-30")
        )
        changes[f"{GUARANTEE}.{relationship}"] = {
            str(year): base * 1.05 ** (year - 2026) for year in range(2027, 2041)
        }
    simulation = _simulation(couple, changes, YEARS)
    relationship = "COUPLE" if couple else "SINGLE"
    path = f"{GUARANTEE}.{relationship}"
    parameter = simulation.tax_benefit_system.parameters.get_child(path)

    for year in range(2027, 2041):
        expected = changes[path][str(year)]
        assert parameter(f"{year}-04-30") == pytest.approx(expected)
        assert simulation.calculate("pension_credit", year)[0] == pytest.approx(
            expected * 52, rel=1e-6
        )
    _assert_projections_follow_main(simulation)


@pytest.mark.parametrize("relationship", ["SINGLE", "COUPLE"])
def test_invalid_enacted_protected_allowance_still_raises(relationship):
    parameters = system.parameters
    guarantee = float(parameters.get_child(f"{GUARANTEE}.{relationship}")("2026-04-01"))
    assumptions = parameters.gov.economic_assumptions

    with pytest.raises(ValueError, match="cannot be lower than"):
        protected_allowance_index_values(
            guarantee - 0.01,
            guarantee,
            assumptions.indices.earnings_uprating,
            assumptions.statutory_uprating_inputs.cpi_september,
            2026,
            base_year=2026,
        )


@pytest.mark.parametrize("allowance_name,amount", [("single", 200), ("couple", 300)])
def test_invalid_statutory_allowance_still_raises_during_projection(
    allowance_name, amount
):
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.reset_parameters()
    parameters = tax_benefit_system.parameters
    parameters.get_child(f"{HB_ALLOWANCES}.{allowance_name}.aged").update(
        start=instant("2026-04-01"), stop=None, value=amount
    )

    with pytest.raises(ValueError, match="cannot be lower than"):
        process_parameter_tree(parameters, annualise=False)


def _index_growth(parameters, name, year=2027):
    index = parameters.get_child(
        f"{HB_ALLOWANCES}.protected_pension_age_uprating.{name}"
    )
    return index(f"{year}-04-30") / index(f"{year - 1}-04-30")


def _earnings_growth(parameters, year=2027):
    earnings = parameters.gov.economic_assumptions.indices.earnings_uprating
    return earnings(f"{year}-04-30") / earnings(f"{year - 1}-04-30")


@pytest.mark.parametrize(
    "relationship,allowance_name", [("SINGLE", "single"), ("COUPLE", "couple")]
)
def test_completed_joint_reform_below_the_guarantee_projects_with_the_guarantee(
    relationship, allowance_name
):
    """An allowance cut below a cut guarantee no longer stops the build: with
    no retained Savings Credit, it follows the guarantee's earnings path."""
    changes = {
        f"{GUARANTEE}.{relationship}": 230,
        f"{HB_ALLOWANCES}.{allowance_name}.aged": 220,
    }
    simulation = _modifier_simulation(relationship == "COUPLE", changes)
    parameters = simulation.tax_benefit_system.parameters

    allowance = parameters.get_child(f"{HB_ALLOWANCES}.{allowance_name}.aged")
    assert allowance("2026-04-30") == pytest.approx(220)
    assert _index_growth(parameters, allowance_name) == pytest.approx(
        _earnings_growth(parameters)
    )
    earnings = parameters.gov.economic_assumptions.indices.earnings_uprating
    for year in range(2027, 2031):
        at = f"{year}-04-30"
        assert allowance(at) == pytest.approx(
            220 * earnings(at) / earnings("2026-04-30")
        )


@pytest.mark.parametrize("offset", [-100, -0.01, 0, 0.01])
def test_allowance_reform_at_the_guarantee_boundary_is_continuous(offset):
    """Below, at and just above the enacted £238 guarantee, a 2026 cut to the
    single allowance projects within a millionth of the guarantee's earnings
    growth, exactly so at or below it, and leaves the other indices. Just
    above, the penny of retained Savings Credit grows by CPI, so the growth
    lies between the two."""
    guarantee = float(system.parameters.get_child(f"{GUARANTEE}.SINGLE")("2026-04-30"))
    changes = {f"{HB_ALLOWANCES}.single.aged": guarantee + offset}
    parameters = _modifier_simulation(False, changes).tax_benefit_system.parameters

    growth = _index_growth(parameters, "single")
    earnings_growth = _earnings_growth(parameters)
    if offset <= 0:
        assert growth == pytest.approx(earnings_growth, rel=1e-12)
    else:
        assert growth == pytest.approx(earnings_growth, rel=1e-6)
        cpi = parameters.gov.economic_assumptions.statutory_uprating_inputs
        cpi_growth = 1 + max(float(cpi.cpi_september("2026-09-01")), 0)
        assert min(earnings_growth, cpi_growth) <= growth
        assert growth <= max(earnings_growth, cpi_growth)
    for name in ("lone_parent", "couple"):
        assert _index_growth(parameters, name) == pytest.approx(
            _index_growth(system.parameters, name)
        )
    earnings = parameters.gov.economic_assumptions.indices.earnings_uprating
    prices = parameters.gov.economic_assumptions.indices.september_cpi_uprating
    for year in range(2027, 2031):
        at = f"{year}-04-30"
        expected = (
            min(guarantee, guarantee + offset) * earnings(at) / earnings("2026-04-30")
        )
        expected += max(0, offset) * prices(at) / prices("2026-04-30")
        assert parameters.gov.dwp.housing_benefit.allowances.single.aged(
            at
        ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "path",
    [
        f"{HB_ALLOWANCES}.single.aged",
        f"{HB_ALLOWANCES}.couple.aged",
        f"{SAVINGS_CREDIT}.threshold.SINGLE",
        f"{SAVINGS_CREDIT}.threshold.COUPLE",
    ],
)
def test_zero_base_reform_builds_and_keeps_the_zero(path):
    """Zeroing a base-year allowance or threshold used to raise or divide by
    zero while the tree was built; the zero now holds."""
    simulation = _simulation(False, {path: {"year:2026-01-01:1": 0}}, [2026])
    parameter = simulation.tax_benefit_system.parameters.get_child(path)
    assert parameter("2026-04-30") == 0


@pytest.mark.parametrize("route", ["reform", "scenario"])
def test_zero_phase_in_reform_keeps_the_previous_threshold_and_pays_no_credit(route):
    """Follow main: a zero phase-in rate leaves no residual threshold to solve."""
    situation = _situation(False, [2027])
    # Savings Credit needs State Pension age before 6 April 2016. About £231 a
    # week is above the projected threshold and below the guarantee.
    situation["people"]["claimant"]["age"] = {2027: 85}
    situation["people"]["claimant"]["state_pension"] = {2027: 12_000}
    baseline = Simulation(situation=situation)
    changes = {f"{SAVINGS_CREDIT}.rate.phase_in": 0}
    options = (
        {"reform": changes}
        if route == "reform"
        else {
            "scenario": Scenario(
                parameter_changes=changes, applied_before_data_load=True
            )
        }
    )
    simulation = Simulation(situation=situation, **options)

    assert baseline.calculate("savings_credit", 2027)[0] > 0
    assert simulation.calculate("savings_credit", 2027)[0] == 0
    _assert_projections_follow_main(simulation)


MAXIMUM = f"{SAVINGS_CREDIT}.maximum"
FAR = "2100-12-31"
FORECAST_YEARS = range(2027, 2041)
MAXIMUM_ROUTES = ["reform", "scenario", "structural", "modifier"]
RELATIONSHIP_ALLOWANCES = {"SINGLE": ("single", "lone_parent"), "COUPLE": ("couple",)}


@pytest.mark.parametrize("route", MAXIMUM_ROUTES)
def test_guarantee_increase_reaches_forecasts_through_every_route(route):
    changes = {f"{GUARANTEE}.SINGLE": {"2026-04-01.2100-12-31": 300}}
    if route == "modifier":
        simulation = _modifier_simulation(
            False, {f"{GUARANTEE}.SINGLE": 300}, stop="2100-12-31"
        )
    elif route == "structural":
        simulation = Simulation(
            situation=_situation(False, [2028]),
            reform=Reform.from_dict(changes, country_id="uk"),
        )
    else:
        simulation = _simulation(False, changes, [2028], route)
    _assert_projections_follow_main(simulation)


def test_zero_phase_in_modifier_preserves_a_reformed_own_threshold():
    parameters = _modifier_simulation(
        False,
        {
            f"{SAVINGS_CREDIT}.threshold.SINGLE": 180,
            f"{SAVINGS_CREDIT}.rate.phase_in": 0,
        },
    ).tax_benefit_system.parameters
    for year in range(2026, 2031):
        assert (
            parameters.gov.dwp.pension_credit.savings_credit.threshold.SINGLE(
                f"{year}-04-30"
            )
            == 180
        )


@pytest.mark.parametrize(
    "weekly_guarantee,expected_threshold,expected_allowance,expected_step",
    [(None, 221.585186, 272.195717, 1.01), (300, 268.368418, 318.978949, 1.38)],
)
def test_guarantee_credit_boundary_matches_main(
    weekly_guarantee, expected_threshold, expected_allowance, expected_step
):
    """Frozen origin/main (6030cbc0b) cliff-probe values, including current law."""
    year = 2028
    situation = {
        "people": {"claimant": {"age": {year: 85}}},
        "benunits": {"benunit": {"members": ["claimant"]}},
        "households": {
            "household": {
                "members": ["claimant"],
                "country": {year: "ENGLAND"},
                "local_authority": {year: "MAIDSTONE"},
                "tenure_type": {year: "RENT_FROM_COUNCIL"},
                "rent": {year: 10_000},
                "council_tax": {year: 2_000},
                "savings": {year: 0},
            }
        },
        "axes": [
            [
                {
                    "name": "private_pension_income",
                    "min": 8_000,
                    "max": 22_000,
                    "count": 2801,
                    "period": year,
                }
            ]
        ],
    }
    changes = {f"{GUARANTEE}.SINGLE": {"2026-01-01.2100-12-31": weekly_guarantee}}
    simulation = Simulation(
        situation=situation, reform=changes if weekly_guarantee is not None else None
    )
    parameters = simulation.tax_benefit_system.parameters
    assert parameters.gov.dwp.pension_credit.savings_credit.threshold.SINGLE(
        "2028-04-30"
    ) == pytest.approx(expected_threshold, rel=0, abs=5e-7)
    assert parameters.gov.dwp.housing_benefit.allowances.single.aged(
        "2028-04-30"
    ) == pytest.approx(expected_allowance, rel=0, abs=5e-7)
    guarantee_credit = simulation.calculate("guarantee_credit", year)
    last = int(np.flatnonzero(guarantee_credit > 0)[-1])
    net = simulation.calculate("household_net_income", year) + simulation.calculate(
        "tv_licence", year
    )
    assert round(float(net[last + 1] - net[last]), 2) == expected_step
    assert net[last + 1] >= net[last]


def _zero_single_maximum(start):
    """A modifier that reloads the parameters, zeroes the single maximum
    Savings Credit from ``start`` and processes them again."""

    def modify(simulation):
        tax_benefit_system = simulation.tax_benefit_system
        tax_benefit_system.reset_parameters()
        tax_benefit_system.parameters.get_child(f"{MAXIMUM}.SINGLE").update(
            start=instant(start), stop=instant(FAR), value=0
        )
        tax_benefit_system.process_parameters()

    return modify


def _maximum_reform_simulation(route, start, situation, extra=None):
    changes = {f"{MAXIMUM}.SINGLE": {f"{start}.{FAR}": 0}, **(extra or {})}
    if route == "reform":
        options = {"reform": changes}
    elif route == "scenario":
        options = {
            "scenario": Scenario(
                parameter_changes=changes, applied_before_data_load=True
            )
        }
    elif route == "structural":
        options = {"reform": Reform.from_dict(changes, country_id="uk")}
    else:
        options = {
            "scenario": Scenario(
                simulation_modifier=_zero_single_maximum(start),
                applied_before_data_load=True,
            )
        }
    return Simulation(situation=situation, **options)


SAVINGS_CREDIT_YEARS = [2027, 2028]


def _savings_credit_situation():
    """A single pensioner whose State Pension lies midway between the
    projected threshold and guarantee in each year, so Savings Credit is paid.
    Savings Credit needs State Pension age before 6 April 2016."""
    situation = _situation(False, SAVINGS_CREDIT_YEARS)
    pc = system.parameters.gov.dwp.pension_credit
    claimant = situation["people"]["claimant"]
    claimant["age"] = {year: 85 + year - 2027 for year in SAVINGS_CREDIT_YEARS}
    claimant["state_pension"] = {
        year: 52
        * (
            pc.savings_credit.threshold.SINGLE(f"{year}-04-30")
            + pc.guarantee_credit.minimum_guarantee.SINGLE(f"{year}-04-30")
        )
        / 2
        for year in SAVINGS_CREDIT_YEARS
    }
    return situation


@pytest.fixture(scope="module")
def baseline_savings_credit():
    simulation = Simulation(situation=_savings_credit_situation())
    return {
        year: simulation.calculate("savings_credit", year)[0]
        for year in SAVINGS_CREDIT_YEARS
    }


@pytest.mark.parametrize("route", MAXIMUM_ROUTES)
@pytest.mark.parametrize("start", ["2026-04-01", "2028-04-01"])
def test_maximum_reform_reaches_both_forecasts_through_every_route(
    route, start, baseline_savings_credit
):
    """A zero single maximum from the base year, or from a later one, makes
    the single threshold and the single and lone-parent higher allowances
    equal the guarantee from then on, so no Savings Credit is paid. Every
    forecast year reads the maximum the reform leaves; couples are unchanged.
    """
    first_year = int(start[:4])
    simulation = _maximum_reform_simulation(route, start, _savings_credit_situation())
    parameters = simulation.tax_benefit_system.parameters
    pc = parameters.gov.dwp.pension_credit
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for year in FORECAST_YEARS:
        at = f"{year}-04-30"
        phase_in = pc.savings_credit.rate.phase_in(at)
        for relationship, kinds in RELATIONSHIP_ALLOWANCES.items():
            guarantee = getattr(pc.guarantee_credit.minimum_guarantee, relationship)(at)
            maximum = getattr(pc.savings_credit.maximum, relationship)(at)
            threshold = getattr(pc.savings_credit.threshold, relationship)(at)
            assert threshold == pytest.approx(max(0, guarantee - maximum / phase_in)), (
                relationship,
                year,
            )
            for kind in kinds:
                assert getattr(allowances, kind).aged(at) == pytest.approx(
                    guarantee + maximum
                ), (kind, year)
            if relationship == "SINGLE" and year >= first_year:
                assert maximum == 0
                assert threshold == pytest.approx(guarantee)
    for path in PROJECTION_PATHS:
        if path.endswith(("COUPLE", "couple", "couple.aged")):
            for year in YEARS:
                at = f"{year}-04-30"
                assert parameters.get_child(path)(at) == pytest.approx(
                    system.parameters.get_child(path)(at)
                ), (path, year)
    for year in SAVINGS_CREDIT_YEARS:
        assert baseline_savings_credit[year] > 0
        if year >= first_year:
            assert simulation.calculate("savings_credit", year)[0] == 0, year
    if route != "modifier":
        # The dated routes keep prior law's projected maximum before the
        # change, so everything before it is as baseline. (Uprating extends a
        # parameter only from its last explicit value, so the modifier's
        # direct update holds the 2026 maximum until it starts, and the
        # forecasts follow that maximum instead, as checked above.)
        for path in PROJECTION_PATHS:
            for year in range(2026, first_year):
                at = f"{year}-04-30"
                assert parameters.get_child(path)(at) == pytest.approx(
                    system.parameters.get_child(path)(at)
                ), (path, year)
        for year in SAVINGS_CREDIT_YEARS:
            if year < first_year:
                assert simulation.calculate("savings_credit", year)[0] == pytest.approx(
                    baseline_savings_credit[year]
                ), year


@pytest.mark.parametrize("route", ["reform", "structural"])
@pytest.mark.parametrize(
    "own_base,value,index",
    [
        (
            f"{SAVINGS_CREDIT}.threshold.SINGLE",
            180,
            f"{SAVINGS_CREDIT}.threshold_uprating.SINGLE",
        ),
        (
            f"{HB_ALLOWANCES}.single.aged",
            250,
            f"{HB_ALLOWANCES}.protected_pension_age_uprating.single",
        ),
    ],
)
def test_a_reformed_own_base_keeps_its_index_beside_a_maximum_reform(
    route, own_base, value, index
):
    """A 2026 change to a threshold or allowance keeps its own index, which
    projects its reformed gap whether or not the maximum is reformed. Once the
    change ends, the dated routes restore prior law under the reform's other
    changes (``prior_law_projection``), here the zero maximum, so it then
    equals the guarantee, as the other amounts built from that maximum do."""
    simulation = _maximum_reform_simulation(
        route,
        "2026-04-01",
        _situation(False, [2026]),
        extra={own_base: {"year:2026-01-01:1": value}},
    )
    parameters = simulation.tax_benefit_system.parameters
    assumptions = parameters.gov.economic_assumptions
    earnings = assumptions.indices.earnings_uprating
    cpi = assumptions.indices.september_cpi_uprating
    earnings_growth = earnings("2027-04-30") / earnings("2026-04-30")
    cpi_growth = cpi("2027-04-30") / cpi("2026-04-30") - 1
    guarantee = float(system.parameters.get_child(f"{GUARANTEE}.SINGLE")("2026-04-30"))
    if "threshold" in own_base:
        # The reformed gap implies a £34.80 maximum at the 60% phase-in rate.
        implied_maximum = round(0.6 * (guarantee - value), 2)
        expected = (
            guarantee * earnings_growth - implied_maximum * (1 + cpi_growth) / 0.6
        )
    else:
        expected = guarantee * earnings_growth + (value - guarantee) * (1 + cpi_growth)
    assert parameters.get_child(own_base)("2026-04-30") == pytest.approx(value)
    assert parameters.get_child(index)("2027-04-30") == pytest.approx(expected / value)
    projected_guarantee = parameters.get_child(f"{GUARANTEE}.SINGLE")("2027-04-30")
    for path in (
        f"{SAVINGS_CREDIT}.threshold.SINGLE",
        f"{HB_ALLOWANCES}.single.aged",
        f"{HB_ALLOWANCES}.lone_parent.aged",
    ):
        assert parameters.get_child(path)("2027-04-30") == pytest.approx(
            projected_guarantee
        ), path

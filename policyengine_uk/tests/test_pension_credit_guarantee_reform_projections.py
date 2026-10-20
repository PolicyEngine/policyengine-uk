"""Guarantee reforms leave independently enacted pension-age projections intact."""

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import instant

from policyengine_uk import Simulation, system
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.housing_benefit.allowances.create_protected_pension_age_uprating import (
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
        for name in ("single", "couple")
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


def _assert_projections_unchanged(simulation):
    parameters = simulation.tax_benefit_system.parameters
    for path in PROJECTION_PATHS:
        actual = parameters.get_child(path)
        baseline = system.parameters.get_child(path)
        for year in YEARS:
            instant = f"{year}-04-30"
            assert actual(instant) == pytest.approx(baseline(instant)), (path, year)


@pytest.mark.parametrize("route", ["reform", "scenario"])
@pytest.mark.parametrize("couple,expected", [(False, 15_600), (True, 23_868)])
def test_2026_guarantee_reform_pays_the_reformed_credit_without_rebuilding_hb(
    couple, expected, route
):
    changes = {
        f"{GUARANTEE}.SINGLE": 300,
        f"{GUARANTEE}.COUPLE": 459,
    }
    simulation = _simulation(couple, changes, [2026], route)

    assert simulation.calculate("pension_credit", 2026)[0] == pytest.approx(expected)
    _assert_projections_unchanged(simulation)


@pytest.mark.parametrize("route", ["reform", "scenario"])
@pytest.mark.parametrize("couple,expected", [(False, 15_600), (True, 23_868)])
def test_simultaneous_calendar_guarantee_reforms_keep_independent_projections(
    couple, expected, route
):
    """Rebuilding prior law for either dated change must tolerate the other."""
    changes = {
        f"{GUARANTEE}.SINGLE": {"year:2026-01-01:1": 300},
        f"{GUARANTEE}.COUPLE": {"year:2026-01-01:1": 459},
    }
    simulation = _simulation(couple, changes, [2026], route)

    assert simulation.calculate("pension_credit", 2026)[0] == pytest.approx(expected)
    _assert_projections_unchanged(simulation)


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

    for name in ("single", "couple"):
        path = f"{HB_ALLOWANCES}.protected_pension_age_uprating.{name}"
        index = parameters.get_child(path)
        assumptions = parameters.gov.economic_assumptions
        earnings = assumptions.indices.statutory_earnings_floor
        earnings_growth = earnings("2027-04-30") / earnings("2026-04-30")
        cpi_growth = assumptions.statutory_uprating_inputs.cpi_september("2026-09-01")
        guarantee = guarantees[name.upper()]
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
        earnings = assumptions.indices.statutory_earnings_floor
        earnings_growth = earnings("2027-04-30") / earnings("2026-04-30")
        cpi_growth = assumptions.statutory_uprating_inputs.cpi_september("2026-09-01")
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
    _assert_projections_unchanged(simulation)


@pytest.mark.parametrize("couple", [False, True])
def test_earnings_path_guarantee_reform_keeps_independent_projections(couple):
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
    _assert_projections_unchanged(simulation)


@pytest.mark.parametrize("relationship", ["SINGLE", "COUPLE"])
def test_invalid_enacted_protected_allowance_still_raises(relationship):
    parameters = system.parameters
    guarantee = float(parameters.get_child(f"{GUARANTEE}.{relationship}")("2026-04-01"))
    assumptions = parameters.gov.economic_assumptions

    with pytest.raises(ValueError, match="cannot be lower than"):
        protected_allowance_index_values(
            guarantee - 0.01,
            guarantee,
            assumptions.indices.statutory_earnings_floor,
            assumptions.statutory_uprating_inputs.cpi_september,
            2026,
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


@pytest.mark.parametrize("route", ["reform", "scenario"])
@pytest.mark.parametrize(
    "relationship,allowance_name", [("SINGLE", "single"), ("COUPLE", "couple")]
)
def test_invalid_completed_joint_reform_still_raises(
    route, relationship, allowance_name
):
    changes = {
        f"{GUARANTEE}.{relationship}": {"year:2026-01-01:1": 230},
        f"{HB_ALLOWANCES}.{allowance_name}.aged": {"year:2026-01-01:1": 220},
    }
    with pytest.raises(ValueError, match="cannot be lower than"):
        _simulation(relationship == "COUPLE", changes, [2026], route)

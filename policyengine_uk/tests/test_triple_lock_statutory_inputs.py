"""The statutory uprating inputs, their forecasts, and how scenarios move them.

The April uprating of the State Pension uses September CPI and May-July
earnings growth from the previous year. These tests check that forecasts of
those inputs follow the OBR where it publishes them, fall back to
calendar-year growth after, respond to macro scenarios applied before the
data load, and can be set directly. They also check that Pension Credit uses
the same May-July earnings input without inheriting the CPI and 2.5% elements
of the State Pension triple lock, and that the earnings-path guarantee models
one reading of the plan announced in September 2026 as a parameter reform.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.model_api import Scenario
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.system import system

INPUTS = "gov.economic_assumptions.statutory_uprating_inputs"
OBR = "gov.economic_assumptions.yoy_growth.obr"
TRIPLE_LOCK = "gov.dwp.state_pension.triple_lock"
WEEKS_IN_YEAR = 52

PENSIONER = {
    "people": {"person": {"age": {2026: 70}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def parameters_under(changes):
    simulation = Simulation(
        situation=PENSIONER,
        scenario=Scenario(parameter_changes=changes, applied_before_data_load=True),
    )
    return simulation.tax_benefit_system.parameters


def uprating(parameters, year):
    return parameters.gov.economic_assumptions.yoy_growth.triple_lock(f"{year}-01-01")


def statutory_earnings_floor(parameters, year):
    return parameters.gov.economic_assumptions.yoy_growth.statutory_earnings_floor(
        f"{year}-01-01"
    )


def new_state_pension_weekly(parameters, year):
    return parameters.gov.dwp.state_pension.new_state_pension.amount(f"{year}-06-01")


def minimum_guarantee_weekly(parameters, relation_type, year):
    guarantee = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    return getattr(guarantee, relation_type)(f"{year}-06-01")


def statutory_inputs(parameters):
    return parameters.gov.economic_assumptions.statutory_uprating_inputs


def test_april_2027_uses_published_may_july_2026_earnings():
    """May-July 2026 total pay growth was 3.9% (first estimate), above the
    model's September 2026 CPI forecast (the OBR's 2.1%; August 2026 CPI was
    3.1%). Unless September CPI exceeds 3.9%, the new State Pension rises from
    £241.30 to £250.71 (before rounding to 5p)."""
    parameters = system.parameters
    assert uprating(parameters, 2027) == pytest.approx(0.039)
    assert new_state_pension_weekly(parameters, 2027) == pytest.approx(
        241.30 * 1.039, abs=0.005
    )


def test_pension_credit_uses_the_state_pension_statutory_earnings_input():
    parameters = system.parameters

    assert statutory_inputs(parameters).awe_total_pay_may_july(
        "2026-07-01"
    ) == pytest.approx(0.039)
    assert statutory_earnings_floor(parameters, 2027) == pytest.approx(0.039)
    assert minimum_guarantee_weekly(parameters, "SINGLE", 2027) == pytest.approx(
        238 * 1.039, rel=1e-5
    )
    assert minimum_guarantee_weekly(parameters, "COUPLE", 2027) == pytest.approx(
        363.25 * 1.039, rel=1e-5
    )


def test_pension_credit_earnings_floor_rounds_and_never_reduces_the_guarantee():
    parameters = parameters_under(
        {
            f"{INPUTS}.awe_total_pay_may_july": {
                "2027": 0.0124,
                "2028": -0.004,
            }
        }
    )

    assert [
        statutory_earnings_floor(parameters, year) for year in (2028, 2029)
    ] == pytest.approx([0.012, 0.0])
    for relation_type in ("SINGLE", "COUPLE"):
        guarantee_2027 = minimum_guarantee_weekly(parameters, relation_type, 2027)
        guarantee_2028 = minimum_guarantee_weekly(parameters, relation_type, 2028)
        guarantee_2029 = minimum_guarantee_weekly(parameters, relation_type, 2029)
        assert guarantee_2028 == pytest.approx(guarantee_2027 * 1.012, rel=1e-5)
        assert guarantee_2029 == pytest.approx(guarantee_2028, rel=1e-5)


def test_every_published_year_has_its_own_value():
    """A missing year would silently carry the previous year's figure."""
    inputs = statutory_inputs(system.parameters)
    for name, month_day, last_published in [
        ("cpi_september", "09-01", 2025),
        ("awe_total_pay_may_july", "07-01", 2026),
    ]:
        parameter = getattr(inputs, name)
        explicit = {value.instant_str for value in parameter.values_list}
        for year in range(2010, last_published + 1):
            assert f"{year}-{month_day}" in explicit, (name, year)


@pytest.mark.parametrize(
    "name, series, month_day, first_forecast_year",
    [
        ("cpi_september", "consumer_price_index", "09-01", 2026),
        ("awe_total_pay_may_july", "average_earnings", "07-01", 2027),
    ],
)
def test_forecasts_are_calendar_growth_plus_the_obr_gap(
    name, series, month_day, first_forecast_year
):
    parameters = system.parameters
    statutory = getattr(statutory_inputs(parameters), name)
    gap = getattr(statutory_inputs(parameters).forecast_gap, name)
    calendar = getattr(parameters.gov.economic_assumptions.yoy_growth.obr, series)
    last_year = max(int(v.instant_str[:4]) for v in calendar.values_list)
    assert last_year >= 2073
    for year in range(first_forecast_year, last_year + 1):
        observed = f"{year}-{month_day}"
        assert statutory(observed) == pytest.approx(
            calendar(f"{year}-01-01") + gap(observed), abs=1e-12
        ), year
        if year > 2030:
            # After the EFO horizon the forecast is calendar-year growth.
            assert gap(observed) == 0
    assert statutory(f"{last_year + 1}-{month_day}") is None


# OBR March 2026 EFO: September CPI from receipts Table 3.19 ("CPI used to
# uprate thresholds"), Q3 CPI from economy Table 1.7 for 2030, and Q2 average
# earnings growth on a year earlier from economy Table 1.6.
OBR_SEPTEMBER_CPI = {
    2026: 0.021157,
    2027: 0.020719,
    2028: 0.020299,
    2029: 0.020480,
    2030: 0.019996,
}
OBR_Q2_EARNINGS = {2027: 0.024266, 2028: 0.020795, 2029: 0.021852, 2030: 0.023890}


def test_baseline_forecasts_reproduce_the_obr_statutory_forecasts():
    """The gaps are measured from the calendar-year growth stored in
    yoy_growth.yaml, so stored growth plus the gap is the OBR's figure, to
    the 1e-5 the gaps are stored to. This fails if yoy_growth.yaml is
    refreshed without regenerating the gaps."""
    inputs = statutory_inputs(system.parameters)
    for year, value in OBR_SEPTEMBER_CPI.items():
        observed = inputs.cpi_september(f"{year}-09-01")
        assert observed == pytest.approx(value, abs=1e-5), year
    for year, value in OBR_Q2_EARNINGS.items():
        observed = inputs.awe_total_pay_may_july(f"{year}-07-01")
        assert observed == pytest.approx(value, abs=1e-5), year


def test_rule_reproduces_the_obr_triple_lock_forecast_from_its_own_inputs():
    """OBR Long-term economic determinants (March 2026 EFO), 'Triple Lock'
    row: 3.7% in April 2027 and 2.5% in April 2028-2031. With the published
    May-July 2026 figure removed, so earnings follow the OBR forecast, the
    rule gives the same rates."""

    def drop_may_july_2026(simulation):
        system_ = simulation.tax_benefit_system
        system_.reset_parameters()
        statutory_inputs(system_.parameters).awe_total_pay_may_july.update(
            period="year:2026-07-01:1", value=None
        )
        system_.process_parameters()

    simulation = Simulation(
        situation=PENSIONER,
        scenario=Scenario(
            simulation_modifier=drop_may_july_2026, applied_before_data_load=True
        ),
    )
    parameters = simulation.tax_benefit_system.parameters
    assert statutory_inputs(parameters).awe_total_pay_may_july(
        "2026-07-01"
    ) == pytest.approx(0.036736, abs=1e-5)
    assert [uprating(parameters, year) for year in range(2027, 2032)] == (
        pytest.approx([0.037, 0.025, 0.025, 0.025, 0.025])
    )


def test_horizon_runs_to_the_end_of_the_economic_assumptions():
    triple_lock = system.parameters.gov.economic_assumptions.yoy_growth.triple_lock
    years = sorted(int(value.instant_str[:4]) for value in triple_lock.values_list)
    assert years[0] == 2011
    assert years[-1] == 2074
    assert years == list(range(2011, 2075))
    # 2035 onwards follows the long-run earnings path, not a value carried
    # from the last year of the old horizon (2034).
    assert uprating(system.parameters, 2040) == pytest.approx(0.038)


def test_macro_scenario_on_calendar_growth_moves_the_uprating():
    """Raising 2027 earnings growth from 2.4% to 5% moves May-July 2027
    earnings with it (plus the OBR gap, 0.027pp) and so the April 2028 rise.

    Calendar-year series are keyed to 1 January, so the change is keyed
    year:2027-01-01:1; a bare "2027" names the fiscal year from 6 April 2027
    and would change the 2028 calendar-year value instead."""
    parameters = parameters_under(
        {f"{OBR}.average_earnings": {"year:2027-01-01:1": 0.05}}
    )
    assert statutory_inputs(parameters).awe_total_pay_may_july(
        "2027-07-01"
    ) == pytest.approx(0.05 + 0.00027)
    assert uprating(parameters, 2028) == pytest.approx(0.05)
    assert uprating(system.parameters, 2028) == pytest.approx(0.025)
    assert new_state_pension_weekly(parameters, 2028) > new_state_pension_weekly(
        system.parameters, 2028
    )
    # Only that year moves.
    assert uprating(parameters, 2029) == uprating(system.parameters, 2029)


def test_macro_scenario_moves_the_state_pension_in_a_microsimulation():
    """The rate reaches the benefit: a full-rate new State Pension recipient
    in 2026 data is paid the uprated full rate in 2028."""
    person = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "age": [70],
            "state_pension_reported": [241.30 * WEEKS_IN_YEAR],
        }
    )
    dataset = UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "council_tax": [2_000.0],
                "rent": [0.0],
            }
        ),
        fiscal_year=2026,
    )
    scenario = Scenario(
        parameter_changes={f"{OBR}.average_earnings": {"year:2027-01-01:1": 0.05}},
        applied_before_data_load=True,
    )
    baseline = Simulation(dataset=dataset)
    reformed = Simulation(dataset=dataset, scenario=scenario)

    baseline_pension = float(baseline.calculate("new_state_pension", 2028)[0])
    reformed_pension = float(reformed.calculate("new_state_pension", 2028)[0])
    full_rate_2027 = 241.30 * 1.039
    # Uprating indices are stored to 5 decimal places.
    assert baseline_pension == pytest.approx(
        full_rate_2027 * 1.025 * WEEKS_IN_YEAR, rel=1e-5
    )
    assert reformed_pension == pytest.approx(
        full_rate_2027 * 1.05 * WEEKS_IN_YEAR, rel=1e-5
    )


def test_setting_a_statutory_input_directly_overrides_its_forecast():
    """A scenario can supply September CPI and May-July earnings itself, for
    example from a model of the monthly series. The value replaces the
    forecast for that year only, whatever calendar-year growth says."""
    parameters = parameters_under(
        {
            f"{INPUTS}.awe_total_pay_may_july": {"2027": 0.07},
            f"{INPUTS}.cpi_september": {"2028": 0.061},
            f"{OBR}.average_earnings": {"year:2027-01-01:1": 0.01},
        }
    )
    assert uprating(parameters, 2028) == pytest.approx(0.07)
    assert uprating(parameters, 2029) == pytest.approx(0.061)
    assert uprating(parameters, 2030) == uprating(system.parameters, 2030)
    inputs = statutory_inputs(parameters)
    assert inputs.awe_total_pay_may_july("2028-07-01") == pytest.approx(
        statutory_inputs(system.parameters).awe_total_pay_may_july("2028-07-01")
    )


PLAN = {
    f"{TRIPLE_LOCK}.include_earnings": {"year:2030-01-01:100": False},
    f"{TRIPLE_LOCK}.earnings_path_guarantee": {"year:2030-01-01:100": True},
}


def test_plan_is_a_parameter_reform():
    """From April 2030: rises of at least max(CPI, 2.5%), and the pension
    never below an earnings link from its 2029-30 level.

    Earnings inputs of 1.0% (May-July 2029 and 2030) then 6.0% (2031) and
    3.0% (2032), CPI 2.0% throughout:

    - April 2030 and 2031: the floor, 2.5%, is above earnings (the triple
      lock would also pay 2.5%).
    - April 2032: the earnings path has grown 1.01 x 1.01 x 1.06 = 1.0813
      from the 2029-30 level against 1.025 x 1.025 = 1.0506 for the pension,
      so it rises by 1.0813 / 1.0506 - 1 = 2.92%, rounded up to 3.0%, where
      the triple lock pays 6.0%.
    - April 2033: the path grows 3.0% to 1.1137 and the pension, at
      1.0821, again needs 2.92%, rounded up to 3.0%, as the triple lock pays.
    """
    growth = {
        f"{INPUTS}.awe_total_pay_may_july": {
            "2029": 0.01,
            "2030": 0.01,
            "2031": 0.06,
            "2032": 0.03,
        },
        f"{INPUTS}.cpi_september": {str(year): 0.02 for year in range(2029, 2033)},
    }
    triple_lock = parameters_under(growth)
    plan = parameters_under({**growth, **PLAN})

    assert [uprating(triple_lock, year) for year in range(2030, 2034)] == (
        pytest.approx([0.025, 0.025, 0.06, 0.03])
    )
    assert [uprating(plan, year) for year in range(2030, 2034)] == (
        pytest.approx([0.025, 0.025, 0.030, 0.030])
    )
    # Unchanged before the switch.
    for year in range(2027, 2030):
        assert uprating(plan, year) == uprating(triple_lock, year)

    base = new_state_pension_weekly(plan, 2029)
    assert base == new_state_pension_weekly(triple_lock, 2029)
    earnings_path = base
    for year in range(2030, 2034):
        earnings_path *= 1 + [0.01, 0.01, 0.06, 0.03][year - 2030]
        # Uprating indices are stored to 5 decimal places.
        assert new_state_pension_weekly(plan, year) >= earnings_path * (1 - 1e-5)
        assert new_state_pension_weekly(plan, year) <= new_state_pension_weekly(
            triple_lock, year
        )


def test_plan_is_off_under_current_law():
    triple_lock = system.parameters.gov.dwp.state_pension.triple_lock
    for year in range(2011, 2075):
        assert not triple_lock.earnings_path_guarantee(f"{year}-04-30")


def test_without_the_triple_lock_the_pension_follows_earnings():
    """With the triple lock off, the statutory review (SSAA 1992 s150A)
    requires a rise of at least earnings growth, and none when earnings
    fall: 1.2% and then 0%, where the triple lock pays its 2.5% floor."""
    growth = {
        f"{INPUTS}.awe_total_pay_may_july": {"2027": 0.012, "2028": -0.004},
        f"{INPUTS}.cpi_september": {"2027": 0.02, "2028": 0.02},
    }
    triple_lock = parameters_under(growth)
    no_triple_lock = parameters_under(
        {**growth, f"{TRIPLE_LOCK}.active": {"year:2028-01-01:100": False}}
    )
    assert [uprating(triple_lock, year) for year in (2028, 2029)] == (
        pytest.approx([0.025, 0.025])
    )
    assert [uprating(no_triple_lock, year) for year in (2028, 2029)] == (
        pytest.approx([0.012, 0.0])
    )
    assert uprating(no_triple_lock, 2027) == uprating(triple_lock, 2027)


def test_no_economic_assumptions_leaves_only_the_floor():
    simulation = Simulation(situation=PENSIONER, scenario=no_economic_assumptions)
    parameters = simulation.tax_benefit_system.parameters
    cutoff_year = int(simulation.default_input_period)
    for year in range(cutoff_year + 2, 2075):
        assert uprating(parameters, year) == pytest.approx(0.025), year


def test_numpy_inputs_are_accepted():
    """Draws from a time-series model often arrive as numpy scalars."""
    simulation = Simulation(situation=PENSIONER)
    simulation.apply_parameter_changes(
        {
            f"{INPUTS}.cpi_september": {"2027": np.float64(0.045)},
            f"{OBR}.average_earnings": {"year:2028-01-01:1": np.float64(0.031)},
        }
    )
    parameters = simulation.tax_benefit_system.parameters
    assert uprating(parameters, 2028) == pytest.approx(0.045)
    assert uprating(parameters, 2029) == pytest.approx(0.031)


def test_a_zero_input_is_kept_not_forecast():
    """Zero is a value, not a missing figure: with the triple lock off, the
    rise is the 0% earnings input, not the 2.4% forecast."""
    parameters = parameters_under(
        {
            f"{INPUTS}.awe_total_pay_may_july": {"2027": 0.0},
            f"{INPUTS}.cpi_september": {"2027": 0.0},
            f"{TRIPLE_LOCK}.active": {"year:2028-01-01:1": False},
        }
    )
    inputs = statutory_inputs(parameters)
    assert inputs.awe_total_pay_may_july("2027-07-01") == 0
    assert inputs.cpi_september("2027-09-01") == 0
    assert uprating(parameters, 2028) == 0


def test_no_economic_assumptions_zeroes_the_forecast_inputs():
    simulation = Simulation(situation=PENSIONER, scenario=no_economic_assumptions)
    inputs = statutory_inputs(simulation.tax_benefit_system.parameters)
    cutoff_year = int(simulation.default_input_period)
    for year in range(max(cutoff_year, 2027), 2074):
        assert inputs.cpi_september(f"{year}-09-01") == 0, year
        assert inputs.awe_total_pay_may_july(f"{year}-07-01") == 0, year
        assert inputs.forecast_gap.cpi_september(f"{year}-09-01") == 0, year


def test_policy_levers_apply_from_the_april_of_the_year_they_name():
    """A floor of 3% keyed to the bare year 2028 (the fiscal year from
    6 April 2028) sets the April 2028 rise, read on 30 April, and no other
    year's; so do the include flags."""
    low_growth = {
        f"{INPUTS}.awe_total_pay_may_july": {"2027": 0.01, "2028": 0.01},
        f"{INPUTS}.cpi_september": {"2027": 0.05, "2028": 0.01},
    }
    floor = parameters_under(
        {**low_growth, f"{TRIPLE_LOCK}.minimum_rate": {"2028": 0.03}}
    )
    assert [uprating(floor, year) for year in (2028, 2029)] == pytest.approx(
        [0.05, 0.025]
    )
    floor_binds = parameters_under(
        {
            **low_growth,
            f"{INPUTS}.cpi_september": {"2027": 0.01, "2028": 0.01},
            f"{TRIPLE_LOCK}.minimum_rate": {"2028": 0.03},
        }
    )
    assert [uprating(floor_binds, year) for year in (2027, 2028, 2029)] == (
        pytest.approx([0.039, 0.03, 0.025])
    )
    no_cpi = parameters_under(
        {**low_growth, f"{TRIPLE_LOCK}.include_inflation": {"2028": False}}
    )
    assert uprating(no_cpi, 2028) == pytest.approx(0.025)


def test_inputs_are_rounded_to_published_precision():
    """The review uses the published one-decimal figure: 3.04% CPI pays
    3.0%."""
    parameters = parameters_under(
        {
            f"{INPUTS}.cpi_september": {"2027": 0.0304},
            f"{INPUTS}.awe_total_pay_may_july": {"2027": 0.0296},
        }
    )
    assert uprating(parameters, 2028) == pytest.approx(0.030)


def test_horizon_ends_with_the_shorter_calendar_series():
    parameters = parameters_under(
        {f"{OBR}.consumer_price_index": {"year:2075-01-01:1": 0.02}}
    )
    triple_lock = parameters.gov.economic_assumptions.yoy_growth.triple_lock
    assert max(int(v.instant_str[:4]) for v in triple_lock.values_list) == 2074


def test_the_rule_needs_the_forecasts_filled_in_first():
    """Read before the forecasts are filled in, September 2026 CPI is still
    null, and the rule refuses rather than guessing."""
    from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
        read_uprating_years,
    )
    from policyengine_uk.tax_benefit_system import CountryTaxBenefitSystem

    raw = CountryTaxBenefitSystem()
    raw.reset_parameters()
    with pytest.raises(ValueError, match="September 2026 CPI"):
        read_uprating_years(raw.parameters)

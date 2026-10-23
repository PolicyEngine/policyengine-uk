"""Reforms to parameters that processing reads, or generates, take effect.

Processing (``process_parameter_tree``) builds the triple lock rate from its
inputs, the economic indices from the growth rates and the uprated amounts
from the indices. A reform to one of those inputs, or to a generated series,
must move what is built from it; an ordinary reform must be unaffected.

Invariants:

1. Inputs reach what is built from them: a change to the triple lock's
   minimum rate or to calendar-year earnings growth moves the triple lock
   rate by its rule and the State Pension amounts by that rate, through the
   reform dict and both Scenario timings alike.
2. A year is one year on a calendar-year series: on the growth rates, the
   indices and the household tree, a bare year, its 1 January,
   ``year:Y-01-01:1`` and ``Y-01-01.Y-12-31`` give identical parameters, and
   the value shown for year Y is the value processing used for year Y (the
   index grows by it in Y; the May to July Y earnings input moves one for
   one; the April Y+1 triple lock follows).
3. Generated series take effect: a triple lock rate set by reform equals
   the same rate set through its statutory override (``outturn``), on every
   route; a changed index uprates the parameters indexed by it.
4. Ordinary reforms are unaffected (differential): for every parameter that
   is not a calendar-year series, the reform dict and ``parameter_changes``
   read every key exactly as before.
5. Monotonicity: the April 2028 State Pension is non-decreasing in the
   minimum rate.
6. Baselines stay current law: ``sim.baseline`` and ``parameters.baseline``.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk import tax_benefit_system as tbs_module
from policyengine_uk.utils.dated_reforms import (
    ReformPeriodWarning,
    read_parameter_changes,
    read_reform_dict,
)
from policyengine_uk.utils.scenario import Scenario

MINIMUM_RATE = "gov.dwp.state_pension.triple_lock.minimum_rate"
OUTTURN = "gov.dwp.state_pension.triple_lock.outturn"
GROWTH = "gov.economic_assumptions.yoy_growth"
AVERAGE_EARNINGS = f"{GROWTH}.obr.average_earnings"
TRIPLE_LOCK = f"{GROWTH}.triple_lock"
LAGGED_CPI = f"{GROWTH}.obr.lagged_cpi"
INDICES = "gov.economic_assumptions.indices"
CPI_INDEX = f"{INDICES}.obr.consumer_price_index"
INPUTS = "gov.economic_assumptions.statutory_uprating_inputs"
AWE = f"{INPUTS}.awe_total_pay_may_july"
AWE_GAP = f"{INPUTS}.forecast_gap.awe_total_pay_may_july"
CPI_SEPTEMBER = f"{INPUTS}.cpi_september"
NEW_STATE_PENSION = "gov.dwp.state_pension.new_state_pension.amount"
BASIC_STATE_PENSION = "gov.dwp.state_pension.basic_state_pension.amount"
POVERTY_LINE = "household.poverty.absolute_poverty_threshold_bhc"
FINANCIAL_ASSETS = "household.wealth.financial_assets"
CORPORATE_WEALTH = "household.wealth.corporate_wealth"
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
LSR_LEGACY = "gov.simulation.labor_supply_responses.income_elasticity"
LSR = "gov.simulation.labour_supply_responses.income_elasticity"
FAR = "2100-12-31"

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)

PENSIONER = {
    "people": {
        "pensioner": {
            "age": {2025: 70},
            "state_pension_type": {2025: "NEW"},
            # Above the full rate, so the amount paid is the full rate.
            "state_pension_reported": {2025: 50_000},
        }
    },
    "benunits": {"benunit": {"members": ["pensioner"]}},
    "households": {"household": {"members": ["pensioner"]}},
}


def value(simulation, path, instant):
    return simulation.tax_benefit_system.parameters.get_child(path)(instant)


def weekly(simulation, path, year):
    """A State Pension rate in force over fiscal year ``year``."""
    return float(value(simulation, path, f"{year}-04-30"))


def growth(simulation, path, year):
    """An index's growth over calendar year ``year``."""
    return (
        value(simulation, path, f"{year}-01-01")
        / value(simulation, path, f"{year - 1}-01-01")
        - 1
    )


def published(rate):
    """A growth rate to 0.1 percentage points, halves away from zero."""
    return float(Decimal(repr(float(rate))).quantize(Decimal("0.001"), ROUND_HALF_UP))


def via_reform_dict(change, situation=PENSIONER):
    return Simulation(situation=situation, reform=change)


def via_parameter_changes(change, situation=PENSIONER):
    return Simulation(situation=situation, scenario=Scenario(parameter_changes=change))


def via_scenario_before_data_load(change, situation=PENSIONER):
    return Simulation(
        situation=situation,
        scenario=Scenario(parameter_changes=change, applied_before_data_load=True),
    )


ROUTES = [via_reform_dict, via_parameter_changes, via_scenario_before_data_load]


@pytest.fixture(scope="module")
def baseline():
    return Simulation(situation=PENSIONER)


# 1. Inputs reach what is built from them.


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    "spec",
    [0.1, {"2028": 0.1}, {f"2028-01-01.{FAR}": 0.1}],
    ids=["scalar", "bare-year", "interval"],
)
def test_the_minimum_rate_moves_the_triple_lock_and_the_state_pension(
    route, spec, baseline
):
    reformed = route({MINIMUM_RATE: spec})
    assert value(reformed, TRIPLE_LOCK, "2028-01-01") == pytest.approx(0.1)
    for path in (NEW_STATE_PENSION, BASIC_STATE_PENSION):
        if isinstance(spec, dict):
            # A change from 2028 leaves the April 2027 uprating alone; a
            # scalar applies from 2023 (or 2000) and so raises it too.
            assert weekly(reformed, path, 2027) == weekly(baseline, path, 2027)
        assert weekly(reformed, path, 2028) == pytest.approx(
            weekly(reformed, path, 2027) * 1.1, abs=0.006
        )
    pension = float(reformed.calculate("new_state_pension", 2028).sum())
    assert pension == pytest.approx(
        weekly(reformed, NEW_STATE_PENSION, 2028) * 52, rel=1e-6
    )


@PROPERTY_SETTINGS
@given(
    low=st.integers(0, 150).map(lambda n: n / 1000),
    high=st.integers(0, 150).map(lambda n: n / 1000),
)
def test_the_state_pension_is_non_decreasing_in_the_minimum_rate(low, high):
    low, high = sorted((low, high))
    pensions = [
        weekly(via_reform_dict({MINIMUM_RATE: rate}), NEW_STATE_PENSION, 2028)
        for rate in (low, high)
    ]
    assert pensions[0] <= pensions[1]


@PROPERTY_SETTINGS
@given(
    rate=st.integers(-50, 200).map(lambda n: n / 1000 + 0.0003),
    year=st.integers(2027, 2030),
)
def test_earnings_growth_sets_the_next_aprils_triple_lock_by_its_rule(
    rate, year, baseline
):
    reformed = via_reform_dict({AVERAGE_EARNINGS: {str(year): rate}})
    # The May to July input is calendar-year growth plus the OBR gap.
    gap = value(baseline, AWE_GAP, f"{year}-07-01") or 0
    earnings = value(reformed, AWE, f"{year}-07-01")
    assert earnings == pytest.approx(rate + gap, abs=1e-12)
    cpi = value(reformed, CPI_SEPTEMBER, f"{year}-09-01")
    expected = max(
        value(reformed, MINIMUM_RATE, f"{year + 1}-04-30"),
        published(rate + gap),
        published(cpi),
    )
    assert value(reformed, TRIPLE_LOCK, f"{year + 1}-01-01") == pytest.approx(expected)
    # The year before is untouched.
    assert value(reformed, TRIPLE_LOCK, f"{year}-01-01") == value(
        baseline, TRIPLE_LOCK, f"{year}-01-01"
    )
    assert weekly(reformed, NEW_STATE_PENSION, year + 1) == pytest.approx(
        weekly(reformed, NEW_STATE_PENSION, year) * (1 + expected), abs=0.006
    )


# 2. A year is one year on a calendar-year series.


CALENDAR_KEYS = [
    "2027",
    2027,
    "2027-01-01",
    "year:2027-01-01:1",
    "2027-01-01.2027-12-31",
]


def observed(simulation):
    """What processing built from 2027 earnings growth, and what it shows."""
    years = range(2025, 2032)
    return (
        [value(simulation, AVERAGE_EARNINGS, f"{y}-01-01") for y in years],
        [
            value(simulation, f"{INDICES}.obr.average_earnings", f"{y}-01-01")
            for y in years
        ],
        [value(simulation, AWE, f"{y}-07-01") for y in years],
        [value(simulation, TRIPLE_LOCK, f"{y}-01-01") for y in years],
        [weekly(simulation, NEW_STATE_PENSION, y) for y in years],
    )


@pytest.mark.parametrize("route", [via_reform_dict, via_parameter_changes])
def test_every_key_for_a_year_of_growth_gives_the_same_parameters(route):
    results = [observed(route({AVERAGE_EARNINGS: {key: 0.2}})) for key in CALENDAR_KEYS]
    assert all(result == results[0] for result in results)


def test_the_growth_shown_for_a_year_is_the_growth_used_for_it(baseline):
    reformed = via_reform_dict({AVERAGE_EARNINGS: {"2027": 0.2}})
    assert value(reformed, AVERAGE_EARNINGS, "2027-01-01") == 0.2
    assert growth(reformed, f"{INDICES}.obr.average_earnings", 2027) == pytest.approx(
        0.2, abs=1e-4
    )
    assert growth(reformed, f"{INDICES}.obr.average_earnings", 2028) == pytest.approx(
        growth(baseline, f"{INDICES}.obr.average_earnings", 2028), abs=1e-4
    )
    gap = value(baseline, AWE_GAP, "2027-07-01")
    assert value(reformed, AWE, "2027-07-01") == pytest.approx(0.2 + gap)
    assert value(reformed, AWE, "2028-07-01") == value(baseline, AWE, "2028-07-01")
    assert value(reformed, TRIPLE_LOCK, "2028-01-01") == pytest.approx(0.2)
    assert value(reformed, TRIPLE_LOCK, "2029-01-01") == value(
        baseline, TRIPLE_LOCK, "2029-01-01"
    )


def statutory_growth_leaves():
    growth_node = tbs_module.statutory_parameters().get_child(GROWTH)
    return sorted(
        parameter.name
        for parameter in growth_node.get_descendants()
        if isinstance(parameter, Parameter)
        and all(isinstance(v.value, (int, float)) for v in parameter.values_list)
    )


GROWTH_LEAVES = statutory_growth_leaves()


@PROPERTY_SETTINGS
@given(
    path=st.sampled_from(GROWTH_LEAVES),
    year=st.integers(2025, 2035),
    rate=st.integers(-50, 300).map(lambda n: n / 1000),
)
def test_each_growth_rate_moves_its_index_in_the_year_it_is_shown(
    path, year, rate, baseline
):
    index = path.replace("yoy_growth", "indices")
    reformed = via_reform_dict({path: {str(year): rate}})
    assert value(reformed, path, f"{year}-01-01") == pytest.approx(rate)
    assert growth(reformed, index, year) == pytest.approx(rate, abs=2e-4)
    for other in (year - 1, year + 1):
        assert growth(reformed, index, other) == pytest.approx(
            growth(baseline, index, other), abs=2e-4
        )


def test_a_bare_year_on_the_household_tree_is_that_calendar_year(baseline):
    reformed = via_reform_dict({FINANCIAL_ASSETS: {"2027": 1e13}})
    assert value(reformed, FINANCIAL_ASSETS, "2027-01-01") == 1e13
    assert value(reformed, FINANCIAL_ASSETS, "2028-01-01") == value(
        baseline, FINANCIAL_ASSETS, "2028-01-01"
    )
    # Corporate wealth is uprated by financial assets, in the same year.
    ratio = 1e13 / value(baseline, FINANCIAL_ASSETS, "2027-01-01")
    assert value(reformed, CORPORATE_WEALTH, "2027-01-01") == pytest.approx(
        value(baseline, CORPORATE_WEALTH, "2027-01-01") * ratio, rel=1e-9
    )
    assert value(reformed, CORPORATE_WEALTH, "2028-01-01") == value(
        baseline, CORPORATE_WEALTH, "2028-01-01"
    )


def test_calendar_year_series_are_the_growth_rates_indices_and_household_tree():
    reads = tbs_module.parameter_reads_calendar_years()
    paths = tbs_module._leaf_paths(tbs_module.processed_parameters())
    for path in paths:
        if path.startswith("baseline."):
            continue
        expected = path.startswith((f"{GROWTH}.", f"{INDICES}.", "household."))
        assert reads(path) is expected, path
    assert not reads("gov.not.a.parameter")


# 3. Generated series take effect.


@pytest.mark.parametrize(
    "change",
    [
        {TRIPLE_LOCK: {"2028": 0.05}},
        {TRIPLE_LOCK: {"2028-01-01.2028-12-31": 0.05}},
        # The statutory override of the same rate (read at 30 April).
        {OUTTURN: {"2028-04-06.2029-04-05": 0.05}},
    ],
    ids=["generated-bare-year", "generated-interval", "statutory-outturn"],
)
@pytest.mark.parametrize("route", ROUTES)
def test_a_triple_lock_rate_set_by_reform_uprates_the_state_pension(
    route, change, baseline
):
    reformed = route(change)
    years = range(2026, 2036)
    assert value(reformed, TRIPLE_LOCK, "2028-01-01") == pytest.approx(0.05)
    for year in years:
        if year == 2028:
            continue
        assert value(reformed, TRIPLE_LOCK, f"{year}-01-01") == value(
            baseline, TRIPLE_LOCK, f"{year}-01-01"
        )
    pensions = [weekly(reformed, NEW_STATE_PENSION, year) for year in years]
    reference = [
        weekly(
            via_reform_dict({OUTTURN: {"2028-04-06.2029-04-05": 0.05}}),
            NEW_STATE_PENSION,
            y,
        )
        for y in years
    ]
    assert pensions == reference
    assert pensions[2] == pytest.approx(
        weekly(baseline, NEW_STATE_PENSION, 2027) * 1.05, abs=0.006
    )


def test_reform_from_dict_sets_a_generated_series(baseline):
    change = {TRIPLE_LOCK: {"2028-01-01.2028-12-31": 0.05}}
    reformed = Simulation(situation=PENSIONER, reform=Reform.from_dict(change))
    assert weekly(reformed, NEW_STATE_PENSION, 2028) == pytest.approx(
        weekly(baseline, NEW_STATE_PENSION, 2027) * 1.05, abs=0.006
    )


def test_a_changed_index_uprates_the_parameters_indexed_by_it(baseline):
    level = value(baseline, CPI_INDEX, "2029-01-01") * 1.1
    reformed = via_reform_dict({CPI_INDEX: {"2029": level}})
    for year, factor in ((2028, 1), (2029, 1.1), (2030, 1)):
        assert value(reformed, POVERTY_LINE, f"{year}-01-01") == pytest.approx(
            value(baseline, POVERTY_LINE, f"{year}-01-01") * factor, rel=1e-4
        )


def test_a_lagged_series_moves_its_index(baseline):
    reformed = via_reform_dict({LAGGED_CPI: {"2028": 0.1}})
    assert growth(reformed, f"{INDICES}.obr.lagged_cpi", 2028) == pytest.approx(
        0.1, abs=1e-4
    )
    assert growth(reformed, f"{INDICES}.obr.lagged_cpi", 2029) == pytest.approx(
        growth(baseline, f"{INDICES}.obr.lagged_cpi", 2029), abs=1e-4
    )


def test_generated_parameters_are_the_series_processing_builds():
    generates = tbs_module.generated_parameter_defines()
    statutory = tbs_module.statutory_parameter_defines()
    processed = tbs_module.processed_parameters()
    protected_allowance_index = (
        "gov.dwp.housing_benefit.allowances.protected_pension_age_uprating"
    )
    savings_credit_index = "gov.dwp.pension_credit.savings_credit.threshold_uprating"
    # Pension-age forecast indices are generated in their program trees.
    generated_prefixes = (
        f"{INDICES}.",
        f"{GROWTH}.",
        f"{protected_allowance_index}.",
        f"{savings_credit_index}.",
    )
    for path in tbs_module._leaf_paths(processed):
        if path.startswith("baseline.") or path.startswith(
            "gov.simulation.labor_supply_responses."
        ):
            assert not generates(path), path
            continue
        built = path.startswith(generated_prefixes) and not statutory(path)
        assert generates(path) is built, path
    for relationship in ("single", "lone_parent", "couple"):
        assert generates(f"{protected_allowance_index}.{relationship}")
        assert not generates(f"gov.dwp.housing_benefit.allowances.{relationship}.aged")
    for relationship in ("SINGLE", "COUPLE"):
        assert generates(f"{savings_credit_index}.{relationship}")
        assert not generates(
            f"gov.dwp.pension_credit.savings_credit.threshold.{relationship}"
        )
    assert generates(TRIPLE_LOCK)
    assert generates(f"{INDICES}.uc_standard_allowance")
    assert not generates(MINIMUM_RATE)
    # The CGT projection index is added after processing, outside it.
    assert not generates(f"{INDICES}.capital_gains")


@pytest.mark.parametrize(
    "route",
    [
        via_reform_dict,
        lambda change: Simulation(situation=PENSIONER, reform=Reform.from_dict(change)),
    ],
    ids=["reform-dict", "reform-from-dict"],
)
def test_a_labour_supply_alias_path_changes_the_parameter_it_copies(route):
    reformed = route({LSR_LEGACY: {f"2025-01-01.{FAR}": 0.5}})
    assert value(reformed, LSR, "2028-01-01") == 0.5


@pytest.mark.parametrize("route", [via_reform_dict, via_parameter_changes])
def test_an_unknown_path_is_still_rejected(route):
    with pytest.raises(ValueError, match="Could not find the parameter"):
        route({"gov.not.a.parameter": {"2027": 1}})


@pytest.mark.parametrize("route", [via_reform_dict, via_parameter_changes])
@pytest.mark.parametrize("key", ["2030", "2030-01-01", "2030-01-01.2030-12-31"])
def test_a_year_of_an_uprated_household_parameter_leaves_the_others_on_prior_law(
    route, key, baseline
):
    # The poverty line's stated values end before 2030; uprating projects it.
    reformed = route({POVERTY_LINE: {key: 500}})
    for year in range(2025, 2036):
        expected = (
            500 if year == 2030 else value(baseline, POVERTY_LINE, f"{year}-01-01")
        )
        assert value(reformed, POVERTY_LINE, f"{year}-01-01") == pytest.approx(expected)


def test_a_reprocessing_modifier_keeps_a_generated_series_change(baseline):
    from policyengine_uk.scenarios import no_economic_assumptions

    scenario = (
        Scenario.from_reform({TRIPLE_LOCK: {"2028": 0.05}}) + no_economic_assumptions
    )
    reformed = Simulation(situation=PENSIONER, scenario=scenario)
    assert value(reformed, TRIPLE_LOCK, "2028-01-01") == pytest.approx(0.05)
    assert weekly(reformed, NEW_STATE_PENSION, 2028) == pytest.approx(
        weekly(reformed, NEW_STATE_PENSION, 2027) * 1.05, abs=0.006
    )


def test_scenario_apply_on_a_built_simulation_keeps_its_legacy_reading(baseline):
    # Scenario.apply edits the annualised parameters and never rebuilds them.
    simulation = Simulation(situation=PENSIONER)
    Scenario.from_reform({TRIPLE_LOCK: {"2028": 0.05}}).apply(simulation)
    assert value(simulation, TRIPLE_LOCK, "2028-01-01") == pytest.approx(0.05)
    assert weekly(simulation, NEW_STATE_PENSION, 2028) == weekly(
        baseline, NEW_STATE_PENSION, 2028
    )


@pytest.mark.parametrize("route", [via_reform_dict, via_parameter_changes])
def test_a_path_and_its_alias_in_one_reform_are_merged_in_order(route):
    reformed = route(
        {LSR: {f"2030-01-01.{FAR}": 0.2}, LSR_LEGACY: {"2026-01-01.2027-12-31": 0.1}}
    )
    for year, expected in ((2025, 0), (2026, 0.1), (2028, 0), (2030, 0.2)):
        assert value(reformed, LSR, f"{year}-01-01") == pytest.approx(expected)


def test_scenarios_spelling_a_path_differently_combine():
    combined = Scenario(parameter_changes={LSR: {f"2030-01-01.{FAR}": 0.2}}) + Scenario(
        parameter_changes={LSR_LEGACY: {"2026-01-01.2027-12-31": 0.1}}
    )
    reformed = Simulation(situation=PENSIONER, scenario=combined)
    assert value(reformed, LSR, "2026-01-01") == pytest.approx(0.1)
    assert value(reformed, LSR, "2030-01-01") == pytest.approx(0.2)


WIDE = f"2025-01-01.{FAR}"
NARROW = "2026-01-01.2027-12-31"


@pytest.mark.parametrize(
    "stages",
    [
        [{WIDE: 0.1}, 0.2, {NARROW: 0.3}],
        [{WIDE: 0.1}, {WIDE: 0.2}, {WIDE: 0.3}],
        [0.1, {NARROW: 0.2}, 0.3],
        [{NARROW: 0.1}, {WIDE: 0.2}, {NARROW: 0.3}],
    ],
    ids=["dict-scalar-dict", "same-period", "scalar-dict-scalar", "narrow-wide-narrow"],
)
@pytest.mark.parametrize(
    "spellings", [(LSR, LSR_LEGACY, LSR), (LSR_LEGACY, LSR, LSR_LEGACY)]
)
def test_sums_of_scenarios_spelling_a_path_differently_match_one_spelling(
    stages, spellings
):
    def summed(paths):
        scenarios = [
            Scenario(parameter_changes={path: stage})
            for path, stage in zip(paths, stages)
        ]
        return Simulation(
            situation=PENSIONER, scenario=scenarios[0] + scenarios[1] + scenarios[2]
        )

    mixed, single = summed(spellings), summed((LSR, LSR, LSR))
    for year in (2024, 2025, 2026, 2028, 2031):
        assert value(mixed, LSR, f"{year}-01-01") == value(single, LSR, f"{year}-01-01")


@pytest.mark.parametrize("year", [2005, 2006, 2007, 2008])
@pytest.mark.parametrize("path", [f"{GROWTH}.obr.rpi", TRIPLE_LOCK])
def test_a_change_before_a_series_starts_resumes_with_its_first_value(
    path, year, baseline
):
    # Before 2015 nothing is backdated, so a change ending before a series'
    # first stated value resumes with that value rather than with nothing.
    reformed = via_reform_dict({path: {str(year): 0.1}})
    assert value(reformed, path, f"{year}-01-01") == pytest.approx(0.1)
    for later in range(2016, 2030):
        assert value(reformed, path, f"{later}-01-01") == value(
            baseline, path, f"{later}-01-01"
        )


def test_a_stated_null_resumes_as_null(baseline):
    # The triple lock override is null outside the years it overrides.
    reformed = via_reform_dict({OUTTURN: {"2028-04-06.2029-04-05": 0.05}})
    assert value(reformed, OUTTURN, "2029-04-30") is None
    assert value(reformed, TRIPLE_LOCK, "2029-01-01") == value(
        baseline, TRIPLE_LOCK, "2029-01-01"
    )


@pytest.mark.parametrize(
    "path, kind",
    [(AVERAGE_EARNINGS, "calendar"), (PERSONAL_ALLOWANCE, "fiscal")],
)
def test_a_single_day_key_warning_names_the_years_a_bare_year_covers(path, kind):
    with pytest.warns(
        ReformPeriodWarning, match=f"for one {kind} year use the bare year"
    ):
        read_reform_dict(
            {path: {"2027-04-06": 1}},
            tbs_module.reform_parameter_defines(),
            warn=True,
            calendar_years=tbs_module.parameter_reads_calendar_years(),
        )


# 4. Ordinary reforms are unaffected.


def statutory_leaves():
    return tbs_module._leaf_paths(tbs_module.statutory_parameters())


ORDINARY = [
    path
    for path in statutory_leaves()
    if path.startswith("gov.")
    and not path.startswith(("gov.economic_assumptions.yoy_growth.",))
]
KEYS = st.one_of(
    st.integers(2016, 2040),
    st.integers(2016, 2040).map(str),
    st.integers(2016, 2040).map(lambda y: f"{y}-01-01"),
    st.integers(2016, 2040).map(lambda y: f"{y}-04-06"),
    st.integers(2016, 2040).map(lambda y: f"year:{y}-01-01:1"),
    st.integers(2016, 2040).map(lambda y: f"{y}-04-06.{y + 1}-04-05"),
)


@settings(max_examples=200, deadline=None, derandomize=True)
@given(path=st.sampled_from(ORDINARY), key=KEYS)
def test_ordinary_parameters_read_every_key_as_before(path, key):
    reads = tbs_module.parameter_reads_calendar_years()
    defines = tbs_module.reform_parameter_defines()
    change = {path: {key: 1}}
    assert read_reform_dict(change, defines, calendar_years=reads) == read_reform_dict(
        change, defines
    )
    assert read_parameter_changes(
        change, calendar_years=reads
    ) == read_parameter_changes(change)


def test_an_ordinary_bare_year_is_still_the_fiscal_year(baseline):
    reformed = via_reform_dict({PERSONAL_ALLOWANCE: {"2027": 20_000}})
    interval = via_reform_dict({PERSONAL_ALLOWANCE: {"2027-04-06.2028-04-05": 20_000}})
    for year in range(2025, 2032):
        assert value(reformed, PERSONAL_ALLOWANCE, f"{year}-01-01") == value(
            interval, PERSONAL_ALLOWANCE, f"{year}-01-01"
        )
    assert value(reformed, NEW_STATE_PENSION, "2028-04-30") == value(
        baseline, NEW_STATE_PENSION, "2028-04-30"
    )


# 6. Baselines stay current law.


@pytest.mark.parametrize(
    "change",
    [
        {MINIMUM_RATE: 0.1},
        {AVERAGE_EARNINGS: {"2027": 0.2}},
        {TRIPLE_LOCK: {"2028": 0.05}},
    ],
    ids=["input", "calendar-year-series", "generated"],
)
def test_baselines_stay_current_law(change, baseline):
    reformed = via_reform_dict(change)
    for year in (2028, 2029):
        assert weekly(reformed.baseline, NEW_STATE_PENSION, year) == weekly(
            baseline, NEW_STATE_PENSION, year
        )
        assert float(
            reformed.tax_benefit_system.parameters.baseline.get_child(
                NEW_STATE_PENSION
            )(f"{year}-04-30")
        ) == weekly(baseline, NEW_STATE_PENSION, year)
    after = Simulation(situation=PENSIONER)
    assert weekly(after, NEW_STATE_PENSION, 2028) == weekly(
        baseline, NEW_STATE_PENSION, 2028
    )


@pytest.mark.parametrize("summed", [False, True])
def test_scenario_apply_changes_the_parameter_an_alias_path_copies(summed):
    scenario = Scenario(parameter_changes={LSR_LEGACY: 0.3})
    if summed:
        scenario = Scenario() + scenario
    simulation = Simulation(situation=PENSIONER)
    scenario.apply(simulation)
    assert value(simulation, LSR, "2028-01-01") == pytest.approx(0.3)

"""The September CPI benefit uprating in the full parameter tree.

Most benefits rise each April by the previous September's CPI 12-month rate
(Social Security Administration Act 1992 s150; written statement HCWS1101).
These tests check the April rise against September CPI, that every
parameter uprated by ``gov.benefit_uprating_cpi`` follows it after its last
published value, that the State Pension triple lock reads the same September
figure, and that scenarios on the inputs move benefit rates.
"""

import pytest
from policyengine_core.parameters import Parameter, ParameterNode, load_parameter_file

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    read_uprating_years,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_september_cpi_uprating import (
    FIRST_UPRATING_YEAR,
    september_cpi_uprating_rate,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    last_input_year,
)
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import COUNTRY_DIR

INDEX = "gov.benefit_uprating_cpi"
INPUTS = "gov.economic_assumptions.statutory_uprating_inputs"
OBR = "gov.economic_assumptions.yoy_growth.obr"
# create_economic_assumption_indices builds the indices to 2039.
LAST_INDEX_YEAR = 2039

# The index is stored to 5 decimal places, which leaves a few hundredths of
# a penny of noise on a weekly rate.
PENNY_TENTH = 1e-3

PERSON = {
    "people": {"person": {"age": {2026: 40}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def parameters_under(changes):
    simulation = Simulation(
        situation=PERSON,
        scenario=Scenario(parameter_changes=changes, applied_before_data_load=True),
    )
    return simulation.tax_benefit_system.parameters


def rise(parameters, year):
    return parameters.gov.economic_assumptions.yoy_growth.september_cpi_uprating(
        f"{year}-01-01"
    )


def carers_allowance(parameters, year):
    return parameters.gov.dwp.carers_allowance.rate(f"{year}-04-30")


def test_each_april_rises_by_the_previous_september_cpi():
    parameters = system.parameters
    cpi_september = (
        parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    )
    last_year = last_input_year(parameters) + 1
    assert last_year >= 2074
    for year in range(FIRST_UPRATING_YEAR, last_year + 1):
        september = cpi_september(f"{year - 1}-09-01")
        assert rise(parameters, year) == september_cpi_uprating_rate(september), year


# ONS D7G7, September of the year before each April.
PUBLISHED_APRIL_RISES = {
    2011: 0.031,
    2012: 0.052,
    2013: 0.022,
    2014: 0.027,
    2015: 0.012,
    # September 2015 CPI was -0.1%: benefits were held, not cut.
    2016: 0.0,
    2017: 0.010,
    2018: 0.030,
    2019: 0.024,
    2020: 0.017,
    2021: 0.005,
    2022: 0.031,
    2023: 0.101,
    2024: 0.067,
    2025: 0.017,
    2026: 0.038,
    # ONS CPI release of 21 October 2026.
    2027: 0.035,
}


def test_published_september_rates_give_the_april_rises():
    for year, published in PUBLISHED_APRIL_RISES.items():
        assert rise(system.parameters, year) == published, year


def test_april_2028_rise_is_the_obr_september_2027_forecast():
    """OBR October 2026 EFO: calendar-year 2027 CPI plus the receipts Table
    4.19 gap for September 2027 (3.4400%), applied as the published 3.4%."""
    assert rise(system.parameters, 2028) == 0.034


def test_the_index_rises_by_each_april_rise():
    parameters = system.parameters
    index = parameters.gov.benefit_uprating_cpi
    for year in range(2011, LAST_INDEX_YEAR + 1):
        growth = index(f"{year}-04-30") / index(f"{year - 1}-04-30") - 1
        assert growth == pytest.approx(rise(parameters, year), abs=2e-5), year


def uprating_parameter(parameter):
    uprating = (parameter.metadata or {}).get("uprating")
    if isinstance(uprating, dict):
        return uprating.get("parameter")
    return uprating


def uprated_by_the_index(node):
    for parameter in node.get_descendants():
        if isinstance(parameter, Parameter) and uprating_parameter(parameter) == INDEX:
            yield parameter


def last_published_year(raw, name):
    """Year of the last value written in the parameter's YAML file."""
    return max(int(value.instant_str[:4]) for value in raw.get_child(name).values_list)


# An older, unrelated omission: the national financial wealth total is meant
# to project by GDP per capita, but its node metadata never reaches this leaf.
# Keep its existing corporate-incidence fallback unchanged in this benefit fix.
# Limit the exception to this exact leaf so new omissions still fail.
KNOWN_UNPROPAGATED_UPRATING = {
    (
        "household.wealth.national_balance_sheet.household",
        "household.wealth.national_balance_sheet.household.financial_net_worth",
    ),
}


def test_node_uprating_reaches_every_leaf():
    """A node's uprating must reach its leaves, which core actually uprates.

    A leaf can override the parent's index, as the earnings-linked HB income
    bands do, but must not silently lose uprating altogether.
    """
    missing = set()
    for node in system.parameters.get_descendants():
        if not isinstance(node, ParameterNode) or not uprating_parameter(node):
            continue
        for leaf in node.get_descendants():
            if isinstance(leaf, Parameter) and not uprating_parameter(leaf):
                missing.add((node.name, leaf.name))
    assert missing <= KNOWN_UNPROPAGATED_UPRATING, missing - KNOWN_UNPROPAGATED_UPRATING


@pytest.mark.parametrize("children, expected", [("1", 1108.58), ("2", 1900.42)])
def test_uc_childcare_caps_rise_by_september_cpi_in_april_2027(children, expected):
    cap = system.parameters.gov.dwp.universal_credit.elements.childcare.cap
    assert cap.children[children]("2027-04-30") == pytest.approx(expected, abs=0.005)


def test_every_parameter_on_the_index_rises_by_september_cpi_after_its_last_value():
    """After its last published value, each parameter uprated by the index
    rises by the April rise: 0% in April 2016, 3.5% in April 2027,
    and 3.4% in April 2028, with any configured benefit-specific rounding."""
    parameters = system.parameters
    # The processed tree, including its baseline copy, is uprated, so read
    # the YAML files for the last published dates.
    raw = load_parameter_file(str(COUNTRY_DIR / "parameters"), name="")
    checked = 0
    for parameter in uprated_by_the_index(parameters.gov):
        last_year = last_published_year(raw, parameter.name)
        years = range(max(last_year + 1, 2016), LAST_INDEX_YEAR + 1)
        for year in years:
            before = parameter(f"{year - 1}-04-30")
            after = parameter(f"{year}-04-30")
            if not before:
                continue
            uprating = parameter.metadata.get("uprating")
            rounding = uprating.get("rounding") if isinstance(uprating, dict) else None
            if rounding:
                # Scottish benefits round each annual increase to the nearest
                # 5p. Check the rounded amount rather than an exact growth rate.
                assert rounding["type"] == "nearest"
                interval = rounding["interval"]
                index = parameters.gov.benefit_uprating_cpi
                factor = index(f"{year}-04-30") / index(f"{year - 1}-04-30")
                expected = round(before * factor / interval) * interval
                assert after == pytest.approx(expected, abs=PENNY_TENTH), (
                    parameter.name,
                    year,
                )
            else:
                assert after / before - 1 == pytest.approx(
                    rise(parameters, year), abs=2e-5
                ), (parameter.name, year)
        checked += len(years) > 0
    assert checked >= 50


# Parameters with a start_instant before their last value that an open pull
# request fixes. Add an entry only with that pull request's number.
KNOWN_EARLIER_START = set()


def test_no_parameter_projects_from_an_earlier_start():
    """An uprating start_instant before the last value makes policyengine-core
    project from the start value, not the last published one, which put a
    12% jump into April 2027 for constant attendance allowance and the
    disability premiums."""
    raw = load_parameter_file(str(COUNTRY_DIR / "parameters"), name="")
    offenders = []
    for parameter in system.parameters.gov.get_descendants():
        if not isinstance(parameter, Parameter):
            continue
        uprating = (parameter.metadata or {}).get("uprating")
        if not (isinstance(uprating, dict) and "start_instant" in uprating):
            continue
        last = max(
            value.instant_str for value in raw.get_child(parameter.name).values_list
        )
        if str(uprating["start_instant"]) < last:
            offenders.append(parameter.name)
    assert set(offenders) <= KNOWN_EARLIER_START, offenders


LAGGED_CPI = "gov.economic_assumptions.indices.obr.lagged_cpi"


def test_hb_non_dependant_income_bands_keep_lagged_cpi_while_deductions_use_september():
    parameters = system.parameters
    amounts = parameters.gov.dwp.housing_benefit.non_dep_deduction.amount
    index = parameters.gov.economic_assumptions.indices.obr.lagged_cpi
    lagged_factor = index("2027-04-30") / index("2026-04-30")
    for bracket in amounts.brackets:
        assert uprating_parameter(bracket.threshold) == LAGGED_CPI
        assert uprating_parameter(bracket.amount) == INDEX
        assert bracket.threshold("2027-04-30") == pytest.approx(
            bracket.threshold("2026-04-30") * lagged_factor, abs=PENNY_TENTH
        )
        assert bracket.amount("2027-04-30") == pytest.approx(
            bracket.amount("2026-04-30") * 1.035, abs=PENNY_TENTH
        )


def test_amounts_not_raised_by_september_cpi_keep_their_lagged_calendar_projection():
    """Amounts that were on gov.benefit_uprating_cpi but are not raised by
    September CPI, including DfE funding rates and HB non-dependant income
    bands, still rise by the previous calendar year's CPI after their last
    value. Pension Credit amounts and pension-age HB allowances have their
    own projections."""
    parameters = system.parameters
    raw = load_parameter_file(str(COUNTRY_DIR / "parameters"), name="")
    calendar_cpi = (
        parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index
    )
    names = []
    for parameter in parameters.gov.get_descendants():
        if not isinstance(parameter, Parameter):
            continue
        if uprating_parameter(parameter) != LAGGED_CPI:
            continue
        names.append(parameter.name)
        last_year = last_published_year(raw, parameter.name)
        for year in range(max(last_year + 1, 2016), LAST_INDEX_YEAR + 1):
            before = parameter(f"{year - 1}-04-30")
            after = parameter(f"{year}-04-30")
            if not before:
                continue
            assert after / before - 1 == pytest.approx(
                calendar_cpi(f"{year - 1}-01-01"), abs=2e-5
            ), (parameter.name, year)
    assert names
    assert any(name.startswith("gov.dfe.childcare_funding_rate") for name in names)
    assert not any(name.startswith("gov.dwp.pension_credit.") for name in names)
    assert not any(
        name.startswith("gov.dwp.housing_benefit.allowances.") for name in names
    )


def test_the_triple_lock_reads_the_same_september_cpi():
    """The State Pension's CPI element and the benefit rise read the same
    September CPI parameter through the same rounding, so they must agree
    every year; this pins the year each reads (a one-year shift fails)."""
    parameters = system.parameters
    for year, inputs in read_uprating_years(parameters).items():
        assert max(inputs.cpi, 0.0) == rise(parameters, year), year


def test_scenario_setting_september_cpi_moves_the_next_april():
    parameters = parameters_under(
        {f"{INPUTS}.cpi_september": {"year:2026-09-01:1": 0.05}}
    )
    assert rise(parameters, 2027) == 0.05
    assert carers_allowance(parameters, 2027) == pytest.approx(
        86.45 * 1.05, abs=PENNY_TENTH
    )
    # Only that April moves.
    assert rise(parameters, 2028) == rise(system.parameters, 2028)
    assert carers_allowance(parameters, 2026) == 86.45


def test_scenario_on_calendar_cpi_moves_the_forecast_with_the_obr_gap():
    """Calendar-year CPI for 2027 moves the September 2027 forecast one for
    one (keeping the OBR's +0.02pp gap), and so the April 2028 rise."""
    parameters = parameters_under(
        {f"{OBR}.consumer_price_index": {"year:2027-01-01:1": 0.04}}
    )
    assert rise(parameters, 2028) == 0.040
    assert carers_allowance(parameters, 2028) == pytest.approx(
        carers_allowance(parameters, 2027) * 1.040, abs=PENNY_TENTH
    )


def test_falling_prices_hold_benefits():
    parameters = parameters_under(
        {f"{INPUTS}.cpi_september": {"year:2026-09-01:1": -0.01}}
    )
    assert rise(parameters, 2027) == 0
    assert carers_allowance(parameters, 2027) == pytest.approx(86.45, abs=PENNY_TENTH)


def test_carers_allowance_projection():
    """£86.45 a week from April 2026, then the September CPI rises: 3.5% in
    April 2027 (September 2026 CPI)."""
    parameters = system.parameters
    assert carers_allowance(parameters, 2026) == 86.45
    assert carers_allowance(parameters, 2027) == pytest.approx(
        86.45 * 1.035, abs=PENNY_TENTH
    )
    assert carers_allowance(parameters, 2028) == pytest.approx(
        86.45 * 1.035 * (1 + rise(parameters, 2028)), abs=PENNY_TENTH
    )


def test_uc_standard_allowance_follows_september_cpi_and_the_act_uplift():
    """Universal Credit Act 2025 s1: the 2026-27 amount (£424.90, single 25
    or over) rises by September 2026 CPI (3.5%) and by the change in the
    uplift (2.3% to 3.1%) in April 2027."""
    amount = system.parameters.gov.dwp.universal_credit.standard_allowance.amount
    assert amount.SINGLE_OLD("2027-04-30") == pytest.approx(
        424.90 * 1.035 * 1.031 / 1.023, rel=1e-5
    )

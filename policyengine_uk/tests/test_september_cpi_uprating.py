"""The September CPI benefit uprating in the full parameter tree.

Most benefits rise each April by the previous September's CPI 12-month rate
(Social Security Administration Act 1992 s150; written statement HCWS1101).
These tests check the April rise against September CPI, that every
parameter uprated by ``gov.benefit_uprating_cpi`` follows it after its last
published value, that the State Pension triple lock reads the same September
figure, and that scenarios on the inputs move benefit rates.
"""

import pytest
from policyengine_core.parameters import Parameter, load_parameter_file

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
}


def test_published_september_rates_give_the_april_rises():
    for year, published in PUBLISHED_APRIL_RISES.items():
        assert rise(system.parameters, year) == published, year


def test_april_2027_rise_is_the_obr_september_2026_forecast():
    """OBR March 2026 EFO, receipts Table 3.19: 2.1157% for September 2026,
    applied as the published 2.1%."""
    assert rise(system.parameters, 2027) == 0.021


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


def test_every_parameter_on_the_index_rises_by_september_cpi_after_its_last_value():
    """After its last published value, each parameter uprated by the index
    rises by exactly the April rise: 0% in April 2016, 2.1% in April 2027."""
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
            assert after / before - 1 == pytest.approx(
                rise(parameters, year), abs=2e-5
            ), (parameter.name, year)
        checked += len(years) > 0
    assert checked >= 50


def test_no_benefit_parameter_projects_from_an_earlier_start():
    """An uprating start_instant before the last value makes policyengine-core
    project from the start value, not the last published one, which put a
    12% jump into April 2027 for constant attendance allowance and the
    disability premiums."""
    for parameter in uprated_by_the_index(system.parameters.gov):
        uprating = parameter.metadata["uprating"]
        assert not (isinstance(uprating, dict) and "start_instant" in uprating), (
            parameter.name
        )


def test_personal_allowance_is_indexed_by_september_cpi_after_the_freeze():
    """Income Tax Act 2007 s57: £12,570 to April 2030, then September CPI."""
    parameters = system.parameters
    allowance = parameters.gov.hmrc.income_tax.allowances.personal_allowance.amount
    assert allowance("2030-04-30") == 12_570
    assert allowance("2031-04-30") == pytest.approx(
        12_570 * (1 + rise(parameters, 2031)), rel=1e-5
    )


LAGGED_CPI = "gov.economic_assumptions.indices.obr.lagged_cpi"


def test_amounts_outside_the_review_keep_their_lagged_calendar_cpi_projection():
    """Amounts that were on gov.benefit_uprating_cpi but are not raised by
    September CPI (the Pension Credit standard minimum guarantee, the Housing
    Benefit earnings disregards, DfE funding rates and others) still rise
    by the previous calendar year's CPI after their last value."""
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
    assert "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE" in names
    assert "gov.dwp.housing_benefit.means_test.income_disregard.single" in names


def test_the_triple_lock_reads_the_same_september_cpi():
    """Two consumers of one statistic: the State Pension's CPI element and
    the benefit rise must be the same rounded September figure."""
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
    """Calendar-year CPI for 2026 moves the September 2026 forecast one for
    one (keeping the OBR's -0.184pp gap), and so the April 2027 rise."""
    parameters = parameters_under(
        {f"{OBR}.consumer_price_index": {"year:2026-01-01:1": 0.04}}
    )
    assert rise(parameters, 2027) == 0.038
    assert carers_allowance(parameters, 2027) == pytest.approx(
        86.45 * 1.038, abs=PENNY_TENTH
    )


def test_falling_prices_hold_benefits():
    parameters = parameters_under(
        {f"{INPUTS}.cpi_september": {"year:2026-09-01:1": -0.01}}
    )
    assert rise(parameters, 2027) == 0
    assert carers_allowance(parameters, 2027) == pytest.approx(86.45, abs=PENNY_TENTH)


def test_carers_allowance_projection():
    """£86.45 a week from April 2026, then the September CPI rises."""
    parameters = system.parameters
    assert carers_allowance(parameters, 2026) == 86.45
    assert carers_allowance(parameters, 2027) == pytest.approx(
        86.45 * 1.021, abs=PENNY_TENTH
    )
    assert carers_allowance(parameters, 2028) == pytest.approx(
        86.45 * 1.021 * (1 + rise(parameters, 2028)), abs=PENNY_TENTH
    )

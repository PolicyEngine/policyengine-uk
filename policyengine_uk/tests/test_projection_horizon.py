"""How far a single-year dataset is projected, and what serves later years.

A single-year dataset is projected to ``PROJECTION_END_YEAR``: each year up to
it is a dataset year. Most indexed inputs grow from the year before; residential
stocks use the original observation and cumulative house-price index at the
model's storage precision. After it, policyengine-core serves each input from the last
projected year: a variable with a formula is calculated by it, one with an
``uprating`` attribute is scaled by that index, and any other is held at its
last projected value. Rent and council tax have no ``uprating`` attribute, so
while the projection stopped at 2030 they stopped growing after it while
earnings and weights kept growing, and the Enhanced FRS's recorded Pension
Credit capital gave way to its formula.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data import economic_assumptions
from policyengine_uk.data.economic_assumptions import (
    COUNTRY_UPRATED_INPUTS,
    DATASET_UPRATING_EXCLUSIONS,
    LEGACY_PROJECTION_END_YEAR,
    PROJECTION_END_YEAR,
    extend_single_year_dataset,
    reset_growthfactor_uprating,
)
from policyengine_uk.system import system

BASE_YEAR = 2024
GROWTH = parameters.gov.economic_assumptions.yoy_growth
UPRATING_INDICES = yaml.safe_load(
    (Path(economic_assumptions.__file__).parent / "uprating_indices.yaml").read_text()
)
# Each variable the projection grows by a single index, with that index, for
# the variables the model defines. Variables listed for an index that the
# model no longer defines are left out.
INDEX_OF = {
    variable: index
    for index, variables in UPRATING_INDICES.items()
    for variable in variables
    if variable in system.variables
}
FALLBACK_INDEX_OF = {
    name: variable.uprating
    for name, variable in system.variables.items()
    if variable.uprating is not None
    and variable.value_type in (int, float)
    and name not in INDEX_OF
    and name not in DATASET_UPRATING_EXCLUSIONS
    and name not in COUNTRY_UPRATED_INPUTS
}
# These survey inputs already use FY2026-27 prices, so projection must not
# apply their class-level CPI index a second time.
ENERGY_VARIABLES = (
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
)
TABLES = {"person": "person", "benunit": "benunit", "household": "household"}
# One household per tenure and region pair that the rent and council tax
# uprating distinguish: private renters, social renters and owners, in a
# region of each country.
HOUSEHOLDS = [
    ("LONDON", "RENT_PRIVATELY"),
    ("NORTH_EAST", "RENT_FROM_COUNCIL"),
    ("SCOTLAND", "RENT_PRIVATELY"),
    ("WALES", "RENT_FROM_HA"),
    ("NORTHERN_IRELAND", "OWNED_WITH_MORTGAGE"),
]
COUNCIL_TAX_SERIES = {
    "LONDON": "england",
    "NORTH_EAST": "england",
    "SCOTLAND": "scotland",
    "WALES": "wales",
}
# Water and sewerage charges grow by country (#2501): Northern Ireland has
# none to grow.
WATER_SERIES = {
    "LONDON": "ofwat.water_bills",
    "NORTH_EAST": "ofwat.water_bills",
    "SCOTLAND": "scottish_water.water_bills",
    "WALES": "ofwat.water_bills",
}


def _dataset(amount=1_000.0, base_year=BASE_YEAR):
    """One person per household, with every indexed input and excluded energy
    input set to ``amount`` (or one amount per household), plus rent and
    council tax.

    Recorded Pension Credit capital is twice the benefit unit's recorded
    capital, which its formula reads, so the two tell apart a stored value
    from a calculated one."""
    n = len(HOUSEHOLDS)
    ids = np.arange(1, n + 1)
    amounts = np.broadcast_to(np.asarray(amount, dtype=float), (n,)).copy()
    tables = {
        "person": {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": 40,
        },
        "benunit": {
            "benunit_id": ids,
            "pension_credit_reported_capital": 2 * amounts,
        },
        "household": {
            "household_id": ids,
            "household_weight": amounts,
            "region": [region for region, _ in HOUSEHOLDS],
            "tenure_type": [tenure for _, tenure in HOUSEHOLDS],
            "rent": amounts,
            "council_tax": amounts,
            "water_and_sewerage_charges": amounts,
        },
    }
    for variable in (*INDEX_OF, *FALLBACK_INDEX_OF, *ENERGY_VARIABLES):
        entity = system.variables[variable].entity.key
        tables[TABLES[entity]].setdefault(variable, amounts)
    return UKSingleYearDataset(
        person=pd.DataFrame(tables["person"]),
        benunit=pd.DataFrame(tables["benunit"]),
        household=pd.DataFrame(tables["household"]),
        fiscal_year=base_year,
    )


def _table(dataset, variable):
    entity = system.variables[variable].entity.key
    return getattr(dataset, TABLES[entity])


def _rent_growth(region, tenure, year):
    if tenure == "RENT_PRIVATELY":
        return GROWTH.ons.private_rental_prices(year)[region]
    return GROWTH.obr.social_rent(year)


def _council_tax_growth(region, year):
    # Bills grow by their country's receipts growth net of the growth in
    # household weights, so each country's total tracks its receipts (#2067).
    series = COUNCIL_TAX_SERIES.get(region)
    if series is None:
        return 0.0
    receipts = GROWTH.obr.council_tax.get_child(series)(year)
    weights = parameters.get_child(INDEX_OF["household_weight"])(year)
    return (1 + receipts) / (1 + weights) - 1


RESIDENTIAL_STOCKS = (
    "main_residence_value",
    "other_residential_property_value",
)


def _residential_stock_level(observed, variable, year):
    """Independent level oracle from the original observation and explicit HPI."""
    hpi = parameters.get_child("gov.economic_assumptions.indices.obr.house_prices")
    observed = np.asarray(observed, dtype=system.variables[variable].dtype)
    return observed * (hpi(year) / hpi(BASE_YEAR))


@pytest.fixture(scope="module")
def projected():
    return extend_single_year_dataset(_dataset(), parameters)


@pytest.fixture
def sim():
    return Microsimulation(dataset=_dataset())


def test_projection_reaches_fiscal_year_2032_33():
    # Year 2031 is fiscal year 2031-32, the last year of a forecast made in
    # 2026-27, and 2032 the year after.
    assert PROJECTION_END_YEAR >= 2032


def test_every_year_to_the_horizon_is_a_dataset_year(projected, sim):
    years = list(range(BASE_YEAR, PROJECTION_END_YEAR + 1))
    assert [int(year) for year in projected.years] == years
    assert [int(year) for year in sim.dataset.years] == years


def test_each_singly_indexed_input_grows_by_its_index_every_year(projected):
    """For every variable uprating_indices.yaml lists and every projected
    year, check its index: residential stocks use the original observation
    and cumulative HPI. This fixture stores the completed bereavement split,
    so BSP stays flat; other inputs grow from the previous year's raw YoY."""
    observed = _dataset()
    for year in range(BASE_YEAR + 1, PROJECTION_END_YEAR + 1):
        for variable, index in INDEX_OF.items():
            current = _table(projected[year], variable)[variable].to_numpy()
            if variable in RESIDENTIAL_STOCKS:
                original = _table(observed, variable)[variable].to_numpy()
                expected = _residential_stock_level(original, variable, year)
            else:
                previous = _table(projected[year - 1], variable)[variable].to_numpy()
                growth = parameters.get_child(index)(year)
                expected = (
                    previous if variable == "bsp_reported" else previous * (1 + growth)
                )
            assert current == pytest.approx(expected), (variable, year)


def test_unmapped_inputs_preserve_legacy_years_and_grow_after_2030(projected):
    """Previously unmapped columns keep their old values through 2030, then
    grow by the same cumulative-index ratio Core used beyond that year.
    Columns uprating_indices.yaml now lists (the debts, ISAs, lodger and
    boarder rent, gross receipts, salary sacrifice, service charges and rail
    usage), and water bills, which grow by country, grow every year instead,
    so they are no longer fallbacks.
    """
    assert "employee_pension_contributions_reported" in FALLBACK_INDEX_OF
    assert "rail_usage" not in FALLBACK_INDEX_OF
    for year in range(BASE_YEAR + 1, PROJECTION_END_YEAR + 1):
        for variable, index_name in FALLBACK_INDEX_OF.items():
            previous = _table(projected[year - 1], variable)[variable].to_numpy()
            current = _table(projected[year], variable)[variable].to_numpy()
            index = parameters.get_child(index_name)
            factor = (
                index(year) / index(year - 1)
                if year > LEGACY_PROJECTION_END_YEAR
                else 1
            )
            assert current == pytest.approx(previous * factor), (variable, year)


def test_dataset_energy_prices_are_not_uprated_twice(projected):
    for year in range(BASE_YEAR + 1, PROJECTION_END_YEAR + 1):
        for variable in ENERGY_VARIABLES:
            base = _table(projected[BASE_YEAR], variable)[variable].to_numpy()
            current = _table(projected[year], variable)[variable].to_numpy()
            np.testing.assert_array_equal(current, base, err_msg=f"{variable}, {year}")


def test_reset_growthfactor_uprating_restores_unmapped_inputs(projected):
    reset = projected.copy()
    reset_growthfactor_uprating(reset)
    for year in range(BASE_YEAR + 1, PROJECTION_END_YEAR + 1):
        for variable in (*INDEX_OF, *FALLBACK_INDEX_OF, *COUNTRY_UPRATED_INPUTS):
            base = _table(projected[BASE_YEAR], variable)[variable].to_numpy()
            current = _table(reset[year], variable)[variable].to_numpy()
            np.testing.assert_array_equal(current, base, err_msg=f"{variable}, {year}")


def test_water_charges_grow_by_country_every_projected_year(projected):
    # Through the old horizon and after it, each country's own series grows
    # the charge once a year; Northern Ireland's stays flat.
    for year in range(BASE_YEAR + 1, PROJECTION_END_YEAR + 1):
        previous, current = projected[year - 1].household, projected[year].household
        for i, (region, _) in enumerate(HOUSEHOLDS):
            series = WATER_SERIES.get(region)
            growth = 0.0 if series is None else GROWTH.get_child(series)(year)
            assert current["water_and_sewerage_charges"].iloc[i] == pytest.approx(
                previous["water_and_sewerage_charges"].iloc[i] * (1 + growth)
            ), (region, year)


def test_rent_and_council_tax_grow_every_projected_year(projected):
    for year in range(BASE_YEAR + 1, PROJECTION_END_YEAR + 1):
        previous, current = projected[year - 1].household, projected[year].household
        for i, (region, tenure) in enumerate(HOUSEHOLDS):
            assert current["rent"].iloc[i] == pytest.approx(
                previous["rent"].iloc[i] * (1 + _rent_growth(region, tenure, year))
            )
            assert current["council_tax"].iloc[i] == pytest.approx(
                previous["council_tax"].iloc[i]
                * (1 + _council_tax_growth(region, year))
            )
    # The years the projection used to stop short of: rent, and council tax
    # outside Northern Ireland, still grow.
    outside_ni = np.array([region != "NORTHERN_IRELAND" for region, _ in HOUSEHOLDS])
    for year in (2031, 2032):
        previous, current = projected[year - 1].household, projected[year].household
        assert (current["rent"].to_numpy() > previous["rent"].to_numpy()).all()
        assert (
            current["council_tax"].to_numpy()[outside_ni]
            > previous["council_tax"].to_numpy()[outside_ni]
        ).all()


@settings(max_examples=10, deadline=None, derandomize=True)
@given(
    amounts=st.lists(
        st.floats(1, 1e6, allow_nan=False),
        min_size=len(HOUSEHOLDS),
        max_size=len(HOUSEHOLDS),
    ),
    year=st.integers(BASE_YEAR + 1, PROJECTION_END_YEAR),
    variable=st.sampled_from(sorted(INDEX_OF)),
)
def test_growth_ratio_is_one_plus_the_index(amounts, year, variable):
    """For any positive amounts, any projected year and any singly indexed
    variable, check its annual growth record by record. Residential ratios
    come from original-observation cumulative HPI levels at storage precision;
    split BSP stays flat; every other variable retains its raw one-plus-YoY
    growth expectation."""
    projected = extend_single_year_dataset(
        _dataset(np.array(amounts)), parameters, end_year=year
    )
    current = _table(projected[year], variable)[variable].to_numpy()
    previous = _table(projected[year - 1], variable)[variable].to_numpy()
    ratio = current / previous
    if variable in RESIDENTIAL_STOCKS:
        expected_current = _residential_stock_level(amounts, variable, year)
        expected_previous = _residential_stock_level(amounts, variable, year - 1)
        assert current == pytest.approx(expected_current)
        assert previous == pytest.approx(expected_previous)
        expected_ratio = expected_current / expected_previous
    elif variable == "bsp_reported":
        expected_ratio = np.ones(len(amounts))
    else:
        index = parameters.get_child(INDEX_OF[variable])(year)
        expected_ratio = np.full(len(amounts), 1 + index)
    assert ratio == pytest.approx(expected_ratio)


@settings(max_examples=10, deadline=None, derandomize=True)
@given(
    amounts=st.lists(
        st.floats(1, 1e6, allow_nan=False),
        min_size=len(HOUSEHOLDS),
        max_size=len(HOUSEHOLDS),
    ),
    year=st.integers(LEGACY_PROJECTION_END_YEAR + 1, PROJECTION_END_YEAR),
    variable=st.sampled_from(sorted(FALLBACK_INDEX_OF)),
)
def test_unmapped_growth_ratio_equals_its_cumulative_index(amounts, year, variable):
    projected = extend_single_year_dataset(
        _dataset(np.array(amounts)), parameters, end_year=year
    )
    ratio = (
        _table(projected[year], variable)[variable].to_numpy()
        / _table(projected[year - 1], variable)[variable].to_numpy()
    )
    index = parameters.get_child(FALLBACK_INDEX_OF[variable])
    assert ratio == pytest.approx(np.full(len(amounts), index(year) / index(year - 1)))


def test_simulation_serves_projected_values_to_the_horizon(sim, projected):
    # The simulation stores the dataset's employment_income as
    # employment_income_before_lsr. Rent and council tax have no uprating
    # attribute, and recorded Pension Credit capital has a formula, so only
    # the projection grows them.
    for year in range(BASE_YEAR, PROJECTION_END_YEAR + 1):
        for stored, variable in (
            ("employment_income_before_lsr", "employment_income"),
            ("rent", "rent"),
            ("council_tax", "council_tax"),
            ("state_pension_reported", "state_pension_reported"),
            ("pension_credit_reported_capital", "pension_credit_reported_capital"),
        ):
            assert sim.calculate(stored, year).values == pytest.approx(
                _table(projected[year], variable)[variable].to_numpy()
            ), (variable, year)


def test_a_year_past_the_horizon_is_served_from_the_last_projected_year(sim):
    """After the horizon a stored input with a formula is calculated by it,
    one with an uprating attribute is scaled by that index from the last
    projected year, and any other is held at its last projected value."""
    last, after = PROJECTION_END_YEAR, PROJECTION_END_YEAR + 1
    # The formula reads benunit_reported_capital, uprated from the last
    # projected year, in place of the stored value, which was twice it.
    assert system.variables["pension_credit_reported_capital"].formulas
    assert sim.calculate("pension_credit_reported_capital", after).values == (
        pytest.approx(sim.calculate("benunit_reported_capital", after).values)
    )
    assert sim.calculate("pension_credit_reported_capital", last).values == (
        pytest.approx(2 * sim.calculate("benunit_reported_capital", last).values)
    )
    for variable in (
        "employment_income_before_lsr",
        "self_employment_income",
        "benunit_reported_capital",
        "household_weight",
    ):
        index = parameters.get_child(system.variables[variable].uprating)
        assert sim.calculate(variable, after).values == pytest.approx(
            sim.calculate(variable, last).values * index(after) / index(last)
        ), variable
    for variable in ("rent", "council_tax", "state_pension_reported"):
        assert system.variables[variable].uprating is None
        assert sim.calculate(variable, after).values == pytest.approx(
            sim.calculate(variable, last).values
        )


def test_legacy_reported_capital_expires_only_after_the_horizon(projected):
    """Legacy survey files store programme capital without the shared input.

    Projection preserves that observation through the supported horizon.
    Afterward the programme formula uses the absent shared input's sentinel,
    matching direct-situation semantics rather than carrying the observation.
    """
    dataset = _dataset()
    dataset.benunit = dataset.benunit.drop(columns="benunit_reported_capital")
    simulation = Microsimulation(dataset=dataset)
    for year in (2030, 2031, 2032):
        assert simulation.calculate("pension_credit_reported_capital", year).values == (
            pytest.approx(projected[year].benunit["pension_credit_reported_capital"])
        )
    assert simulation.calculate(
        "pension_credit_reported_capital", PROJECTION_END_YEAR + 1
    ).values == pytest.approx(np.full(len(HOUSEHOLDS), -1))


def test_tax_free_savings_formula_takes_over_after_the_horizon():
    """The survey exemption is stored until the horizon, then ISA interest
    supplies it. Legacy files with no ISA-interest input therefore get zero.
    """
    dataset = _dataset()
    dataset.person["tax_free_savings_income"] = 1_000.0
    # Enhanced FRS 2024-25 does not store the formula's ISA-interest source.
    simulation = Microsimulation(dataset=dataset)
    assert simulation.calculate(
        "tax_free_savings_income", PROJECTION_END_YEAR
    ).values == (pytest.approx(np.full(len(HOUSEHOLDS), 1_000)))
    assert simulation.calculate(
        "tax_free_savings_income", PROJECTION_END_YEAR + 1
    ).values == pytest.approx(np.zeros(len(HOUSEHOLDS)))

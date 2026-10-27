"""Synthetic accounting and projection contracts for the WAS property components.

WAS has seven gross terms, but second homes and buy-to-let are saved together
by policyengine-uk-data. These tests exercise that six-input model contract;
licensed-source reconciliation and release persistence belong to the data repo.
The formula properties use fresh Core simulation holders with one shared
model; uprating, datasets, monthly stocks, LVT and purchases exercise the UK
simulation wrapper separately.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from hypothesis import example, given, settings
from hypothesis import strategies as st
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

BASE_YEAR = 2024
GDP_INDEX = "gov.economic_assumptions.indices.obr.per_capita.gdp"
GDP_GROWTH = "gov.economic_assumptions.yoy_growth.obr.per_capita.gdp"
PROPERTY_INPUTS = (
    "main_residence_value",
    "other_residential_property_value",
    "non_residential_property_value",
    "owned_land",
    "overseas_property_value",
    "other_property_value",
)
OTHER_WEALTH_INPUTS = ("corporate_wealth", "private_pension_wealth", "savings")
CAPITAL_PATHS = (
    "gov.dwp.universal_credit.means_test.capital",
    "gov.dwp.housing_benefit.means_test.capital",
    "gov.dwp.income_support.means_test.capital",
    "gov.dwp.JSA.income.capital",
    "gov.dwp.ESA.income.capital",
    "gov.dwp.pension_credit.income.capital",
)
SOURCE_INPUTS = (
    ("main_residence", "main_residence_value"),
    ("second_homes", "other_residential_property_value"),
    ("buy_to_let", "other_residential_property_value"),
    ("other_uk_buildings", "non_residential_property_value"),
    ("uk_land", "owned_land"),
    ("overseas_land_and_property", "overseas_property_value"),
    ("other_real_estate", "other_property_value"),
)
REGIONS = (
    "LONDON",
    "SOUTH_EAST",
    "EAST_OF_ENGLAND",
    "SOUTH_WEST",
    "WEST_MIDLANDS",
    "EAST_MIDLANDS",
    "NORTH_WEST",
    "YORKSHIRE",
    "SCOTLAND",
    "WALES",
    "NORTH_EAST",
    "NORTHERN_IRELAND",
    "UNKNOWN",
)
PROPERTY_SETTINGS = settings(max_examples=15, deadline=None, derandomize=True)
# Finite non-negative stocks at float32 precision, as held by the model.
MONEY = st.floats(
    min_value=0,
    max_value=10_000_000,
    allow_nan=False,
    allow_infinity=False,
    width=32,
)
COMPONENT_VALUES = dict(
    zip(PROPERTY_INPUTS, (60_000, 25_000, 15_000, 20_000, 30_000, 0))
)


@pytest.fixture(scope="module")
def _property_metadata_system(cloned_uk_tax_benefit_system):
    # The dependency installs the clone factory before this read-only fixture.
    import policyengine_uk.simulation as simulation_module

    return simulation_module.CountryTaxBenefitSystem()


def _saved_components(source_values):
    """The upstream release contract combines second homes and buy-to-let."""
    components = dict.fromkeys(PROPERTY_INPUTS, 0.0)
    for source, variable in SOURCE_INPUTS:
        components[variable] += source_values.get(source, 0.0)
    return components


def _situation(assets, region="LONDON"):
    return {
        "people": {"person": {"age": {BASE_YEAR: 40}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "region": {BASE_YEAR: region},
                **{variable: {BASE_YEAR: value} for variable, value in assets.items()},
            }
        },
    }


def _simulation(assets, *, region="LONDON", reform=None):
    return Simulation(situation=_situation(assets, region), reform=reform)


@pytest.fixture(scope="module")
def _formula_simulation(_property_metadata_system):
    """Fresh holders per example; unchanged production formula definitions."""

    def build(assets, *, region="LONDON"):
        return CoreSimulation(
            tax_benefit_system=_property_metadata_system,
            situation=_situation(assets, region),
        )

    return build


def _value(simulation, variable, period=BASE_YEAR):
    return float(simulation.calculate(variable, period)[0])


def _property_sum(simulation, period=BASE_YEAR):
    return sum(_value(simulation, variable, period) for variable in PROPERTY_INPUTS)


def _component_dataset(components, *, stored_total=None):
    """Use the actual single-year loader and its YAML uprating registrations."""
    household = {
        "household_id": [1],
        "region": ["LONDON"],
        "tenure_type": ["OWNED_OUTRIGHT"],
        "council_tax": [0.0],
        "rent": [0.0],
        **{variable: [float(value)] for variable, value in components.items()},
    }
    if stored_total is not None:
        household["property_wealth"] = [stored_total]
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(household),
        fiscal_year=BASE_YEAR,
    )


@pytest.mark.parametrize(
    "variable", ["overseas_property_value", "other_property_value"]
)
def test_new_property_inputs_register_gdp_uprating_for_situations_and_datasets(
    variable, _property_metadata_system
):
    model_variable = _property_metadata_system.variables[variable]
    assert model_variable.uprating == GDP_INDEX
    assert model_variable.entity.key == "household"
    assert model_variable.default_value == 0
    registrations_path = Path(__file__).parents[1] / "data" / "uprating_indices.yaml"
    registrations = yaml.safe_load(registrations_path.read_text())
    assert registrations[GDP_GROWTH].count(variable) == 1
    assert sum(names.count(variable) for names in registrations.values()) == 1


@pytest.mark.parametrize("capital_path", CAPITAL_PATHS)
@pytest.mark.parametrize("year", [2024, 2026])
def test_property_capital_lists_preserve_each_source_once(
    capital_path, year, _property_metadata_system
):
    parameters = _property_metadata_system.parameters
    sources = list(parameters.get_child(f"{capital_path}.sources")(year))
    sale_sources = list(
        parameters.get_child(f"{capital_path}.sale_expenses.sources")(year)
    )
    for names in (sources, sale_sources):
        for variable in ("overseas_property_value", "other_property_value"):
            assert names.count(variable) == (
                0 if "universal_credit" in capital_path else 1
            )
        assert "main_residence_value" not in names
        assert "private_pension_wealth" not in names
        assert names.count("share_like_capital") == 1
        assert "corporate_wealth" not in names
        assert "buy_to_let_value" not in names
    # Preserve UC's existing omission; the aggregate change does not decide it.
    if "universal_credit" in capital_path:
        assert "owned_land" not in sources
        property_sources = list(
            parameters.get_child(f"{capital_path}.property_sources")(year)
        )
        for variable in ("uc_overseas_property_capital", "uc_other_property_capital"):
            assert property_sources.count(variable) == 1
    else:
        assert sources.count("owned_land") == 1


@pytest.mark.parametrize(
    "variable", ["overseas_property_value", "other_property_value"]
)
@PROPERTY_SETTINGS
@given(
    property_pence=st.integers(min_value=0, max_value=2_000_000),
    report_pence=st.integers(min_value=0, max_value=2_000_000),
    holding_pence=st.integers(min_value=0, max_value=2_000_000),
)
@example(property_pence=2_000_000, report_pence=0, holding_pence=0)
def test_financial_reports_preserve_separately_valued_property(
    _property_metadata_system, variable, property_pence, report_pence, holding_pence
):
    # The only financial proxy is an entirely disregarded company holding.
    # A financial-only report adds to the same independently valued property,
    # net of that holding, even when the report is zero.
    holding = holding_pence / 100
    situation = _situation(
        {variable: property_pence / 100, "corporate_wealth": holding}
    )
    situation["people"]["person"]["uc_company_holding_disregard"] = {BASE_YEAR: holding}
    unreported = CoreSimulation(
        tax_benefit_system=_property_metadata_system, situation=situation
    )
    baseline = _value(unreported, "uc_assessable_capital")
    property_capital = _value(unreported, "uc_property_capital")
    report = report_pence / 100
    situation["benunits"]["benunit"]["benunit_reported_capital"] = {BASE_YEAR: report}
    reported = CoreSimulation(
        tax_benefit_system=_property_metadata_system, situation=situation
    )
    counted = _value(reported, "uc_assessable_capital")

    assert counted >= baseline
    assert baseline == property_capital
    assert _value(reported, "uc_property_capital") == property_capital
    # Recover the penny from float32 storage before adding the observed report;
    # compare the exact value after the final float32 holder conversion.
    net_report = max(0, report - holding)
    assert counted == float(
        np.float32(round(net_report + round(property_capital, 2), 2))
    )


@pytest.mark.parametrize("source,variable", SOURCE_INPUTS)
def test_each_was_source_enters_gross_and_total_property_once(source, variable):
    components = _saved_components({source: 100_000})
    sim = _simulation(components)

    assert _value(sim, variable) == 100_000
    assert _value(sim, "property_wealth") == 100_000
    assert _value(sim, "total_wealth") == 100_000
    residential = 100_000 if variable in PROPERTY_INPUTS[:2] else 0
    assert _value(sim, "residential_property_value") == residential


def test_seven_source_terms_reconcile_to_six_saved_components():
    # This is a synthetic mapping contract, not reconciliation of licensed WAS.
    source_values = dict(zip((source for source, _ in SOURCE_INPUTS), range(1, 8)))
    components = _saved_components(source_values)
    sim = _simulation(components)

    assert len(components) == 6
    assert components["other_residential_property_value"] == 2 + 3
    assert _value(sim, "residential_property_value") == 1 + 2 + 3
    assert _value(sim, "property_wealth") == sum(source_values.values())
    assert _value(sim, "total_wealth") == sum(source_values.values())


def test_london_mixed_property_has_150000_gross_and_105000_uk_land():
    sim = _simulation(COMPONENT_VALUES)

    assert _value(sim, "property_wealth") == 150_000
    assert _value(sim, "total_wealth") == 150_000
    assert _value(sim, "household_land_value") == 105_000


@PROPERTY_SETTINGS
@given(st.tuples(*(MONEY for _ in PROPERTY_INPUTS)))
@example((60_000, 25_000, 15_000, 20_000, 30_000, 40_000))
def test_property_wealth_equals_sum_of_saved_inputs(_formula_simulation, values):
    sim = _formula_simulation(dict(zip(PROPERTY_INPUTS, values)))

    assert _value(sim, "property_wealth") == pytest.approx(
        _property_sum(sim), rel=2e-6, abs=0.01
    )


@PROPERTY_SETTINGS
@given(st.tuples(*(MONEY for _ in PROPERTY_INPUTS)), st.sampled_from(REGIONS))
@example((0, 0, 0, 20_000, 0, 0), "LONDON")
def test_household_land_value_is_at_least_direct_uk_land(
    _formula_simulation, values, region
):
    sim = _formula_simulation(dict(zip(PROPERTY_INPUTS, values)), region=region)
    direct_land = _value(sim, "owned_land")
    land = _value(sim, "household_land_value")
    # Subtracting independently rounded stocks can lose a few float32 ulps.
    tolerance = 2e-6 * max(1, _property_sum(sim))

    assert land >= direct_land - tolerance


@PROPERTY_SETTINGS
@given(MONEY, st.sampled_from(REGIONS))
@example(30_000, "LONDON")
def test_overseas_only_households_have_zero_uk_land(_formula_simulation, value, region):
    sim = _formula_simulation({"overseas_property_value": value}, region=region)

    assert _value(sim, "property_wealth") == _value(sim, "overseas_property_value")
    assert _value(sim, "household_land_value") == 0


@PROPERTY_SETTINGS
@given(MONEY, st.sampled_from(REGIONS))
@example(20_000, "LONDON")
def test_land_only_households_count_direct_uk_land_once(
    _formula_simulation, value, region
):
    sim = _formula_simulation({"owned_land": value}, region=region)
    direct_land = _value(sim, "owned_land")

    assert _value(sim, "property_wealth") == direct_land
    assert _value(sim, "household_land_value") == direct_land
    assert _value(sim, "total_wealth") == direct_land


@PROPERTY_SETTINGS
@given(st.tuples(*(MONEY for _ in (*PROPERTY_INPUTS, *OTHER_WEALTH_INPUTS))))
@example((60_000, 25_000, 15_000, 20_000, 30_000, 40_000, 10_000, 5_000, 1_000))
def test_total_wealth_includes_every_asset_category_once(_formula_simulation, values):
    sim = _formula_simulation(
        dict(zip((*PROPERTY_INPUTS, *OTHER_WEALTH_INPUTS), values))
    )
    expected = sum(
        _value(sim, variable) for variable in (*PROPERTY_INPUTS, *OTHER_WEALTH_INPUTS)
    )

    assert _value(sim, "total_wealth") == pytest.approx(expected, rel=2e-6, abs=0.01)


def test_overseas_only_household_has_no_household_lvt():
    reform = {
        "gov.contrib.ubi_center.land_value_tax.household_rate": {
            "2024-01-01.2026-12-31": 0.01
        }
    }
    overseas = _simulation({"overseas_property_value": 100_000}, reform=reform)
    domestic = _simulation(COMPONENT_VALUES, reform=reform)

    assert _value(overseas, "LVT") == 0
    assert _value(domestic, "LVT") == pytest.approx(1_050)


@pytest.mark.parametrize(
    "second_homes,buy_to_let", [(100_000, 0), (0, 200_000), (100_000, 200_000)]
)
def test_second_homes_and_buy_to_let_use_one_explicit_domestic_purchase(
    second_homes, buy_to_let
):
    components = _saved_components(
        {"second_homes": second_homes, "buy_to_let": buy_to_let}
    )
    stocks_only = _simulation({**components, "property_purchased": True})
    assert _value(stocks_only, "additional_residential_property_purchased") == 0
    assert _value(stocks_only, "sdlt_on_transactions") == 0
    combined = second_homes + buy_to_let
    sim = _simulation(
        {**components, "additional_residential_property_purchased": combined}
    )

    assert _value(sim, "residential_property_value") == combined
    assert _value(sim, "property_wealth") == combined
    assert _value(sim, "total_wealth") == combined
    assert _value(sim, "additional_residential_property_purchased") == combined
    stamp_duty = sim.tax_benefit_system.parameters(BASE_YEAR).gov.hmrc.stamp_duty
    assert _value(sim, "sdlt_on_transactions") == pytest.approx(
        stamp_duty.residential.purchase.additional.rate.calc(np.array([combined]))[0]
    )


@pytest.mark.parametrize(
    "variable", ["overseas_property_value", "other_property_value"]
)
def test_overseas_and_unclassified_property_do_not_enter_uk_purchases_or_sdlt(variable):
    sim = _simulation({variable: 500_000, "property_purchased": True})

    for purchase in (
        "main_residential_property_purchased",
        "additional_residential_property_purchased",
        "non_residential_property_purchased",
    ):
        assert _value(sim, purchase) == 0
    assert _value(sim, "sdlt_on_transactions") == 0
    assert _value(sim, "stamp_duty_land_tax") == 0


def _assert_projected_component_accounting(sim, assets, year):
    parameters = sim.tax_benefit_system.parameters
    projected = {}
    for variable, amount in assets.items():
        index_path = sim.tax_benefit_system.variables[variable].uprating
        index = parameters.get_child(index_path)
        expected = amount * index(year) / index(BASE_YEAR)
        projected[variable] = _value(sim, variable, year)
        # Dataset GDP projections compound the growth rates; cumulative indices
        # round their levels. Residential inputs retain current main's HPI route.
        assert projected[variable] == pytest.approx(expected, rel=1e-4, abs=0.02)
        assert _value(sim, variable, f"{year}-01") == projected[variable]
    total = sum(projected.values())
    assert _value(sim, "property_wealth", year) == pytest.approx(total, rel=2e-6)
    assert _value(sim, "total_wealth", year) == pytest.approx(total, rel=2e-6)
    assert _value(sim, "property_wealth", f"{year}-01") == _value(
        sim, "property_wealth", year
    )
    land = (
        total - projected["owned_land"] - projected["overseas_property_value"]
    ) * 0.85 + projected["owned_land"]
    assert _value(sim, "household_land_value", year) == pytest.approx(land, rel=2e-6)
    assert _value(sim, "household_land_value", f"{year}-01") == _value(
        sim, "household_land_value", year
    )


@pytest.mark.parametrize("year", [2024, 2026])
def test_situation_uprating_preserves_accounting_and_monthly_stocks(year):
    assets = {**COMPONENT_VALUES, "other_property_value": 40_000}
    sim = _simulation(assets)

    _assert_projected_component_accounting(sim, assets, year)


@pytest.mark.parametrize("year", [2024, 2026])
def test_component_only_dataset_derives_uprated_property_wealth(year):
    assets = {**COMPONENT_VALUES, "other_property_value": 40_000}
    dataset = _component_dataset(assets)
    assert "property_wealth" not in dataset.household.columns
    sim = Simulation(dataset=dataset)

    _assert_projected_component_accounting(sim, assets, year)


def test_legacy_stored_total_overrides_formula_until_removed_by_data_release():
    # Existing releases are deliberately not migrated by the model. uk-data#543
    # must stop persisting this column, including inherited copies of it.
    legacy = _component_dataset(COMPONENT_VALUES, stored_total=1)
    legacy_sim = Simulation(dataset=legacy)
    assert _value(legacy_sim, "property_wealth") == 1
    assert _value(legacy_sim, "property_wealth", 2026) == 1

    components_only = legacy.copy()
    components_only.household = components_only.household.drop(
        columns="property_wealth"
    )
    sim = Simulation(dataset=components_only)
    assert _value(sim, "property_wealth") == 150_000
    _assert_projected_component_accounting(sim, COMPONENT_VALUES, 2026)

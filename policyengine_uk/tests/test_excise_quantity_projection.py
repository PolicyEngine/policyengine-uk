"""Alcohol and tobacco quantity inputs grow with the OBR's clearances per head
(#2596).

Each input declares its product group's index under
``gov.economic_assumptions.indices.obr.per_capita``, and dataset projection
grows it by the same ``yoy_growth`` series: the growth in the OBR's clearances
of the group (October 2026 receipts Tables 4.11 and 4.12, after the March 2026
EFO's 2024-25 outturn) over one plus ``ons.population`` growth. Dataset
projection grows household weights by ``ons.population``, so the weighted
quantities grow with the clearances, and a duty-rate reform moves receipts
through the rate alone.
"""

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data import economic_assumptions
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    uprating_input_fingerprint,
)
from policyengine_uk.model_api import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

GROWTH = "gov.economic_assumptions.yoy_growth.obr.per_capita"
INDEX = "gov.economic_assumptions.indices.obr.per_capita"
POPULATION = "gov.economic_assumptions.yoy_growth.ons.population"
INPUTS = {
    "tobacco_clearances.cigarettes": ("cigarettes_per_week",),
    "tobacco_clearances.hand_rolling_tobacco": ("hand_rolling_tobacco_grams_per_week",),
    "tobacco_clearances.other_tobacco_products": (
        "cigars_grams_per_week",
        "heated_tobacco_grams_per_week",
        "other_tobacco_grams_per_week",
    ),
    "alcohol_clearances.beer_and_cider": (
        "beer_litres",
        "cider_litres",
        "sparkling_cider_litres",
    ),
    "alcohol_clearances.wine": ("other_fermented_litres", "wine_litres"),
    "alcohol_clearances.spirits": ("spirits_litres",),
}
GROUP = {name: group for group, names in INPUTS.items() for name in names}
# OBR clearances by product group, 2024-25 to 2031-32: the March 2026 EFO's
# 2024-25 outturn (receipts Tables 3.11 and 3.12, column C), then the October
# 2026 EFO's 2025-26 outturn and forecast (Tables 4.11 and 4.12, columns C to
# I). Million sticks, thousand kg, and thousand hectolitres of alcohol.
CLEARANCES = {
    "tobacco_clearances.cigarettes": (13578.199084269218, 12224.568453264392, 10962.756413840059, 9853.5452739735829, 9042.8621730867635, 8222.5673694138313, 7677.1786518547042, 7165.065963684312),
    "tobacco_clearances.hand_rolling_tobacco": (4028.4786869103718, 3338.0207129187247, 3112.6781722236924, 2886.8250342433803, 2649.2381871262742, 2482.242556381048, 2384.6513795861088, 2273.4315215751089),
    "tobacco_clearances.other_tobacco_products": (696.58878604045401, 601.72119516629675, 570.78371235846851, 547.48868265410397, 502.43014658034485, 478.01479115950667, 460.50663098211788, 434.81308397816122),
    "alcohol_clearances.beer_and_cider": (2168.2921615793966, 2108.7303043893562, 2069.8474469367434, 2027.3458030333193, 2012.6406194934405, 2001.8700847628832, 1982.9201100206114, 1962.5485885566063),
    "alcohol_clearances.wine": (1619.9398031719702, 1569.041217813324, 1567.7826624097067, 1540.2033043369458, 1530.2485351419407, 1520.7475110216285, 1505.5439058920508, 1491.4031570887553),
    "alcohol_clearances.spirits": (1289.5543778979199, 1272.4562775587838, 1262.3692523269856, 1241.1318815407608, 1235.8250379612948, 1230.5012764962146, 1218.4826638265554, 1209.5688671337984),
}  # fmt: skip
FORECAST_YEARS = range(2024, 2032)
YEARS = range(2024, 2033)
ALCOHOL_RATES = "gov.hmrc.alcohol_duty.rates"
TOBACCO_RATES = "gov.hmrc.tobacco_duty.rates"
DUTIES = ("alcohol_duty", "tobacco_duty")


@lru_cache(maxsize=None)
def current_law():
    return CountryTaxBenefitSystem().parameters


@pytest.fixture(scope="module")
def parameters():
    return current_law()


def growth(parameters, path, year):
    return parameters.get_child(path)(f"{year}-01-01")


def index(parameters, group, year):
    return parameters.get_child(f"{INDEX}.{group}")(f"{year}-01-01")


def household_frame(year, households):
    """One adult in each household, with the given household inputs. Each
    household is a dict of inputs; ``household_weight`` defaults to 1."""
    count = len(households)
    columns = sorted({name for household in households for name in household})
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": range(1, count + 1),
                "person_benunit_id": range(1, count + 1),
                "person_household_id": range(1, count + 1),
                "age": [40] * count,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": range(1, count + 1)}),
        household=pd.DataFrame(
            {
                "household_id": range(1, count + 1),
                "region": ["LONDON"] * count,
                "tenure_type": ["OWNED_OUTRIGHT"] * count,
                "council_tax": [0.0] * count,
                "rent": [0.0] * count,
                "household_weight": [1.0] * count,
                **{
                    name: [float(household.get(name, 0.0)) for household in households]
                    for name in columns
                },
            }
        ),
        fiscal_year=year,
    )


def situation(inputs, year=2024):
    return {
        "people": {"person": {"age": {year: 40}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                **{name: {year: value} for name, value in inputs.items()},
            }
        },
    }


# A household that buys every product: 5% beer, 4.5% cider, 7% sparkling
# cider, 12% wine, 40% spirits and 5% other fermented drinks, and pays £16 a
# pack for its cigarettes.
SMOKER_AND_DRINKER = {
    "beer_litres": 300.0,
    "beer_abv": 0.05,
    "cider_litres": 60.0,
    "cider_abv": 0.045,
    "sparkling_cider_litres": 20.0,
    "sparkling_cider_abv": 0.07,
    "wine_litres": 80.0,
    "wine_abv": 0.12,
    "spirits_litres": 10.0,
    "spirits_abv": 0.40,
    "other_fermented_litres": 15.0,
    "other_fermented_abv": 0.05,
    "cigarettes_per_week": 70.0,
    "cigarette_price_per_pack": 16.0,
    "hand_rolling_tobacco_grams_per_week": 25.0,
    "cigars_grams_per_week": 5.0,
    "other_tobacco_grams_per_week": 3.0,
    "heated_tobacco_grams_per_week": 4.0,
}
QUANTITIES = {name: SMOKER_AND_DRINKER[name] for name in GROUP}


def test_every_quantity_input_declares_its_product_group_index():
    """Every alcohol and tobacco quantity input declares its product group's
    index, and dataset projection grows it by the same group's series."""
    from policyengine_uk.system import system

    folder = Path(__file__).parents[1] / "variables/input/consumption"
    quantities = {
        path.stem
        for path in [*folder.glob("alcohol/*.py"), *folder.glob("tobacco/*.py")]
        if path.stem.endswith(("_litres", "_per_week"))
    }
    assert quantities == set(GROUP)
    for name, group in GROUP.items():
        assert system.variables[name].uprating == f"{INDEX}.{group}", name
    mapping = yaml.safe_load(
        (Path(__file__).parents[1] / "data/uprating_indices.yaml").read_text()
    )
    clearances = {key: value for key, value in mapping.items() if "clearances" in key}
    assert clearances == {
        f"{GROWTH}.{group}": sorted(names) for group, names in INPUTS.items()
    }


def test_strengths_shares_and_the_cigarette_price_stay_as_they_are():
    """Strengths and draught shares are ratios, and the cigarette price is a
    price, not a quantity (#2596 leaves its forward path out): none of them
    declares an index or appears in the uprating map."""
    from policyengine_uk.system import system

    folder = Path(__file__).parents[1] / "variables/input/consumption"
    others = {
        path.stem
        for path in [*folder.glob("alcohol/*.py"), *folder.glob("tobacco/*.py")]
    } - set(GROUP)
    assert others >= {"beer_abv", "wine_draught_share", "cigarette_price_per_pack"}
    mapped = {
        name
        for names in economic_assumptions._uprating_index_map().values()
        for name in names
    }
    for name in others:
        assert system.variables[name].uprating is None, name
        assert name not in mapped, name


def test_indices_are_positive_from_the_2024_base_year(parameters):
    for group in INPUTS:
        assert index(parameters, group, 2024) == 1
        for year in range(2024, 2040):
            assert index(parameters, group, year) > 0, (group, year)


def test_each_series_is_its_clearances_per_head(parameters):
    """Each year's growth, to six decimals, is the clearances' growth over
    one plus that year's population growth, the growth of household
    weights."""
    for group, levels in CLEARANCES.items():
        assert growth(parameters, f"{GROWTH}.{group}", 2024) == 0
        for year in range(2025, 2032):
            published = levels[year - 2024] / levels[year - 2025]
            population = growth(parameters, POPULATION, year)
            assert growth(parameters, f"{GROWTH}.{group}", year) == round(
                published / (1 + population) - 1, 6
            ), (group, year)
        # After the forecast the clearances hold flat.
        for year in range(2032, 2074):
            population = growth(parameters, POPULATION, year)
            assert growth(parameters, f"{GROWTH}.{group}", year) == round(
                1 / (1 + population) - 1, 6
            ), (group, year)


def test_cigarettes_per_head_halve_by_2031(parameters):
    """The October 2026 forecast puts 2031-32 cigarette clearances 47.2%
    below 2024-25. Population grows 1.5% over those years, so clearances per
    head fall 48.0%, and the index stands at 0.520."""
    levels = CLEARANCES["tobacco_clearances.cigarettes"]
    assert levels[-1] / levels[0] - 1 == pytest.approx(-0.4723, abs=1e-4)
    population = np.prod(
        [1 + growth(parameters, POPULATION, year) for year in range(2025, 2032)]
    )
    assert population - 1 == pytest.approx(0.0154, abs=1e-4)
    assert index(parameters, "tobacco_clearances.cigarettes", 2031) == pytest.approx(
        levels[-1] / levels[0] / population, abs=1e-5
    )
    assert index(parameters, "tobacco_clearances.cigarettes", 2031) == pytest.approx(
        0.520, abs=5e-4
    )


def test_weighted_quantities_follow_the_clearances(parameters):
    """Two households with different weights: dataset projection grows each
    quantity per head and each weight by population growth, so every
    weighted total grows with the OBR's clearances, and in 2032-33, after
    the forecast, holds at 2031-32's. Growing quantities by the clearances
    themselves would count population growth twice: 1.5% too much by
    2031-32."""
    households = [QUANTITIES, {name: 2 * value for name, value in QUANTITIES.items()}]
    frame = household_frame(2024, households)
    frame.household["household_weight"] = [1_000.0, 250.0]
    projected = extend_single_year_dataset(frame, parameters, end_year=2032)
    base = projected[2024].household
    weights = {year: projected[year].household["household_weight"] for year in YEARS}
    population = 1.0
    for year in YEARS:
        if year > 2024:
            population *= 1 + growth(parameters, POPULATION, year)
        assert weights[year].sum() == pytest.approx(1_250 * population, rel=1e-12)
        for name, group in GROUP.items():
            levels = CLEARANCES[group]
            published = levels[min(year, 2031) - 2024] / levels[0]
            total = (weights[year] * projected[year].household[name]).sum()
            base_total = (weights[2024] * base[name]).sum()
            assert total / base_total == pytest.approx(published, rel=1e-5), (
                name,
                year,
            )
    assert population - 1 > 0.015


QUANTITY = st.floats(min_value=0, max_value=1e4, allow_nan=False)


# Each example projects a dataset through 2032.
@settings(max_examples=8, deadline=None, derandomize=True)
@given(
    quantities=st.fixed_dictionaries({name: QUANTITY for name in GROUP}),
    weight=st.floats(min_value=0.1, max_value=1e5, allow_nan=False),
)
def test_projected_quantities_are_the_base_times_the_index(quantities, weight):
    """For any quantities and weight: dataset projection gives each year's
    quantity as the 2024 quantity times its series' growth compounded, which
    is its index to the index's five decimals; Core's uprating of a 2024
    situation input (the other route to a later year) agrees; the weight
    grows by population alone."""
    parameters = current_law()
    frame = household_frame(2024, [quantities])
    frame.household["household_weight"] = [weight]
    projected = extend_single_year_dataset(frame, parameters, end_year=2032)
    simulation = Simulation(situation=situation(quantities))
    for name, group in GROUP.items():
        compounded = 1.0
        for year in YEARS:
            if year > 2024:
                compounded *= 1 + growth(parameters, f"{GROWTH}.{group}", year)
            stored = projected[year].household[name].iloc[0]
            assert stored == pytest.approx(quantities[name] * compounded, rel=1e-12)
            ratio = index(parameters, group, year) / index(parameters, group, 2024)
            assert compounded == pytest.approx(ratio, rel=1e-4), (name, year)
            uprated = simulation.calculate(name, year)[0]
            assert uprated == pytest.approx(quantities[name] * ratio, rel=1e-6)
    population = 1.0
    for year in YEARS:
        if year > 2024:
            population *= 1 + growth(parameters, POPULATION, year)
        stored = projected[year].household["household_weight"].iloc[0]
        assert stored == pytest.approx(weight * population, rel=1e-12)


def test_a_later_year_charges_duty_on_the_uprated_quantity(parameters):
    """A projected 2027 household pays the duty a household holding the 2027
    quantities pays, less than on its 2024 quantities: 2027 rates on fewer
    cigarettes and drinks."""
    projected = Simulation(dataset=household_frame(2024, [SMOKER_AND_DRINKER]))
    uprated = {
        name: SMOKER_AND_DRINKER[name]
        * index(parameters, group, 2027)
        / index(parameters, group, 2024)
        for name, group in GROUP.items()
    }
    held = {**SMOKER_AND_DRINKER, **uprated}
    at_2027 = Simulation(situation=situation(held, year=2027))
    flat = Simulation(situation=situation(SMOKER_AND_DRINKER, year=2027))
    for duty in DUTIES:
        duty_2027 = projected.calculate(duty, 2027)[0]
        assert duty_2027 == pytest.approx(at_2027.calculate(duty, 2027)[0], rel=1e-4)
        assert duty_2027 < flat.calculate(duty, 2027)[0]
    # Cigarettes alone: 70 a week is 3,640 a year. Per head, clearances fall
    # 10.3%, 10.5% and 10.2% in 2025-26, 2026-27 and 2027-28, an index of
    # 0.721 in 2027, which leaves 2,624.
    assert index(parameters, "tobacco_clearances.cigarettes", 2027) == 0.72092
    cigarettes = projected.calculate("cigarettes_per_week", 2027)[0] * 52
    assert cigarettes == pytest.approx(3_640 * 0.72092, rel=1e-5)


def rate_leaves(parameters):
    """Every alcohol and tobacco duty rate the duty formulas read, without
    the wine strength easement's switch, which is true or false."""
    leaves = [
        leaf
        for node in (ALCOHOL_RATES, TOBACCO_RATES)
        for leaf in parameters.get_child(node).get_descendants()
        if not hasattr(leaf, "children")
    ]
    switches = [leaf.name for leaf in leaves if leaf.metadata["unit"] == "bool"]
    assert switches == [f"{ALCOHOL_RATES}.wine_easement"]
    return [leaf.name for leaf in leaves if leaf.name not in switches]


# Each example builds a reform, which reprocesses the parameter tree.
@settings(max_examples=4, deadline=None, derandomize=True)
@given(
    factor=st.floats(min_value=0.1, max_value=3, allow_nan=False),
    year=st.integers(min_value=2027, max_value=2031),
    scale=st.floats(min_value=0.1, max_value=10, allow_nan=False),
)
def test_a_duty_rate_reform_moves_receipts_by_the_rate_alone(factor, year, scale):
    """Scaling every alcohol and tobacco duty rate in a year from 2027-28,
    when the current-law rates hold flat, leaves every projected quantity as
    it was and multiplies each duty by the factor: the duties are linear in
    their rates, and the rates are not among the parameters the dataset
    projection reads."""
    parameters = current_law()
    inputs = {
        name: value * scale if name in GROUP else value
        for name, value in SMOKER_AND_DRINKER.items()
    }
    changes = {
        name: {str(year): parameters.get_child(name)(f"{year}-06-01") * factor}
        for name in rate_leaves(parameters)
    }
    scenario = Scenario(parameter_changes=changes)
    baseline = Simulation(dataset=household_frame(2024, [inputs]))
    reform = Simulation(dataset=household_frame(2024, [inputs]), scenario=scenario)
    assert uprating_input_fingerprint(
        reform.tax_benefit_system.parameters
    ) == uprating_input_fingerprint(baseline.tax_benefit_system.parameters)
    for name in GROUP:
        for period in (2024, year):
            np.testing.assert_array_equal(
                reform.calculate(name, period), baseline.calculate(name, period)
            )
    for duty in DUTIES:
        before = baseline.calculate(duty, year)[0]
        assert before > 0
        assert reform.calculate(duty, year)[0] == pytest.approx(
            before * factor, rel=1e-5
        )


# Outputs that read neither duty, directly or through a total.
UNTOUCHED = (
    "income_tax",
    "national_insurance",
    "household_benefits",
    "household_market_income",
    "hbai_household_net_income",
    "vat",
)


def test_the_change_touches_only_the_quantity_inputs(parameters):
    """Differential against the projection without this change, which
    leaves the quantity inputs out of the uprating map and out of Core's
    fallback: every other stored input is the same in every year, the
    quantity inputs differ by their index alone, and outputs differ only
    through the two duties."""
    households = [
        {**SMOKER_AND_DRINKER, "remote_gaming_net_losses": 500.0},
        {"beer_litres": 50.0, "cigarettes_per_week": 0.0},
    ]
    frame = household_frame(2024, households)
    frame.person["employment_income"] = [30_000.0, 55_000.0]
    frame.household["household_weight"] = [700.0, 300.0]
    mapping = economic_assumptions._uprating_index_map()
    unmapped = economic_assumptions._unmapped_uprating_indices
    without_map = {
        key: names for key, names in mapping.items() if "clearances" not in key
    }
    assert sum(len(names) for names in mapping.values()) - sum(
        len(names) for names in without_map.values()
    ) == len(GROUP)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(economic_assumptions, "_uprating_index_map", lambda: without_map)
        patch.setattr(
            economic_assumptions,
            "_unmapped_uprating_indices",
            lambda uprating: {
                name: index
                for name, index in unmapped(uprating).items()
                if name not in GROUP
            },
        )
        before = extend_single_year_dataset(frame, parameters, end_year=2032)
    after = extend_single_year_dataset(frame, parameters, end_year=2032)
    for year in YEARS:
        for table in ("person", "benunit", "household"):
            old, new = getattr(before[year], table), getattr(after[year], table)
            assert list(old.columns) == list(new.columns)
            for column in old.columns:
                if column in GROUP:
                    group = GROUP[column]
                    ratio = index(parameters, group, year) / index(
                        parameters, group, 2024
                    )
                    np.testing.assert_allclose(
                        new[column], old[column] * ratio, rtol=1e-4
                    )
                    np.testing.assert_array_equal(old[column], frame.household[column])
                else:
                    pd.testing.assert_series_equal(old[column], new[column])
    old_simulation = Simulation(dataset=before)
    new_simulation = Simulation(dataset=after)
    for year in YEARS:
        changed = sum(
            new_simulation.calculate(duty, year) - old_simulation.calculate(duty, year)
            for duty in DUTIES
        )
        if year > 2024:
            assert changed[0] < 0
        for total in ("household_tax", "gov_tax"):
            difference = new_simulation.calculate(
                total, year
            ) - old_simulation.calculate(total, year)
            np.testing.assert_allclose(difference, changed, atol=0.01)
        net = new_simulation.calculate(
            "household_net_income", year
        ) - old_simulation.calculate("household_net_income", year)
        np.testing.assert_allclose(net, -changed, atol=0.01)
        for name in UNTOUCHED:
            np.testing.assert_array_equal(
                new_simulation.calculate(name, year),
                old_simulation.calculate(name, year),
            )

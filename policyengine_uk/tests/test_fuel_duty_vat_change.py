"""VAT includes excise duty: OBR fuel-duties explainer and HMRC VATVAL02300.

OBR's example is 52.95p duty plus 10.59p VAT at 20% per litre. Thus a
5p duty change changes VAT by 1p per litre when quantities and the non-tax
price stay fixed. Expected amounts below use that arithmetic, not model
output. Synthetic consumption bases isolate the change from existing VAT.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario


def situation(year=2026, **inputs):
    values = {
        "full_rate_vat_consumption": 1_000,
        "reduced_rate_vat_consumption": 0,
        "petrol_litres": 600,
        "diesel_litres": 400,
        "lpg_kg": 0,
        "natural_gas_kg": 0,
        **inputs,
    }
    return {
        "people": {"person1": {"age": {year: 40}}},
        "benunits": {"benunit": {"members": ["person1"]}},
        "households": {
            "household": {
                "members": ["person1"],
                **{name: {year: value} for name, value in values.items()},
            }
        },
    }


def simulation(year=2026, changes=None, **inputs):
    scenario = Scenario(parameter_changes=changes) if changes else None
    return Simulation(situation=situation(year, **inputs), scenario=scenario)


@pytest.mark.parametrize("rate, expected", [(0.5795, 10), (0.4795, -10)])
def test_duty_changes_vat_without_grossing_or_school_allocation(rate, expected):
    # 1,000 litres x (+/- £0.05) x 20%, without either VAT grossing factor
    # or the private-school share of receipts applied to the extra VAT.
    sim = simulation(changes={"gov.hmrc.fuel_duty.petrol_and_diesel": {"2026": rate}})
    assert sim.calculate("vat_change", 2026)[0] == pytest.approx(expected, abs=0.01)
    assert sim.calculate("fuel_duty_vat_change", 2026)[0] == pytest.approx(
        expected, abs=0.01
    )


@pytest.mark.parametrize("year", [2025, 2026, 2027, 2028, 2031])
def test_native_dated_schedules_add_no_vat_without_a_duty_reform(year):
    sim = simulation(year, lpg_kg=100, natural_gas_kg=200)
    assert sim.calculate("fuel_duty_vat_change", year)[0] == 0
    assert sim.calculate("vat_change", year)[0] == pytest.approx(0, abs=0.01)


def test_supplied_duty_is_not_mistaken_for_a_parameter_reform():
    sim = simulation(fuel_duty=0)
    assert sim.calculate("fuel_duty_vat_change", 2026)[0] == 0
    assert sim.calculate("vat_change", 2026)[0] == pytest.approx(0, abs=0.01)


def test_leap_year_uses_all_three_native_duty_rates():
    # FY2027: 86 days at 52.95p, 275 at 60.59p and 5 at 63.21p.
    # A reform retaining 52.95p throughout removes duty on the last 280 days.
    expected = 1_000 * (0.5295 - (0.5295 * 86 + 0.6059 * 275 + 0.6321 * 5) / 366) * 0.2
    sim = simulation(
        2027,
        changes={"gov.hmrc.fuel_duty.petrol_and_diesel": {"2027": 0.5295}},
    )
    assert sim.calculate("fuel_duty_vat_change", 2027)[0] == pytest.approx(
        expected, abs=0.01
    )
    assert sim.calculate("vat_change", 2027)[0] == pytest.approx(expected, abs=0.01)


def test_current_vat_rate_applies_to_the_duty_change():
    sim = simulation(
        changes={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {"2026": 0.5795},
            "gov.hmrc.vat.standard_rate": {"2026": 0.25},
        },
        full_rate_vat_consumption=0,
    )
    # 1,000 litres x £0.05 x the reformed 25%, not the baseline 20%.
    assert sim.calculate("fuel_duty_vat_change", 2026)[0] == pytest.approx(12.5)
    assert sim.calculate("vat_change", 2026)[0] == pytest.approx(12.5)


def test_an_ordinary_baseline_parameter_uses_thirty_april_not_january():
    from policyengine_uk.variables.gov.hmrc.fuel_duty_vat_change import _baseline_rate

    # Synthetic history isolates the model's ordinary fiscal convention.
    rate = Parameter(
        "synthetic.relief",
        data={"values": {"2026-01-01": 0.05, "2026-04-20": 0.06}},
    )
    assert _baseline_rate(rate, 2026) == 0.06


def test_a_missing_blended_value_uses_the_same_thirty_april_fallback():
    from policyengine_uk.variables.gov.hmrc.fuel_duty_vat_change import _baseline_rate

    rate = Parameter(
        "synthetic.relief",
        data={
            "values": {"2026-01-01": 0.05, "2026-06-01": None},
            "metadata": {"fiscal_year_blend": True},
        },
    )
    assert _baseline_rate(rate, 2026) == 0.05


@settings(max_examples=5, deadline=None)
@given(
    quantities=st.lists(
        st.tuples(*(st.integers(0, 10_000) for _ in range(4))),
        min_size=1,
        max_size=8,
    )
)
def test_vat_delta_is_additive_and_matches_duty_at_the_current_rate(quantities):
    """Vectorized conservation: extra VAT = duty change x current VAT rate."""
    year = 2026
    rows = [
        situation(
            year,
            petrol_litres=petrol,
            diesel_litres=diesel,
            lpg_kg=lpg,
            natural_gas_kg=gas,
            in_rural_fuel_duty_relief_area=i % 2 == 0,
        )
        for i, (petrol, diesel, lpg, gas) in enumerate(quantities)
    ]
    combined = {"people": {}, "benunits": {}, "households": {}}
    for i, row in enumerate(rows):
        combined["people"][f"person{i}"] = row["people"]["person1"]
        combined["benunits"][f"benunit{i}"] = {"members": [f"person{i}"]}
        combined["households"][f"household{i}"] = {
            **row["households"]["household"],
            "members": [f"person{i}"],
        }
    changes = {
        "gov.hmrc.fuel_duty.petrol_and_diesel": {"2026": 0.5795},
        "gov.hmrc.fuel_duty.rural_fuel_duty_relief": {"2026": 0.06},
        "gov.hmrc.fuel_duty.lpg": {"2026": 0.3888},
        "gov.hmrc.fuel_duty.natural_gas": {"2026": 0.2757},
        "gov.hmrc.vat.standard_rate": {"2026": 0.25},
    }
    baseline = Simulation(situation=combined)
    reform = Simulation(
        situation=combined, scenario=Scenario(parameter_changes=changes)
    )
    delta = reform.calculate("fuel_duty_vat_change", year)
    # Independent statutory-rate arithmetic: main duty +5p; eligible rural
    # relief +1p; LPG +10p/kg; natural gas +5p/kg. VAT is now 25%.
    expected = [
        (
            (petrol + diesel) * (0.05 - (0.01 if i % 2 == 0 else 0))
            + lpg * 0.1
            + gas * 0.05
        )
        * 0.25
        for i, (petrol, diesel, lpg, gas) in enumerate(quantities)
    ]
    np.testing.assert_allclose(delta, expected, atol=0.01, rtol=1e-6)
    duty_difference = reform.calculate("fuel_duty", year) - baseline.calculate(
        "fuel_duty", year
    )
    np.testing.assert_allclose(delta, duty_difference * 0.25, atol=0.01, rtol=1e-6)

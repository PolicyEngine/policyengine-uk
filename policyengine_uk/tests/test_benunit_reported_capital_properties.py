"""Properties of `benunit_reported_capital`, the benefit unit's recorded capital.

A dataset records what it observes (the benefit unit's savings and
investments, -1 when nothing is recorded), and each means test derives its
own reported capital from it: `uc_reported_capital` and
`pension_credit_reported_capital` default to it and can still be set directly.

Invariants, over generated households of one or two benefit units:

1. Derivation: with only the recorded input set, both programmes' reported
   capital equals it, -1 included.
2. Differential: recording R once gives the same assessable capital, eligibility
   and entitlement for Universal Credit and Pension Credit as setting R on both
   programme variables directly, which is how they were supplied before the
   input existed. With nothing recorded this is the old default (-1), so the
   input changes nothing for data that do not supply it.
3. Precedence: a programme variable set directly wins for that programme only.
4. Override identity and bounds: a unit with recorded R >= 0 has Universal
   Credit assessable capital R, whatever the household holds, and assessable
   capital is never negative.
5. Monotonicity: Universal Credit tariff income never falls, and eligibility and
   the award never rise, as recorded capital rises.
6. Uprating: a dataset that stores the input, or either programme variable
   directly as datasets built before the input did, projects it to later years
   exactly as it projects `savings`.
7. Periods: the input set for one year is uprated into later years. A
   programme variable set directly applies only to the years it is set, as for
   any formula variable; later years derive from the input (intended: the
   input carries the uprating).
"""

from pathlib import Path

import numpy as np
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import pandas as pd

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2025
SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
recorded = st.one_of(st.just(-1), st.integers(min_value=0, max_value=40_000))
PROGRAMME_VARIABLES = ["uc_reported_capital", "pension_credit_reported_capital"]
OUTPUTS = [
    "uc_reported_capital",
    "pension_credit_reported_capital",
    "uc_assessable_capital",
    "pension_credit_assessable_capital",
    "is_uc_eligible",
    "uc_tariff_income",
    "universal_credit",
    "pension_credit",
]


@st.composite
def households(draw):
    units = []
    for _ in range(draw(st.integers(min_value=1, max_value=2))):
        units.append(
            {
                "ages": draw(
                    st.lists(
                        st.sampled_from([25, 40, 58, 70, 82]), min_size=1, max_size=2
                    )
                ),
                "children": draw(st.integers(min_value=0, max_value=2)),
                "earnings": draw(st.sampled_from([0, 0, 9_000, 30_000])),
                "state_pension": draw(st.sampled_from([0, 9_000])),
                "recorded": draw(recorded),
            }
        )
    household = {
        "savings": draw(st.sampled_from([0, 4_000, 30_000, 120_000])),
        "corporate_wealth": draw(st.sampled_from([0, 50_000])),
        "rent": draw(st.sampled_from([0, 7_200])),
    }
    return units, household


def simulate(units, household, benunit_inputs):
    year = str(YEAR)
    people, benunits, members = {}, {}, []
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"a{i}_{j}"
            people[name] = {
                "age": {year: age},
                "is_claimant_or_partner": {year: True},
                "employment_income": {year: unit["earnings"] if j == 0 else 0},
                "state_pension": {year: unit["state_pension"] if age >= 66 else 0},
            }
            names.append(name)
        for k in range(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {
                "age": {year: 4 + 3 * k},
                "is_claimant_or_partner": {year: False},
            }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            **{k: {year: v} for k, v in benunit_inputs[i].items()},
        }
        members += names
    situation = {
        "people": people,
        "benunits": benunits,
        "households": {
            "h": {
                "members": members,
                "tenure_type": {
                    year: "RENT_PRIVATELY" if household["rent"] else "OWNED_OUTRIGHT"
                },
                **{k: {year: v} for k, v in household.items()},
            }
        },
    }
    return Simulation(situation=situation)


def outputs(sim):
    return {v: np.asarray(sim.calculate(v, YEAR), dtype=float) for v in OUTPUTS}


@SETTINGS
@given(households())
def test_recorded_capital_is_equivalent_to_setting_each_programme(case):
    units, household = case
    via_input = simulate(
        units,
        household,
        [{"benunit_reported_capital": u["recorded"]} for u in units],
    )
    via_programmes = simulate(
        units,
        household,
        [{v: u["recorded"] for v in PROGRAMME_VARIABLES} for u in units],
    )
    a, b = outputs(via_input), outputs(via_programmes)
    for i, unit in enumerate(units):
        for v in PROGRAMME_VARIABLES:
            assert a[v][i] == unit["recorded"]
        if unit["recorded"] >= 0:
            assert a["uc_assessable_capital"][i] == unit["recorded"]
    for v in OUTPUTS:
        np.testing.assert_allclose(a[v], b[v], rtol=0, atol=1e-6, err_msg=v)
    for v in ["uc_assessable_capital", "pension_credit_assessable_capital"]:
        assert np.all(a[v] >= 0)


@SETTINGS
@given(households(), recorded, st.integers(min_value=0, max_value=40_000))
def test_programme_variable_set_directly_wins_for_that_programme(case, base, uc):
    units, household = case
    inputs = [{"benunit_reported_capital": base}] + [
        {"benunit_reported_capital": u["recorded"]} for u in units[1:]
    ]
    inputs[0]["uc_reported_capital"] = uc
    sim = simulate(units, household, inputs)
    assert sim.calculate("uc_reported_capital", YEAR)[0] == uc
    assert sim.calculate("pension_credit_reported_capital", YEAR)[0] == base
    assert sim.calculate("uc_assessable_capital", YEAR)[0] == uc


@SETTINGS
@given(
    households(),
    st.integers(min_value=0, max_value=40_000),
    st.integers(min_value=0, max_value=40_000),
)
def test_uc_never_rises_with_recorded_capital(case, x, y):
    units, household = case
    low, high = sorted([x, y])

    def run(value):
        inputs = [{"benunit_reported_capital": value}] + [
            {"benunit_reported_capital": u["recorded"]} for u in units[1:]
        ]
        return outputs(simulate(units, household, inputs))

    lo, hi = run(low), run(high)
    assert hi["uc_tariff_income"][0] >= lo["uc_tariff_income"][0]
    assert hi["is_uc_eligible"][0] <= lo["is_uc_eligible"][0]
    assert hi["universal_credit"][0] <= lo["universal_credit"][0] + 1e-6


def test_recorded_capital_uprates_with_savings():
    """The input uprates like `savings`. The programme variables are formulas,
    which cannot also carry an uprating index, but stay in the same
    uprating_indices.yaml group so a dataset that stores them directly (such
    as one built before the input existed) projects them the same way."""
    from policyengine_uk.system import system

    variables = system.variables
    indices = yaml.safe_load(
        (Path(__file__).parents[1] / "data" / "uprating_indices.yaml").read_text()
    )
    group = [k for k, v in indices.items() if "savings" in v]
    assert len(group) == 1
    recorded = variables["benunit_reported_capital"]
    assert recorded.uprating == variables["savings"].uprating
    assert recorded.default_value == -1
    assert not recorded.formulas
    for name in ["benunit_reported_capital", *PROGRAMME_VARIABLES]:
        assert name in indices[group[0]]
    for name in PROGRAMME_VARIABLES:
        assert variables[name].formulas
        assert variables[name].uprating is None
        assert variables[name].default_value == -1


def _dataset(benunit_columns, savings):
    """Three single adults, one per benefit unit and household, aged 30, 50
    and 75 so that both programmes assess them."""
    ids = np.arange(1, 4)
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": [30, 50, 75],
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": 1.0,
            "region": "LONDON",
            "rent": 0.0,
            "tenure_type": "OWNED_OUTRIGHT",
            "council_tax": 0.0,
            "savings": savings,
        }
    )
    benunit = pd.DataFrame({"benunit_id": ids, **benunit_columns})
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2025
    )


def test_stored_columns_project_like_savings():
    recorded = [10_000.0, -1.0, 0.0]
    savings = [10_000.0, 20_000.0, 30_000.0]
    for columns in [
        {"benunit_reported_capital": recorded},
        # As a dataset built before the input existed stores them.
        {"uc_reported_capital": recorded, "pension_credit_reported_capital": recorded},
    ]:
        sim = Microsimulation(dataset=_dataset(columns, savings))
        growth = (
            sim.calculate("savings", 2027).values
            / sim.calculate("savings", 2025).values
        )
        assert np.all(growth > 1)
        for name in PROGRAMME_VARIABLES:
            first = sim.calculate(name, 2025).values
            later = sim.calculate(name, 2027).values
            np.testing.assert_array_equal(first, recorded)
            np.testing.assert_allclose(later, np.array(recorded) * growth, rtol=1e-6)
            # A stored -1 stays negative, so "nothing recorded" survives.
            assert later[1] < 0


def _single_adult(benunit_inputs):
    return Simulation(
        situation={
            "people": {"p": {"age": {"2025": 30}}},
            "benunits": {"b": {"members": ["p"], **benunit_inputs}},
            "households": {"h": {"members": ["p"], "savings": {"2025": 50_000}}},
        }
    )


def test_input_set_once_is_uprated_into_later_years():
    sim = _single_adult({"benunit_reported_capital": {"2025": 10_000}})
    index = sim.tax_benefit_system.parameters.get_child(
        "gov.economic_assumptions.indices.obr.per_capita.gdp"
    )
    expected = 10_000 * index("2026-01-01") / index("2025-01-01")
    for name in PROGRAMME_VARIABLES:
        np.testing.assert_allclose(sim.calculate(name, 2026)[0], expected, rtol=1e-6)
    np.testing.assert_allclose(
        sim.calculate("uc_assessable_capital", 2026)[0], expected, rtol=1e-6
    )


def test_programme_variable_set_directly_applies_to_its_year_only():
    """Intended: set the input to have a value carried into later years."""
    for name in PROGRAMME_VARIABLES:
        sim = _single_adult({name: {"2025": 3_000}})
        assert sim.calculate(name, 2025)[0] == 3_000
        assert sim.calculate(name, 2026)[0] == -1
    # With nothing recorded for 2026, UC falls back to the household proxy.
    sim = _single_adult({"uc_reported_capital": {"2025": 3_000}})
    np.testing.assert_allclose(
        sim.calculate("uc_assessable_capital", 2026)[0],
        sim.calculate("savings", 2026)[0],
        rtol=1e-6,
    )
    assert sim.calculate("savings", 2026)[0] > 50_000

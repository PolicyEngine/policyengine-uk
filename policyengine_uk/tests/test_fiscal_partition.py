"""The tax totals against an independently specified tax-head partition.

``policyengine_uk/data/fiscal_partition.yaml`` divides UK tax receipts into
heads, one OBR current-receipts line (split by payer where the model splits
it) per head, and names the one variable that measures each. It was written
from the OBR classification and the variables' formulas, not from the
model's lists, so these tests compare two specifications:

1. Schema: ids and variables are unique, every reference resolves, and no
   variable is both a head and an exclusion.
2. Differential: for each total, the heads the partition assigns to it are
   exactly the variables the model sums (``GOV_TAX_VARIABLES``,
   ``HOUSEHOLD_TAX_VARIABLES``, ``PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES``),
   each listed once.
3. Overlap guard (traced): within a total, no head's formula reaches another
   head of that total unless the partition declares the read (an
   eligibility or imputation route) under the head's ``reads``; every
   declared read occurs. Component and baseline-measure exclusions are reached
   from their head; composite, duplicate and measure-within exclusions are
   reached from no head.
4. Coefficient one (perturbation): raising one head by delta, with every
   other input unchanged, raises each total that includes it by exactly
   delta per member and leaves every other head of those totals unchanged.
   A head counted twice, as corporate SDLT was through ``expected_sdlt``
   (#2159), moves its totals by 2 x delta.
5. Identity (property-based): on random households, years 2025-2030, and
   under SDLT abolition and council tax abolition, each total equals the sum
   of its heads, less the heads ``dropped_when`` names. Heads marked
   ``sign: nonnegative`` are non-negative and heads marked
   ``zero_at_baseline: expected`` are zero at current law; at most one of
   SDLT, LTT and LBTT is non-zero per household.

"Equal" allows float32 rounding: 64 float32 ulps of the largest magnitude
compared, per household.
"""

from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import policyengine_uk
from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.variables.contrib.policyengine.pre_budget_change_household_tax import (
    PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES,
)
from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES
from policyengine_uk.variables.gov.hmrc.household_tax import HOUSEHOLD_TAX_VARIABLES

PARTITION_PATH = (
    Path(policyengine_uk.__file__).parent / "data" / "fiscal_partition.yaml"
)
MODEL_LISTS = {
    "gov_tax": GOV_TAX_VARIABLES,
    "household_tax": HOUSEHOLD_TAX_VARIABLES,
    "pre_budget_change_household_tax": PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES,
}
EXCLUSION_KINDS = {
    "component",
    "measure_within",
    "composite",
    "duplicate",
    "baseline_measure",
}
ULPS = 64
ALWAYS = "2000-01-01.2100-12-31"


@lru_cache(maxsize=None)
def partition() -> dict:
    return yaml.safe_load(PARTITION_PATH.read_text())


def heads() -> list:
    return partition()["tax_heads"]


def head_by_id() -> dict:
    return {head["id"]: head for head in heads()}


def heads_of(total: str) -> list:
    return [head for head in heads() if total in head["totals"]]


def tolerance(*arrays) -> np.ndarray:
    magnitude = np.max(np.abs(np.stack(arrays)), axis=0)
    return ULPS * np.spacing(magnitude.astype(np.float32)).astype(np.float64)


# 1. Schema


def test_partition_schema():
    p = partition()
    assert p["schema_version"] == 1
    totals = set(p["totals"])
    assert totals == set(MODEL_LISTS)
    ids = [head["id"] for head in heads()]
    variables = [head["variable"] for head in heads()]
    assert len(ids) == len(set(ids)), "duplicate head id"
    assert len(variables) == len(set(variables)), "a variable is in two heads"
    for head in heads():
        variable = system.variables[head["variable"]]
        assert head["entity"] == variable.entity.key, head["id"]
        assert set(head["totals"]) <= totals, head["id"]
        assert head["sign"] in {"nonnegative", "any"}, head["id"]
        assert head.get("zero_at_baseline", "expected") == "expected", head["id"]
        assert head["obr_line"], head["id"]
        assert head["report_group"], head["id"]
        for read in head.get("reads", []):
            assert read["head"] in head_by_id(), (head["id"], read)
    excluded = [x["variable"] for x in p["exclusions"]]
    assert len(excluded) == len(set(excluded)), "duplicate exclusion"
    assert not set(excluded) & set(variables), "a head variable is also excluded"
    for x in p["exclusions"]:
        assert x["variable"] in system.variables, x
        assert x["kind"] in EXCLUSION_KINDS, x
        if x["kind"] == "composite":
            assert set(x["spans"]) <= set(ids), x
        else:
            assert x["head"] in ids, x
    for total, spec in p["totals"].items():
        for switch, dropped in spec.get("dropped_when", {}).items():
            system.parameters.get_child(switch)
            assert set(dropped) <= {h["variable"] for h in heads_of(total)}
    for guard in p["overlap_guards"]:
        assert set(guard["heads"]) <= set(ids), guard["id"]
    assert p["model_double_counts"] == []


# 2. Differential against the model's lists


@pytest.mark.parametrize("total", sorted(MODEL_LISTS))
def test_partition_heads_are_the_variables_each_total_sums(total):
    listed = MODEL_LISTS[total]
    assert len(listed) == len(set(listed)), f"{total} lists a variable twice"
    specified = {head["variable"] for head in heads_of(total)}
    assert set(listed) == specified, (
        f"{total}: listed but not a head: {sorted(set(listed) - specified)}; "
        f"a head of it but not listed: {sorted(specified - set(listed))}"
    )
    excluded = {x["variable"] for x in partition()["exclusions"]}
    assert not set(listed) & excluded


# Population for the traced and perturbation tests: every nation, buyers of
# property in each, shareholders, a self-employed person with gains and a
# student loan, a two-adult household, an owner liable for the high value
# council tax surcharge, and an over-75 pensioner (the TV licence route).
# shareholding is set directly: derived from corporate wealth, it would split
# all UK corporate taxes across these few households, and values in the
# billions leave float32 too coarse to see a 1,024 change.

YEAR = 2028
PEOPLE = {
    "london_buyer": {"age": 45, "employment_income": 90_000},
    "welsh_buyer": {"age": 35, "employment_income": 40_000},
    "scottish_buyer": {"age": 50, "employment_income": 60_000},
    "ni_earner": {"age": 40, "employment_income": 30_000},
    "ni_partner": {"age": 38, "employment_income": 15_000},
    "self_employed": {
        "age": 33,
        "self_employment_income": 45_000,
        "capital_gains": 25_000,
        "student_loan_plan": "PLAN_2",
        "employment_income": 10_000,
    },
    "pensioner": {"age": 80},
}
HOUSEHOLDS = {
    "london": {
        "members": ["london_buyer"],
        "region": "LONDON",
        "main_residential_property_purchased": 600_000,
        "additional_residential_property_purchased": 300_000,
        "non_residential_property_purchased": 200_000,
        "shareholding": 1e-6,
        "council_tax": 2_000,
        "consumption": 40_000,
        "petrol_litres": 900,
        "tenure_type": "OWNED_WITH_MORTGAGE",
        "main_residence_value": 3_000_000,
    },
    "wales": {
        "members": ["welsh_buyer"],
        "region": "WALES",
        "main_residential_property_purchased": 400_000,
        "council_tax": 1_800,
        "consumption": 25_000,
    },
    "scotland": {
        "members": ["scottish_buyer"],
        "region": "SCOTLAND",
        "main_residential_property_purchased": 450_000,
        "shareholding": 1e-7,
        "council_tax": 1_700,
        "consumption": 30_000,
    },
    "northern_ireland": {
        "members": ["ni_earner", "ni_partner"],
        "region": "NORTHERN_IRELAND",
        "main_residential_property_purchased": 250_000,
        "domestic_rates": 1_200,
        "consumption": 28_000,
    },
    "north_west": {
        "members": ["self_employed"],
        "region": "NORTH_WEST",
        "shareholding": 4e-8,
        "council_tax": 1_600,
        "consumption": 20_000,
        "petrol_litres": 1_200,
    },
    "pensioner": {
        "members": ["pensioner"],
        "region": "NORTH_EAST",
        "council_tax": 1_400,
        "consumption": 12_000,
    },
}


def fixed_situation(year: int = YEAR) -> dict:
    people = {
        name: {key: {year: value} for key, value in inputs.items()}
        for name, inputs in PEOPLE.items()
    }
    households, benunits = {}, {}
    for name, inputs in HOUSEHOLDS.items():
        members = inputs["members"]
        households[name] = {
            "members": members,
            **{key: {year: value} for key, value in inputs.items() if key != "members"},
        }
        benunits[f"{name}_benunit"] = {"members": members}
    return {"people": people, "benunits": benunits, "households": households}


def household_values(sim: Simulation, variable: str, year: int) -> np.ndarray:
    """A variable's annual value per household (person values summed)."""
    entity = system.variables[variable].entity.key
    if entity == "household":
        values = sim.calculate(variable, year)
    else:
        values = sim.map_result(
            sim.calculate(variable, year), entity, "household", how="sum"
        )
    return np.asarray(values, dtype=np.float64)


# 3. Overlap guard on the traced dependency graph


@lru_cache(maxsize=None)
def traced_reads() -> dict:
    """Variable name -> names of the variables it reads, at current law."""
    sim = Simulation(situation=fixed_situation())
    sim.trace = True
    for head in heads():
        sim.calculate(head["variable"], YEAR)
    for total in MODEL_LISTS:
        sim.calculate(total, YEAR)
    children = defaultdict(set)

    def walk(node):
        for child in node.children:
            children[node.name].add(child.name)
            walk(child)

    for tree in sim.tracer.trees:
        walk(tree)
    return dict(children)


def reached_from(variable: str) -> set:
    children, seen, stack = traced_reads(), set(), [variable]
    while stack:
        for child in children.get(stack.pop(), ()):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


@pytest.mark.parametrize("total", sorted(MODEL_LISTS))
def test_no_head_reaches_another_head_of_its_total_undeclared(total):
    by_variable = {head["variable"]: head for head in heads_of(total)}
    for variable, head in by_variable.items():
        reached = reached_from(variable) & (set(by_variable) - {variable})
        declared = {
            head_by_id()[read["head"]]["variable"] for read in head.get("reads", [])
        }
        undeclared = reached - declared
        assert not undeclared, (
            f"{total}: {variable} reaches {sorted(undeclared)}, which {total} "
            "also sums; that double counts unless it is an eligibility read "
            "declared under the head's reads"
        )


def test_declared_reads_occur():
    for head in heads():
        for read in head.get("reads", []):
            target = head_by_id()[read["head"]]["variable"]
            assert target in reached_from(head["variable"]), (
                f"{head['id']} declares a read of {read['head']} that no "
                "longer happens; remove it"
            )


def test_exclusions_sit_where_the_partition_says():
    head_variables = {head["variable"] for head in heads()}
    for x in partition()["exclusions"]:
        readers = {v for v in head_variables if x["variable"] in reached_from(v)}
        if x["kind"] in ("component", "baseline_measure"):
            owner = head_by_id()[x["head"]]["variable"]
            assert owner in readers, f"{x['variable']} is not inside {owner}"
        else:
            assert not readers, (
                f"{x['variable']} ({x['kind']}) is read by heads {sorted(readers)}"
            )


# 4. Coefficient one


DELTA = 1_024.0


@lru_cache(maxsize=None)
def baseline_values() -> dict:
    sim = Simulation(situation=fixed_situation())
    names = [head["variable"] for head in heads()] + list(MODEL_LISTS)
    return {name: household_values(sim, name, YEAR) for name in names}


@lru_cache(maxsize=None)
def baseline_entity_values(variable: str) -> dict:
    """A head's baseline values at its own entity, by period."""
    sim = Simulation(situation=fixed_situation())
    if system.variables[variable].definition_period == "month":
        periods = [f"{YEAR}-{month:02d}" for month in range(1, 13)]
    else:
        periods = [str(YEAR)]
    return {
        period: np.asarray(sim.calculate(variable, period), dtype=np.float64)
        for period in periods
    }


def raise_head(sim: Simulation, variable: str, delta: float) -> None:
    """Set a head to its baseline value plus delta a year, per member."""
    values = baseline_entity_values(variable)
    for period, base in values.items():
        sim.set_input(variable, period, base + delta / len(values))


def members_per_household(sim: Simulation, variable: str) -> np.ndarray:
    if system.variables[variable].entity.key == "household":
        return np.ones(len(HOUSEHOLDS))
    return np.asarray(sim.populations["household"].nb_persons(), dtype=float)


@pytest.mark.parametrize("head_id", [head["id"] for head in heads()])
def test_each_head_enters_its_totals_once(head_id):
    head = head_by_id()[head_id]
    variable = head["variable"]
    base = baseline_values()
    sim = Simulation(situation=fixed_situation())
    raise_head(sim, variable, DELTA)
    after = {name: household_values(sim, name, YEAR) for name in base}
    step = DELTA * members_per_household(sim, variable)

    own_tolerance = tolerance(after[variable], base[variable])
    np.testing.assert_array_less(
        np.abs(after[variable] - base[variable] - step), own_tolerance + 1e-9
    )
    for total in head["totals"]:
        moved = after[total] - base[total]
        # Keep the population's magnitudes small enough that float32 can
        # resolve the step; otherwise this test would pass vacuously.
        assert (tolerance(after[total], base[total]) < DELTA / 8).all(), total
        np.testing.assert_array_less(
            np.abs(moved - step),
            tolerance(after[total], base[total]) + 1e-9,
            err_msg=f"{total} moved by {moved} when {variable} rose by {step}",
        )
        for other in heads_of(total):
            if other["id"] == head_id:
                continue
            name = other["variable"]
            np.testing.assert_array_less(
                np.abs(after[name] - base[name]),
                tolerance(after[name], base[name]) + 1e-9,
                err_msg=f"raising {variable} moved {name}, also in {total}",
            )
    for total in MODEL_LISTS:
        parts = sum(after[h["variable"]] for h in heads_of(total))
        np.testing.assert_array_less(
            np.abs(after[total] - parts),
            tolerance(after[total], parts) + 1e-9,
        )


# 5. Identity, signs and zero-at-baseline on random households


SCENARIOS = {
    "baseline": None,
    "sdlt_abolished": {"gov.hmrc.stamp_duty.abolish": {ALWAYS: True}},
    "council_tax_abolished": {"gov.contrib.abolish_council_tax": {ALWAYS: True}},
}
REGIONS = ["LONDON", "NORTH_WEST", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
amount = lambda top: st.one_of(st.just(0.0), st.floats(1_000, top))  # noqa: E731
random_household = st.fixed_dictionaries(
    {
        "region": st.sampled_from(REGIONS),
        "age": st.integers(18, 90),
        "employment_income": amount(250_000),
        "self_employment_income": amount(100_000),
        "capital_gains": amount(200_000),
        "main_residential_property_purchased": amount(3_000_000),
        "shareholding": st.one_of(st.just(0.0), st.floats(1e-9, 1e-5)),
        "council_tax": amount(5_000),
        "consumption": amount(80_000),
        "main_residence_value": amount(5_000_000),
        "owner": st.booleans(),
    }
)
PERSON_INPUTS = {"age", "employment_income", "self_employment_income", "capital_gains"}


def random_situation(drawn: list, year: int) -> dict:
    people, benunits, households = {}, {}, {}
    for i, inputs in enumerate(drawn):
        person = f"person_{i}"
        people[person] = {key: {year: inputs[key]} for key in PERSON_INPUTS}
        benunits[f"benunit_{i}"] = {"members": [person]}
        household = {
            key: {year: value}
            for key, value in inputs.items()
            if key not in PERSON_INPUTS and key != "owner"
        }
        household["tenure_type"] = {
            year: "OWNED_OUTRIGHT" if inputs["owner"] else "RENT_PRIVATELY"
        }
        households[f"household_{i}"] = {"members": [person], **household}
    return {"people": people, "benunits": benunits, "households": households}


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    drawn=st.lists(random_household, min_size=2, max_size=2),
    year=st.integers(2025, 2030),
)
def test_each_total_is_the_sum_of_its_heads(drawn, year):
    for scenario, reform in SCENARIOS.items():
        sim = Simulation(situation=random_situation(drawn, year), reform=reform)
        values = {h["id"]: household_values(sim, h["variable"], year) for h in heads()}
        for total, spec in partition()["totals"].items():
            dropped = set()
            for switch, names in spec.get("dropped_when", {}).items():
                if reform and switch in reform:
                    dropped |= set(names)
            parts = [
                values[h["id"]] for h in heads_of(total) if h["variable"] not in dropped
            ]
            value = household_values(sim, total, year)
            parts_sum = np.sum(parts, axis=0)
            np.testing.assert_array_less(
                np.abs(value - parts_sum),
                tolerance(value, np.sum(np.abs(parts), axis=0)) + 1e-9,
                err_msg=f"{scenario}: {total} is not the sum of its heads",
            )
        property_taxes = np.stack(
            [
                values[i] != 0
                for i in (
                    "sdlt_household",
                    "land_transaction_tax",
                    "land_and_buildings_transaction_tax",
                )
            ]
        )
        assert (property_taxes.sum(axis=0) <= 1).all(), scenario
        if scenario == "baseline":
            for head in heads():
                if head["sign"] == "nonnegative":
                    assert (values[head["id"]] >= 0).all(), head["id"]
                if head.get("zero_at_baseline") == "expected":
                    np.testing.assert_array_equal(values[head["id"]], 0, head["id"])
        if scenario == "sdlt_abolished":
            np.testing.assert_array_equal(values["sdlt_household"], 0)
            np.testing.assert_array_equal(values["sdlt_corporate"], 0)

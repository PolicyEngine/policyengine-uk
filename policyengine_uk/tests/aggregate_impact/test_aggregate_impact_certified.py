"""The aggregate-impact measurement on the certified dataset.

One year, the counted-once check on every tax component plus a few benefits.
Runs where microsimulation tests run (see conftest's data mode).
"""

import dataclasses

import numpy as np
import pytest

from policyengine_uk.utils.aggregate_impact.measure import measure
from policyengine_uk.utils.aggregate_impact.partition import (
    default_partition_path,
    load_partition,
)
from policyengine_uk.utils.aggregate_impact.spec import load_spec

pytestmark = pytest.mark.microsimulation

YEAR = 2026
# Universal Credit deducts income tax and National Insurance on Statutory Sick
# Pay (taxable_employment_income adds employment_benefits) but does not count
# the pay itself as earnings (uc_individual_earned_income_before_mif), so UC
# rises when SSP does. When that is fixed this test fails: remove the entry.
KNOWN_RISING_WITH_INCOME = {"statutory_sick_pay"}
SPENDING_SAMPLE = {
    "state_pension",
    "universal_credit",
    "child_benefit",
    "statutory_sick_pay",
}


@pytest.fixture(scope="module")
def measured():
    from policyengine_uk import Microsimulation

    sim = Microsimulation()
    dataset = sim.dataset
    partition = load_partition(default_partition_path())
    spec = dataclasses.replace(
        load_spec(), first_year=YEAR, last_year=YEAR, guard_year=YEAR
    )
    tax_components = {h.variable for h in partition.tax_heads} | {
        d.variable for d in partition.double_counts
    }
    result, households = measure(
        sim,
        lambda reform=None: Microsimulation(dataset=dataset, reform=reform),
        partition,
        spec,
        label="test",
        guard_variables=tax_components | SPENDING_SAMPLE,
    )
    return result, households, partition, Microsimulation(dataset=dataset)


def checks(result, prefix):
    return [c for c in result["checks"] if c["id"].startswith(prefix)]


def test_accounting_identities_and_closure_hold(measured):
    result, _, _, _ = measured
    assert result["status"] == "ok"
    for prefix in (
        "closure",
        "identity:",
        "finite:",
        "weights:",
        "bounds:",
        "determinism:",
    ):
        failing = [c for c in checks(result, prefix) if c["status"] != "pass"]
        assert failing == [], failing


def test_every_tax_component_is_counted_exactly_once(measured):
    result, _, partition, _ = measured
    guard = result["guard"]
    assert guard["status"] == "ran" and guard["reset_reproduces_baseline"]
    rows = {r["variable"]: r for r in guard["components"]}
    for head in partition.tax_heads:
        row = rows[head.variable]
        assert row["status"] == "pass", row
        for total, k in row["coefficients"].items():
            assert k == pytest.approx(1, abs=1e-3), (head.id, total)


def test_declared_double_counts_are_still_double_counted_by_the_model(measured):
    result, _, partition, _ = measured
    rows = {r["variable"]: r for r in result["guard"]["components"]}
    for declared in partition.double_counts:
        present = next(
            d
            for d in result["guard"]["double_counts"]
            if d["variable"] == declared.variable
        )
        assert present["status"] == "pass", present
        for total in declared.totals:
            assert rows[declared.variable]["model_coefficients"][
                total
            ] == pytest.approx(2, abs=1e-3)


def test_spending_never_rises_by_more_than_is_added_except_known_defects(measured):
    result, _, _, _ = measured
    rows = {r["variable"]: r for r in result["guard"]["components"]}
    for variable in SPENDING_SAMPLE:
        row = rows[variable]
        if variable in KNOWN_RISING_WITH_INCOME:
            assert (
                row["status"] == "fail"
                and 1 < row["coefficients"]["gov_spending"] < 1.05
            )
        else:
            assert row["status"] == "pass", row


def test_head_totals_agree_with_the_model_weighted_sums(measured):
    result, _, partition, sim = measured
    metrics = {m["id"]: m for m in result["metrics"]}
    for head in partition.heads:
        section = "receipts" if head.kind == "tax" else "spending"
        ours = metrics[f"{section}.{head.id}"]["values"][str(YEAR)]
        theirs = float(sim.calculate(head.variable, YEAR).sum())
        assert ours == pytest.approx(theirs, rel=1e-6, abs=1e3), head.id
    receipts = metrics["balance.receipts"]["values"][str(YEAR)]
    model = metrics["model.gov_tax"]["values"][str(YEAR)]
    double_counted = sum(
        metrics[f"double_counts.{d.variable}"]["values"][str(YEAR)]
        for d in partition.double_counts
        if "gov_tax" in d.totals
    )
    assert receipts + double_counted == pytest.approx(model, rel=1e-9)


def test_household_detail_is_complete(measured):
    _, households, _, _ = measured
    columns = households[str(YEAR)]
    n = len(columns["household_id"])
    assert all(len(v) == n for v in columns.values())
    assert np.all(np.isfinite(columns["income"]))
    assert set(np.unique(columns["decile"])) <= set(range(-1, 11))

"""Dated parameter views survive the UK public cache-reset lifecycle.

These are behavior-preservation controls for an ownership refactor. The
separate architecture gate checks that country code leaves Core cache fields
to Core; no tax-policy correction is asserted by these tests.
"""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import pytest
from policyengine_core.parameters import ParameterNode
from policyengine_core.reforms import Reform
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk import tax_benefit_system as tbs_module
from policyengine_uk.entities import BenUnit, Household, Person
from policyengine_uk.utils.dated_reforms import read_parameter_changes


def parameter_tree():
    def branch(value):
        return {"nested": {"amount": {"values": {"2025-01-01": value}}}}

    return ParameterNode(
        "",
        data={"branch": branch(11), "baseline": {"branch": branch(23)}},
    )


def small_system():
    system = CountryTaxBenefitSystem.__new__(CountryTaxBenefitSystem)
    TaxBenefitSystem.__init__(system, entities=[Person, BenUnit, Household])
    system.modify_parameters(lambda _: parameter_tree())
    system.dated_assignments = []
    system.legacy_overrides = []
    system._projected_timelines = {}
    system._raw_parameters = None
    system._parameters_before_reset = None
    system.capital_gains_projection = None
    return system


def readings(system):
    root = system.parameters
    return (
        system.get_parameters_at_instant("2026-01-01").branch.nested.amount,
        root("2026-01-01").branch.nested.amount,
        root.branch("2026-01-01").nested.amount,
        root.branch.nested("2026-01-01").amount,
        root.baseline("2026-01-01").branch.nested.amount,
        root.baseline.branch.nested("2026-01-01").amount,
    )


def test_reset_refreshes_system_and_every_descendant_without_replacing_tree():
    system = small_system()
    root = system.parameters
    leaf = root.branch.nested.amount
    baseline = root.baseline
    assert readings(system) == (11, 11, 11, 11, 23, 23)
    old_view = system.get_parameters_at_instant("2026-01-01")
    # A structural modifier can edit a timeline in place before asking for a
    # reset. This deliberately does not invoke Parameter.update's own clearing.
    leaf.values_list[0].value = 31
    root.baseline.branch.nested.amount.values_list[0].value = 47
    system.reset_parameter_caches()
    assert readings(system) == (31, 31, 31, 31, 47, 47)
    assert system.parameters is root
    assert root.branch.nested.amount is leaf
    assert root.baseline is baseline
    assert system.get_parameters_at_instant("2026-01-01") is not old_view


def test_reset_keeps_an_actual_reforms_current_edits_and_baseline_separate():
    original = small_system()

    class Changed(Reform):
        def apply(self):
            self.parameters.branch.nested.amount.update(period="2026", value=31)

    reformed = Changed(original)
    root = reformed.parameters
    assert readings(original) == (11, 11, 11, 11, 23, 23)
    assert readings(reformed) == (31, 31, 31, 31, 23, 23)
    CountryTaxBenefitSystem.reset_parameter_caches(reformed)
    assert reformed.parameters is root
    assert readings(reformed) == (31, 31, 31, 31, 23, 23)
    assert readings(original) == (11, 11, 11, 11, 23, 23)


def test_resets_can_repeat_inside_a_public_parameter_modifier():
    system = small_system()
    root = system.parameters
    assert readings(system)[0] == 11

    def modifier(parameters):
        parameters.branch.nested.amount.values_list[0].value = 37
        system.reset_parameter_caches()
        system.reset_parameter_caches()
        return parameters

    TaxBenefitSystem.modify_parameters(system, modifier)
    assert system.parameters is root
    assert readings(system) == (37, 37, 37, 37, 23, 23)


def test_cloned_systems_clear_only_their_own_dated_views_in_threads():
    original = small_system()
    assert readings(original)[0] == 11

    def change(amount):
        clone = original.clone()
        assert readings(clone)[0] == 11
        clone.parameters.branch.nested.amount.values_list[0].value = amount
        clone.reset_parameter_caches()
        return readings(clone), clone.parameters

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(change, [29, 31, 37]))
    for (values, root), amount in zip(results, [29, 31, 37]):
        assert values == (amount, amount, amount, amount, 23, 23)
        assert root is not original.parameters
    assert readings(original) == (11, 11, 11, 11, 23, 23)


@pytest.mark.parametrize("route", ["process", "assignments"])
def test_a_failed_rebuild_restores_tree_timelines_and_readable_views(
    monkeypatch, route
):
    system = small_system()
    root = system.parameters
    timelines = system._projected_timelines
    original_values = readings(system)

    def fail(*args, **kwargs):
        raise RuntimeError("deliberate processor failure")

    monkeypatch.setattr(tbs_module, "_rebuilt_parameters_cache", OrderedDict())
    monkeypatch.setattr(tbs_module, "process_parameter_tree", fail)
    with pytest.raises(RuntimeError, match="deliberate processor failure"):
        if route == "process":
            system.process_parameters()
        else:
            # Use a real statutory path so assignment validation succeeds;
            # the injected processor failure must exercise the rollback.
            system.apply_parameter_assignments(
                read_parameter_changes(
                    {"gov.hmrc.income_tax.rates.uk[0].rate": {"2026": 0.31}}
                )
            )
    assert system.parameters is root
    assert system._projected_timelines is timelines
    assert system._raw_parameters is None
    assert system.dated_assignments == []
    assert readings(system) == original_values


def test_real_cold_and_warm_uk_construction_keeps_entities_and_default_tax(
    monkeypatch,
):
    for name in (
        "_processed_parameters_cache",
        "_statutory_parameters_cache",
        "_projected_timelines_cache",
    ):
        monkeypatch.setattr(tbs_module, name, None)
    cold = CountryTaxBenefitSystem()
    warm = CountryTaxBenefitSystem()
    assert cold.parameters is not warm.parameters
    path = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
    for system in (cold, warm):
        assert system.parameters.get_child(path)("2026-01-01") == 12_570
        for entity in system.entities:
            assert entity.get_variable("age") is system.get_variable("age")
    situation = {
        "people": {"person": {"age": {2026: 40}, "employment_income": {2026: 30_000}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    for system in (cold, warm):
        monkeypatch.setattr(
            "policyengine_uk.simulation.CountryTaxBenefitSystem", system.clone
        )
        simulation = Simulation(situation=situation)
        assert simulation.calculate("income_tax", 2026).tolist() == pytest.approx(
            [3486]
        )


def test_real_reload_and_processing_keep_structural_nodes_and_baseline():
    system = CountryTaxBenefitSystem()
    added = ParameterNode(
        "extra_structure", data={"amount": {"values": {"2025-01-01": 17}}}
    )
    system.parameters.add_child("extra_structure", added)
    path = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
    assert system.parameters.get_child(path)("2026-01-01") == 12_570
    system.get_parameters_at_instant("2026-01-01")
    system.reset_parameters()
    system.process_parameters()
    assert system.parameters.extra_structure("2026-01-01").amount == 17
    assert system.parameters.get_child(path)("2026-01-01") == 12_570
    assert system.parameters.baseline.get_child(path)("2026-01-01") == 12_570

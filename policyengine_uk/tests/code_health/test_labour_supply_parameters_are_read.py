"""Every labour supply parameter must be read by a formula or by the dynamics.

``gov.simulation.labour_supply_responses.obr_elasticities`` ("Use the OBR's
progression elasticities for the labour supply responses") stayed in the tree
from October 2024 to October 2026 although nothing read it, so setting it
changed no output (#2412). The OBR elasticities are applied by
``Simulation.apply_dynamics`` when ``gov.dynamic.obr_labour_supply_assumptions``
is on.

This test runs both labour supply response paths on a small household and
records every parameter read along the way:

- the elasticity-based response (``employment_income_behavioral_response``)
  with non-zero elasticities, so that it gets past its early return and reads
  the bounds too;
- the OBR dynamics (``Simulation.apply_dynamics``) with the OBR assumptions on.

It fails if a parameter under ``GUARDED_PREFIXES`` was never read. A new
parameter there needs a reader. If it is read only under a condition this
scenario does not meet, extend the scenario.

Reads are recorded on the parameter tree itself, so a read counts whether a
formula makes it through ``parameters(period)`` or the dynamics make it through
``sim.tax_benefit_system.parameters``. Three kinds of read are recorded: an
attribute or item of a node at an instant that holds a value (not a node), a
direct call of a parameter or scale (``parameter(year)``), and fancy indexing
of a node at an instant (``node[array]``), which reads every leaf under that
node. A read straight from a node's ``_children`` is not recorded.

Building a node at an instant does not count its children as read. A node may
build a child when it is first read: ``__getattr__`` then returns the child,
and ``__getattribute__`` returns it after that, so both are recorded. Building
a scale reads its brackets, which records the paths of the brackets but not the
path of the scale.

A control parameter that nothing reads is added to the tree of both runs, and
every child of its node is built during the recording. It must stay unread,
which shows the recorder does not count a parameter just because it is in the
tree or has been built.
"""

import contextlib

import numpy as np
import pytest
from policyengine_core.parameters import (
    Parameter,
    ParameterNode,
    ParameterNodeAtInstant,
    ParameterScale,
)
from policyengine_core.parameters.at_instant_like import AtInstantLike

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
    canonicalize_lsr_parameter_path,
)

GUARDED_PREFIXES = (
    "gov.simulation.labour_supply_responses",
    "gov.dynamic",
)
YEAR = 2025
BASIC_RATE_RISE = {"gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}}
ELASTICITIES = {
    "gov.simulation.labour_supply_responses.income_elasticity": {str(YEAR): -0.05},
    "gov.simulation.labour_supply_responses.substitution_elasticity": {str(YEAR): 0.25},
}
OBR_ASSUMPTIONS = {"gov.dynamic.obr_labour_supply_assumptions": {str(YEAR): True}}
CONTROL_NODE = "gov.simulation.labour_supply_responses"
CONTROL = f"{CONTROL_NODE}.unread_control"


def leaf_paths(node: ParameterNode, path: str) -> set:
    """The path of every parameter and scale under ``node``."""
    leaves = set()
    for key, child in node.children.items():
        child_path = f"{path}.{key}"
        if isinstance(child, ParameterNode):
            leaves |= leaf_paths(child, child_path)
        else:
            leaves.add(child_path)
    return leaves


def _leaves_at_instant(node: ParameterNodeAtInstant, path: str):
    for key, child in node._children.items():
        if isinstance(child, ParameterNodeAtInstant):
            yield from _leaves_at_instant(child, f"{path}.{key}")
        else:
            yield f"{path}.{key}"


@contextlib.contextmanager
def record_parameter_reads():
    """Record the paths of the kinds of parameter read listed above."""
    reads = set()
    getattribute = ParameterNodeAtInstant.__getattribute__
    getattr_fallback = ParameterNodeAtInstant.__getattr__
    getitem = ParameterNodeAtInstant.__getitem__
    get_at_instant = AtInstantLike.get_at_instant

    def record_attribute_read(self, key, value):
        if not key.startswith("_") and not isinstance(value, ParameterNodeAtInstant):
            reads.add(f"{getattribute(self, '_name')}.{key}")

    def recording_getattribute(self, key):
        value = getattribute(self, key)
        if key in getattribute(self, "__dict__"):
            record_attribute_read(self, key, value)
        return value

    def recording_getattr(self, key):
        value = getattr_fallback(self, key)
        record_attribute_read(self, key, value)
        return value

    def recording_getitem(self, key):
        value = getitem(self, key)
        name = getattribute(self, "_name")
        if not isinstance(key, str):
            # Fancy indexing: the vectorial node reads the whole subtree.
            reads.update(_leaves_at_instant(self, name))
        elif not isinstance(value, ParameterNodeAtInstant):
            reads.add(f"{name}.{key}")
        return value

    def recording_get_at_instant(self, instant):
        if isinstance(self, (Parameter, ParameterScale)):
            reads.add(self.name)
        return get_at_instant(self, instant)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            ParameterNodeAtInstant, "__getattribute__", recording_getattribute
        )
        patch.setattr(ParameterNodeAtInstant, "__getattr__", recording_getattr)
        patch.setattr(ParameterNodeAtInstant, "__getitem__", recording_getitem)
        patch.setattr(AtInstantLike, "get_at_instant", recording_get_at_instant)
        yield reads


def _couple_with_child() -> dict:
    members = ["adult_1", "adult_2", "child"]
    return {
        "people": {
            "adult_1": {"age": 45, "employment_income": 60_000, "hours_worked": 1_800},
            "adult_2": {"age": 43, "employment_income": 18_000, "hours_worked": 1_000},
            "child": {"age": 7},
        },
        "benunits": {"benunit": {"members": members}},
        "households": {"household": {"members": members}},
    }


def _add_unread_control(simulation) -> None:
    node = simulation.tax_benefit_system.parameters.get_child(CONTROL_NODE)
    node.add_child(
        "unread_control",
        Parameter(
            CONTROL,
            {
                "description": "A parameter nothing reads.",
                "values": {"2000-01-01": 1},
            },
        ),
    )
    simulation.tax_benefit_system.reset_parameter_caches()


@pytest.fixture(scope="module")
def labour_supply_run():
    """Run both labour supply response paths and record the parameters read."""
    formula_sim = Simulation(
        situation=_couple_with_child(),
        scenario=Scenario(parameter_changes={**ELASTICITIES, **BASIC_RATE_RISE}),
    )
    dynamics_sim = Microsimulation(
        situation=_couple_with_child(),
        scenario=Scenario(parameter_changes={**OBR_ASSUMPTIONS, **BASIC_RATE_RISE}),
    )
    dynamics_sim.baseline = Microsimulation(situation=_couple_with_child())
    simulations = (formula_sim, dynamics_sim)
    for simulation in simulations:
        _add_unread_control(simulation)

    with record_parameter_reads() as reads:
        response = formula_sim.calculate("employment_income_behavioral_response", YEAR)
        dynamics = dynamics_sim.apply_dynamics(YEAR)
        for simulation in simulations:
            # Build the control, which a node may otherwise leave unbuilt.
            simulation.tax_benefit_system.parameters.get_child(CONTROL_NODE)(
                f"{YEAR}-01-01"
            )._children

    # Both paths ran in full: the formula measured a response, which it does
    # only after its early returns (its measurement branches are not kept),
    # and the dynamics returned results.
    assert (np.asarray(response) != 0).any()
    assert dynamics is not None
    return simulations, {canonicalize_lsr_parameter_path(read) for read in reads}


@pytest.mark.parametrize("prefix", GUARDED_PREFIXES)
def test_every_labour_supply_parameter_is_read(prefix, labour_supply_run):
    _, reads = labour_supply_run
    parameters = CountryTaxBenefitSystem().parameters
    leaves = leaf_paths(parameters.get_child(prefix), prefix)
    assert leaves, f"No parameters found under {prefix}."

    unread = sorted(leaves - reads)
    assert not unread, (
        f"No formula or dynamics read these parameters under {prefix}: "
        f"{unread}. Setting them changes no output. Delete them or read them; "
        "if they are read only under a condition, extend the scenario in "
        "this test to meet it."
    )


def test_recorder_does_not_count_a_parameter_nothing_reads(labour_supply_run):
    simulations, reads = labour_supply_run
    for simulation in simulations:
        # The control was in the tree for the whole run.
        assert simulation.tax_benefit_system.parameters.get_child(CONTROL)
    assert CONTROL not in reads


def test_recorder_counts_each_kind_of_read():
    getattr_fallback = ParameterNodeAtInstant.__getattr__
    getitem = ParameterNodeAtInstant.__getitem__
    get_at_instant = AtInstantLike.get_at_instant
    leaf = {"values": {"2000-01-01": 1}}
    root = ParameterNode(
        "root",
        data={
            "by_attribute": leaf,
            "by_attribute_again": leaf,
            "by_item": leaf,
            "by_call": leaf,
            "unread": leaf,
            "vector": {"a": leaf, "b": leaf},
        },
    )
    # Read before recording starts, so the reads below use what these leave in
    # the cached node: ``by_attribute_again`` is already an attribute, which
    # does not reach ``__getattr__``, and ``vector`` already has its vectorial
    # node, so fancy indexing does not read each child by name.
    before_recording = root("2020-01-01")
    before_recording.by_attribute_again
    before_recording.vector[np.array(["a", "a"])]
    with record_parameter_reads() as reads:
        at_instant = root("2020-01-01")
        assert reads == set(), "Building a node at an instant is not a read."
        at_instant.by_attribute
        at_instant.by_attribute_again
        at_instant["by_item"]
        root.by_call("2020-01-01")
        at_instant.vector[np.array(["a", "a"])]

    assert reads == {
        "root.by_attribute",
        "root.by_attribute_again",
        "root.by_item",
        "root.by_call",
        "root.vector.a",
        "root.vector.b",
    }
    # The recorder leaves the classes as it found them.
    assert "__getattribute__" not in ParameterNodeAtInstant.__dict__
    assert ParameterNodeAtInstant.__getattr__ is getattr_fallback
    assert ParameterNodeAtInstant.__getitem__ is getitem
    assert AtInstantLike.get_at_instant is get_at_instant

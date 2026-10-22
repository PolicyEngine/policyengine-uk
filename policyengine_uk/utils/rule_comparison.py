"""Whether two tax-benefit systems apply the same rules.

A simulation built without a reform measures behavioural responses against a
copy of itself taken when it was built (its baseline). If its rules still
match that copy's, no reform separates them, so a response measured between
them is exactly zero and need not be measured. Rules change after
construction too: a scenario's modifier, ``apply_reform`` and callers such as
policyengine.py edit parameters in place, so the check compares what the two
systems hold rather than how they were built.

The comparison errs one way only. Systems it calls the same hold the same
parameter timelines and the same variable definitions. Anything it cannot
compare counts as different, which costs a measurement but never skips one
that a reform needs. Two systems loaded separately hold separate copies of
every variable's class and formulas, so they compare as different even when
their rules agree; copies of one system (``clone``) share them.
"""

from typing import Iterable

import numpy as np
from policyengine_core.parameters import Parameter, ParameterNode, ParameterScale

# Variable attributes that change what a variable calculates. The rest
# (labels, documentation, units, references) describe it.
RULE_ATTRIBUTES = (
    "formulas",
    "adds",
    "subtracts",
    "default_value",
    "defined_for",
    "definition_period",
    "end",
    "is_neutralized",
    "possible_values",
    "value_type",
    "uprating",
    "set_input",
    "calculate_output",
    "max_value",
    "min_value",
    "requires_computation_after",
    "is_period_size_independent",
    "quantity_type",
    "baseline_variable",
)


def _equal(value, other) -> bool:
    """Whether two values are the same, strictly: equal and of one type."""
    if value is other:
        return True
    if type(value) is not type(other):
        return False
    if isinstance(value, np.ndarray):
        return value.shape == other.shape and bool(np.array_equal(value, other))
    try:
        result = value == other
    except Exception:
        return False
    return isinstance(result, (bool, np.bool_)) and bool(result)


def same_parameters(tree, other, ignore: Iterable[str] = ()) -> bool:
    """Whether two parameter trees hold the same timelines.

    Every parameter must have the same dated values, read from its own
    ``values_list`` (so no cache is written), with the same effective times,
    and scales the same brackets. Subtrees at the dotted paths in ``ignore``
    are skipped.
    """
    ignore = frozenset(ignore)
    stack = [("", tree, other)]
    while stack:
        path, node, other_node = stack.pop()
        if node is other_node or path in ignore:
            continue
        if type(node) is not type(other_node):
            return False
        if isinstance(node, Parameter):
            values, other_values = node.values_list, other_node.values_list
            if len(values) != len(other_values):
                return False
            for value, other_value in zip(values, other_values):
                if (
                    value.instant_str != other_value.instant_str
                    or not _equal(value.value, other_value.value)
                    or value.metadata.get("effective_time")
                    != other_value.metadata.get("effective_time")
                ):
                    return False
        elif isinstance(node, ParameterScale):
            if len(node.brackets) != len(other_node.brackets) or node.metadata.get(
                "type"
            ) != other_node.metadata.get("type"):
                return False
            stack.extend(
                (f"{path}[{index}]", bracket, other_bracket)
                for index, (bracket, other_bracket) in enumerate(
                    zip(node.brackets, other_node.brackets)
                )
            )
        elif isinstance(node, ParameterNode):
            if node.children.keys() != other_node.children.keys():
                return False
            stack.extend(
                (f"{path}.{key}" if path else key, child, other_node.children[key])
                for key, child in node.children.items()
            )
        else:
            return False
    return True


def same_variables(variables: dict, other: dict) -> bool:
    """Whether two systems' variables calculate the same way.

    The same names, and for each the same class, entity and
    :data:`RULE_ATTRIBUTES` (formulas compared function by function).
    """
    if variables.keys() != other.keys():
        return False
    for name, variable in variables.items():
        other_variable = other[name]
        if variable is other_variable:
            continue
        if type(variable) is not type(other_variable):
            return False
        if getattr(variable.entity, "key", None) != getattr(
            other_variable.entity, "key", None
        ):
            return False
        for attribute in RULE_ATTRIBUTES:
            if not _equal(
                getattr(variable, attribute, None),
                getattr(other_variable, attribute, None),
            ):
                return False
    return True


def same_rules(system, other, ignore_parameters: Iterable[str] = ()) -> bool:
    """Whether two tax-benefit systems apply the same rules.

    The same parameter timelines, apart from the subtrees in
    ``ignore_parameters``, and the same variable definitions.
    """
    if system is other:
        return True
    try:
        return same_parameters(
            system.parameters, other.parameters, ignore_parameters
        ) and same_variables(system.variables, other.variables)
    except Exception:
        return False

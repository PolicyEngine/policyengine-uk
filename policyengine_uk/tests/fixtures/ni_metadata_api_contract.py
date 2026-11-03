"""Source-extracted API contract, not an installed/full API execution.

Country.build_parameters and get_safe_json are copied without body changes from
PolicyEngine/policyengine-api commit 71dba65b3780f0bb4699d4dcbfe179e5f1506c78.
country.py SHA256 cfbb900691d45bd95e05b08e53bf72708ac75ee82d1647c04ff09240a92e61bb;
utils/json.py SHA256 acef75a37b1d90cc52c0bda57db47ffd2348eaa400d4674d244c8090b47ddc61.
https://github.com/PolicyEngine/policyengine-api/blob/71dba65b3780f0bb4699d4dcbfe179e5f1506c78/policyengine_api/country.py#L371
https://github.com/PolicyEngine/policyengine-api/blob/71dba65b3780f0bb4699d4dcbfe179e5f1506c78/policyengine_api/utils/json.py#L34
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

if TYPE_CHECKING:
    from policyengine_api.json_types import JSONValue

from policyengine_core.parameters.operations.get_parameter import get_parameter
from policyengine_core.periods import instant
from policyengine_core.reforms import Reform
from policyengine_core.parameters import (
    Parameter,
    ParameterNode,
    ParameterScale,
    ParameterScaleBracket,
)


def get_safe_json(value: object) -> JSONValue:
    # This function is used when constructing metadata,
    # which will be consumed by JS, hence Infinity, not .inf
    if isinstance(value, (int, float)):
        if value == np.inf:
            return "Infinity"
        if value == -np.inf:
            return "-Infinity"
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return {k: get_safe_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [get_safe_json(v) for v in value]
    return None


def build_parameters(self) -> dict:
    parameters = self.tax_benefit_system.parameters
    parameter_data = {}
    for parameter in parameters.get_descendants():
        if "gov" != parameter.name[:3]:
            continue
        end_name = parameter.name.split(".")[-1]
        if isinstance(parameter, ParameterScale):
            parameter.propagate_units()
            parameter_data[parameter.name] = {
                "type": "parameterNode",
                "parameter": parameter.name,
                "description": parameter.description,
                "label": parameter.metadata.get("label", end_name.replace("_", " ")),
            }
        elif isinstance(parameter, ParameterScaleBracket):
            bracket_index = int(parameter.name[parameter.name.index("[") + 1 : -1])
            # Set the label to 'first bracket' for the first bracket, 'second bracket' for the second, etc.
            bracket_label = f"bracket {bracket_index + 1}"
            parameter_data[parameter.name] = {
                "type": "parameterNode",
                "parameter": parameter.name,
                "description": parameter.description,
                "label": parameter.metadata.get("label", bracket_label),
            }
        elif isinstance(parameter, Parameter):
            parameter_data[parameter.name] = {
                "type": "parameter",
                "parameter": parameter.name,
                "description": parameter.description,
                "label": parameter.metadata.get("label", end_name.replace("_", " ")),
                "unit": parameter.metadata.get("unit"),
                "period": parameter.metadata.get("period"),
                "values": {
                    value_at_instant.instant_str: get_safe_json(value_at_instant.value)
                    for value_at_instant in parameter.values_list
                },
                "economy": parameter.metadata.get("economy", True),
                "household": parameter.metadata.get("household", True),
            }
        elif isinstance(parameters, ParameterNode):
            parameter_data[parameter.name] = {
                "type": "parameterNode",
                "parameter": parameter.name,
                "description": parameter.description,
                "label": parameter.metadata.get("label", end_name.replace("_", " ")),
                "economy": parameter.metadata.get("economy", True),
                "household": parameter.metadata.get("household", True),
            }
    return parameter_data


def _normalize_reform_values(
    self,
    reform: dict,
    system: TaxBenefitSystem,
) -> dict:
    normalized_reform = {}
    for parameter_name, parameter_updates in reform.items():
        parameter = get_parameter(system.parameters, parameter_name)
        normalized_reform[parameter_name] = {}
        for time_period, value in parameter_updates.items():
            node_type = type(parameter.values_list[-1].value)
            if node_type is int:
                node_type = float
            try:
                value = float(value)
            except Exception:
                pass
            normalized_reform[parameter_name][time_period] = node_type(value)
    return normalized_reform


def _apply_reform_to_system(
    self,
    system: TaxBenefitSystem,
    reform: dict,
) -> None:
    for parameter_name, parameter_updates in reform.items():
        parameter = get_parameter(system.parameters, parameter_name)
        for time_period, value in parameter_updates.items():
            start_instant, end_instant = time_period.split(".")
            parameter.update(
                start=instant(start_instant),
                stop=instant(end_instant),
                value=value,
            )


def create_policy_reform(policy_data: dict) -> dict:
    """
    Create a policy reform.

    Args:
        policy_data (dict): The policy data.

    Returns:
        dict: The reform.
    """

    def modify_parameters(parameters: ParameterNode) -> ParameterNode:
        for path, values in policy_data.items():
            node = parameters
            for step in path.split("."):
                if "[" in step:
                    step, index = step.split("[")
                    index = int(index[:-1])
                    node = node.children[step].brackets[index]
                else:
                    node = node.children[step]
            for period, value in values.items():
                start, end = period.split(".")
                node_type = type(node.values_list[-1].value)
                if node_type is int:
                    node_type = float  # '0' is of type int by default, but usually we want to cast to float.
                if node.values_list[-1].value is None:
                    node_type = float
                node.update(
                    start=instant(start),
                    stop=instant(end),
                    value=node_type(value),
                )

        return parameters

    class reform(Reform):
        def apply(self) -> None:
            self.modify_parameters(modify_parameters)

    return reform

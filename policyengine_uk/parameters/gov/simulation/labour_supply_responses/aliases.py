"""Deprecation aliases mirroring the renamed `labour_supply_responses` parameters
under the legacy `labor_supply_responses` path.

`policyengine-app` (legacy) hard-codes
`gov.simulation.labor_supply_responses.{income_elasticity,substitution_elasticity}`
in PolicyRightSidebar.jsx. Without this alias the LSR sliders break the
moment a deployed app rebuilds against this version of policyengine-uk.
The companion app PR (PolicyEngine/policyengine-app#2829) migrates to the
new path; remove this alias once that ships.
"""

from policyengine_core.parameters import ParameterNode


_LEGACY_LSR_PATH = "gov.simulation.labor_supply_responses"
_CANONICAL_LSR_PATH = "gov.simulation.labour_supply_responses"


def canonicalize_lsr_parameter_path(path: str) -> str:
    if path == _LEGACY_LSR_PATH:
        return _CANONICAL_LSR_PATH
    if path.startswith(f"{_LEGACY_LSR_PATH}."):
        return path.replace(_LEGACY_LSR_PATH, _CANONICAL_LSR_PATH, 1)
    return path


def canonicalize_parameter_changes(changes: dict) -> dict:
    """Changes keyed by canonical parameter paths.

    A deprecated alias path names the parameter it copies, the one formulas
    read. Where a path and its alias both appear (two scenarios spelling it
    differently, say), their changes are merged in order, as two changes to
    one path are: dated keys from both are kept, a later key for the same
    period wins, and a value with no period replaces what came before.
    """
    canonical = {}
    for path, value in changes.items():
        name = canonicalize_lsr_parameter_path(path)
        if name not in canonical:
            canonical[name] = value
        elif isinstance(canonical[name], dict) and isinstance(value, dict):
            canonical[name] = {**canonical[name], **value}
        else:
            canonical[name] = value
    return canonical


def add_lsr_deprecation_aliases(parameters: ParameterNode) -> ParameterNode:
    simulation = parameters.gov.simulation
    canonical = simulation.labour_supply_responses

    legacy_node = canonical.clone()
    legacy_node.name = _LEGACY_LSR_PATH
    simulation.add_child("labor_supply_responses", legacy_node)
    return parameters

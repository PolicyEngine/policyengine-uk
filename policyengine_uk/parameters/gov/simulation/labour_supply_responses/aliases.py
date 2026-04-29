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


def add_lsr_deprecation_aliases(parameters: ParameterNode) -> ParameterNode:
    simulation = parameters.gov.simulation
    canonical = simulation.labour_supply_responses

    legacy_node = canonical.clone()
    legacy_node.name = _LEGACY_LSR_PATH
    simulation.add_child("labor_supply_responses", legacy_node)
    return parameters

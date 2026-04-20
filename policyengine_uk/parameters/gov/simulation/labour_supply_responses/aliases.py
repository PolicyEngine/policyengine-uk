"""Deprecation aliases mirroring the renamed `labour_supply_responses` parameters
under the legacy `labor_supply_responses` path.

`policyengine-app` (legacy) hard-codes
`gov.simulation.labor_supply_responses.{income_elasticity,substitution_elasticity}`
in PolicyRightSidebar.jsx. Without this alias the LSR sliders break the
moment a deployed app rebuilds against this version of policyengine-uk.
The companion app PR (PolicyEngine/policyengine-app#2829) migrates to the
new path; remove this alias once that ships.
"""

from policyengine_core.parameters import Parameter, ParameterNode


_ALIASED_PARAMETERS = ("income_elasticity", "substitution_elasticity")


def add_lsr_deprecation_aliases(parameters: ParameterNode) -> ParameterNode:
    simulation = parameters.gov.simulation
    canonical = simulation.labour_supply_responses

    legacy_node = ParameterNode(
        name="gov.simulation.labor_supply_responses",
        data={},
    )

    for child_name in _ALIASED_PARAMETERS:
        canonical_child: Parameter = getattr(canonical, child_name)
        legacy_child = canonical_child.clone()
        legacy_child.name = f"gov.simulation.labor_supply_responses.{child_name}"
        legacy_node.add_child(child_name, legacy_child)

    simulation.add_child("labor_supply_responses", legacy_node)
    return parameters

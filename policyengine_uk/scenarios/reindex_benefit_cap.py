from policyengine_uk.model_api import Scenario
from policyengine_uk import Simulation
from policyengine_core.parameters import Parameter


def index_benefit_cap(simulation: Simulation):
    # Identify benefit cap parameters
    simulation.tax_benefit_system.reset_parameters()

    params = (
        simulation.tax_benefit_system.parameters.gov.dwp.benefit_cap.get_descendants()
    )
    # We just want the leaf nodes of the parameter tree
    # TODO: add a get-descendants-leaf-nodes-only function

    params = [param for param in params if isinstance(param, Parameter)]

    for parameter in params:
        parameter: Parameter  # Type annotation
        # Delete all values after 2025
        parameter.values_list = [
            entry
            for entry in parameter.values_list
            if entry.instant_str < "2026-01-01"
        ]
        parameter.metadata.update(
            uprating="gov.benefit_uprating_cpi",
        )
    simulation.tax_benefit_system.process_parameters()


reindex_benefit_cap = Scenario(simulation_modifier=index_benefit_cap)

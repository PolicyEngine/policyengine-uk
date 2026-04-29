from policyengine_core.parameters import Parameter

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario


def remove_economic_assumptions(simulation: Simulation):
    simulation.disable_economic_assumptions = True
    simulation.tax_benefit_system.reset_parameters()

    cutoff = f"{simulation.default_input_period}-01-01"
    yoy_growth = (
        simulation.tax_benefit_system.parameters.gov.economic_assumptions.yoy_growth
    )

    for parameter in yoy_growth.get_descendants():
        if not isinstance(parameter, Parameter):
            continue
        for value_at_instant in parameter.values_list:
            if value_at_instant.instant_str >= cutoff:
                value_at_instant.value = 0

    simulation.tax_benefit_system.process_parameters()


no_economic_assumptions = Scenario(
    simulation_modifier=remove_economic_assumptions,
    applied_before_data_load=True,
)

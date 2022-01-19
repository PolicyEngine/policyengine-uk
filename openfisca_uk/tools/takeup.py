

from openfisca_core.parameters import Parameter
from openfisca_core.periods import instant
from openfisca_uk.tools.simulation import Microsimulation
import logging

logging.basicConfig(level=logging.INFO)


def calculate_takeup_rate(sim: Microsimulation, variable: str, caseload_parameter: Parameter, takeup_parameter: Parameter) -> float:
    for caseload in caseload_parameter.values_list:
        year = instant(caseload.instant_str).year
        takeup_parameter.update(period=f"year:{year}-01-01:1", value=1)
        eligible_caseload = (sim.calc(variable) > 0).sum()
        simulated_takeup = round(caseload.value / eligible_caseload, 3)
        logging.info(f"Simulated takeup rate for {sim.simulation.tax_benefit_system.variables[variable].label} in {year} is {simulated_takeup:.1%}")
        takeup_parameter.update(period=f"year:{year}-01-01:1", value=simulated_takeup)
    return str(takeup_parameter)

sim = Microsimulation()

parameters = sim.simulation.tax_benefit_system.parameters

print(calculate_takeup_rate(sim, "child_benefit", parameters.hmrc.child_benefit.statistics.caseload, parameters.hmrc.child_benefit.takeup_rate))

from policyengine_uk.model_api import *
from policyengine_core.simulations import *


class relative_capital_gains_mtr_change(Variable):
    value_type = float
    entity = Person
    label = "relative change in capital gains tax rate"
    unit = "/1"
    definition_period = YEAR

    def formula(person, period, parameters):
        simulation: Simulation = person.simulation
        baseline_branch = simulation.get_branch("baseline").get_branch(
            "baseline_cgr_measurement"
        )
        baseline_branch.set_input(
            "capital_gains_before_response",
            period,
            person("capital_gains_before_response", period),
        )
        baseline_person = baseline_branch.populations["person"]
        baseline_branch.tax_benefit_system.neutralize_variable(
            "capital_gains_behavioural_response"
        )
        baseline_branch.set_input(
            "capital_gains_before_response",
            period,
            person("capital_gains_before_response", period),
        )
        baseline_mtr = baseline_person(
            "marginal_tax_rate_on_capital_gains", period
        )
        del simulation.branches["baseline"].branches[
            "baseline_cgr_measurement"
        ]

        measurement_branch = simulation.get_branch("cgr_measurement")
        measurement_branch.tax_benefit_system.neutralize_variable(
            "capital_gains_behavioural_response"
        )
        measurement_branch.set_input(
            "capital_gains_before_response",
            period,
            person("capital_gains_before_response", period),
        )
        measurement_person = measurement_branch.populations["person"]
        reform_mtr = measurement_person(
            "marginal_tax_rate_on_capital_gains", period
        )
        del simulation.branches["cgr_measurement"]

        # Handle zeros in tax rates to prevent log(0)
        min_rate = 0.001
        baseline_mtr_adj = np.maximum(baseline_mtr, min_rate)
        reform_mtr_adj = np.maximum(reform_mtr, min_rate)

        # Calculate log difference
        return np.log(reform_mtr_adj) - np.log(baseline_mtr_adj)

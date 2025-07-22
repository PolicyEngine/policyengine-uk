from policyengine_uk.model_api import *


class employment_income_behavioral_response(Variable):
    value_type = float
    entity = Person
    label = "income-related labor supply change"
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        lsr = parameters(period).gov.simulation.labor_supply_responses
        simulation = person.simulation
        if simulation.baseline is None:
            return 0  # No reform, no impact
        if lsr.income_elasticity == 0 and lsr.substitution_elasticity == 0:
            return 0

        measurement_branch = simulation.get_branch(
            "lsr_measurement", clone_system=True
        )  # A branch without LSRs
        baseline_branch = simulation.get_branch("baseline").get_branch(
            "baseline_lsr_measurement", clone_system=True
        )  # Already created by default

        # (system with LSRs) <- (system without LSRs used to calculate LSRs)
        #                      |
        #                      * -(baseline system without LSRs used to calculate LSRs)

        for branch in [measurement_branch, baseline_branch]:
            branch.tax_benefit_system.neutralize_variable(
                "employment_income_behavioral_response"
            )
            branch.set_input(
                "employment_income_before_lsr",
                period,
                person("employment_income_before_lsr", period),
            )

        return add(
            person,
            period,
            [
                "income_elasticity_lsr",
                "substitution_elasticity_lsr",
            ],
        )

from policyengine_uk.model_api import *
from policyengine_uk.utils.household_subset import whole_population_value
from policyengine_uk.utils.labour_supply_responses import (
    measurement_branches,
    response_source,
)


class employment_income_behavioral_response(Variable):
    value_type = float
    entity = Person
    label = "income-related labour supply change"
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        lsr = parameters(period).gov.simulation.labour_supply_responses
        simulation = person.simulation
        if simulation.baseline is None:
            return 0  # No reform, no impact
        if lsr.income_elasticity == 0 and lsr.substitution_elasticity == 0:
            return 0
        # A branch holding only some households (utils.household_subset) has
        # the whole simulation as an ancestor with its rules: it takes the
        # whole population's response, at its own people.
        whole = whole_population_value(
            person, "employment_income_behavioral_response", period
        )
        if whole is not None:
            return whole
        # A branch with its parent's rules takes the parent's response.
        source = response_source(simulation)
        if source is not simulation:
            return source.person("employment_income_behavioral_response", period)

        # (system with LSRs) <- (system without LSRs used to calculate LSRs)
        #                      |
        #                      * -(baseline system without LSRs used to calculate LSRs)

        # Both terms measure on the one pair of branches opened here.
        with measurement_branches(person, period):
            return add(
                person,
                period,
                [
                    "income_elasticity_lsr",
                    "substitution_elasticity_lsr",
                ],
            )

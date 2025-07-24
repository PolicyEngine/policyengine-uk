from policyengine_uk.model_api import *


class basic_state_pension(Variable):
    label = "basic State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        has_dataset = simulation.dataset is not None

        data_year = simulation.dataset.time_period if has_dataset else period

        reported = where(
            has_dataset,
            person("state_pension_reported", data_year),
            person("state_pension_reported", period),
        )

        type = person("state_pension_type", period)
        maximum_basic_sp = (
            parameters(
                data_year
            ).gov.dwp.state_pension.basic_state_pension.amount
            * WEEKS_IN_YEAR
        )
        amount_in_data_year = where(
            type == type.possible_values.BASIC,
            min_(reported, maximum_basic_sp),
            reported,
        )
        uprating_factor = where(
            has_dataset,
            parameters.gov.economic_assumptions.yoy_growth.triple_lock(period)
            / parameters.gov.economic_assumptions.yoy_growth.triple_lock(
                data_year
            ),
            1,
        )

        return amount_in_data_year * uprating_factor

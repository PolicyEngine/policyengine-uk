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
            person("state_pension_reported", data_year) / WEEKS_IN_YEAR,
            person("state_pension_reported", period) / WEEKS_IN_YEAR,
        )

        type = person("state_pension_type", period)
        maximum_basic_sp = parameters(
            data_year
        ).gov.dwp.state_pension.basic_state_pension.amount
        amount_in_data_year = where(
            type == type.possible_values.BASIC,
            min_(reported, maximum_basic_sp),
            reported,
        )

        uprating_factor = where(
            has_dataset,
            parameters.gov.dwp.state_pension.triple_lock.index(period)
            / parameters.gov.dwp.state_pension.triple_lock.index(data_year),
            1,
        )

        return amount_in_data_year * uprating_factor * WEEKS_IN_YEAR

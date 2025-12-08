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

        # Determine the data year: from dataset if available, otherwise current
        if has_dataset:
            try:
                data_year = min(simulation.dataset.years)
            except:
                data_year = period.start.year
        else:
            data_year = period.start.year

        reported = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        pension_type = person("state_pension_type", period)
        maximum_basic_sp = parameters(
            data_year
        ).gov.dwp.state_pension.basic_state_pension.amount

        # For BASIC pension type, cap at the maximum; otherwise return 0
        amount_in_data_year = where(
            pension_type == pension_type.possible_values.BASIC,
            min_(reported, maximum_basic_sp),
            0,
        )

        # Apply triple lock uprating only when using dataset
        # (i.e., when data year differs from simulation period)
        if has_dataset:
            triple_lock = (
                parameters.gov.economic_assumptions.indices.triple_lock
            )
            uprating = triple_lock(period) / triple_lock(data_year)
        else:
            uprating = 1

        return amount_in_data_year * uprating * WEEKS_IN_YEAR

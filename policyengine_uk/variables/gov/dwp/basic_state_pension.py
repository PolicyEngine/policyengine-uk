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
        sp_amount = parameters.gov.dwp.state_pension.basic_state_pension.amount
        max_sp_data_year = sp_amount(data_year)
        max_sp_period = sp_amount(period)

        # Compute the person's share of the data-year maximum so reforms can
        # scale the current-period amount while preserving the original cap.
        share = where(
            max_sp_data_year > 0,
            min_(reported, max_sp_data_year) / max_sp_data_year,
            0,
        )
        return (
            where(
                pension_type == pension_type.possible_values.BASIC,
                share * max_sp_period,
                0,
            )
            * WEEKS_IN_YEAR
        )

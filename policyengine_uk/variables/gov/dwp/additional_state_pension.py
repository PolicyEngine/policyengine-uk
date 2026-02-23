from policyengine_uk.model_api import *


class additional_state_pension(Variable):
    label = "additional State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        if simulation.dataset is None:
            return 0
        try:
            data_year = min(simulation.dataset.years)
        except:
            data_year = period.start.year
        reported = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        type = person("state_pension_type", data_year)
        # Use leaf-level access so parameter reforms are visible
        sp_amount = parameters.gov.dwp.state_pension.basic_state_pension.amount
        max_sp_data_year = sp_amount(data_year)
        max_sp_period = sp_amount(period)

        # Additional SP is the excess above the basic SP maximum
        additional_data_year = where(
            type == type.possible_values.BASIC,
            max_(reported - max_sp_data_year, 0),
            0,
        )

        # Uprate using the ratio of basic SP parameters (responds to reforms)
        uprating = where(
            max_sp_data_year > 0,
            max_sp_period / max_sp_data_year,
            1,
        )
        return additional_data_year * uprating * WEEKS_IN_YEAR

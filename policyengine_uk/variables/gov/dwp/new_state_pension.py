from policyengine_uk.model_api import *


class new_state_pension(Variable):
    label = "new State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        has_dataset = simulation.dataset is not None

        if has_dataset:
            try:
                data_year = min(simulation.dataset.years)
            except:
                data_year = period.start.year
        else:
            data_year = period.start.year

        pension_type = person("state_pension_type", period)
        eligible = pension_type == pension_type.possible_values.NEW

        reported_weekly = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        p = parameters.gov.dwp.state_pension.new_state_pension
        max_new_data_year = p.amount(data_year)
        max_new_period = p.amount(period)

        # Pro-rate by reported amount rather than flat max:
        #   share < 1 → under-35-year NI records get their actual partial rate
        #   share > 1 → pre-2016 SERPS/S2P Protected Payment adds on top
        # The previous ``eligible * p.amount`` overstated partial-record
        # retirees and dropped the Protected Payment tail entirely.
        share = where(
            max_new_data_year > 0,
            reported_weekly / max_new_data_year,
            0,
        )
        return eligible * share * max_new_period * WEEKS_IN_YEAR

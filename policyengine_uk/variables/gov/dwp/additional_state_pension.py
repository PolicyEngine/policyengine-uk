from policyengine_uk.model_api import *


class additional_state_pension(Variable):
    label = "additional State Pension"
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
        reported = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        pension_type = person("state_pension_type", data_year)
        types = pension_type.possible_values

        bsp_amount = parameters.gov.dwp.state_pension.basic_state_pension.amount
        nsp_amount = parameters.gov.dwp.state_pension.new_state_pension.amount

        # Each pension type has its own flat-rate ceiling; anything above
        # the ceiling is an add-on:
        #   BASIC → SERPS / S2P (pre-2016 earnings-related top-up)
        #   NEW   → Protected Payment (pre-2016 accrual exceeding the
        #           new flat rate, folded into NSP under current law)
        max_for_type_data = select(
            [pension_type == types.BASIC, pension_type == types.NEW],
            [bsp_amount(data_year), nsp_amount(data_year)],
            default=0,
        )
        max_for_type_period = select(
            [pension_type == types.BASIC, pension_type == types.NEW],
            [bsp_amount(period), nsp_amount(period)],
            default=0,
        )

        amount_in_data_year = where(
            pension_type != types.NONE,
            max_(reported - max_for_type_data, 0),
            0,
        )
        uprating = where(
            max_for_type_data > 0,
            max_for_type_period / max_for_type_data,
            1,
        )
        return amount_in_data_year * uprating * WEEKS_IN_YEAR

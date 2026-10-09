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
        # Split by the period's type, as basic_state_pension and
        # new_state_pension do, so the three components add up to the
        # reported amount. Survey ages are held fixed across years, so a
        # record's birth cohort, and with it its type, can differ from the
        # data year's. The data year's type would pay the band between the
        # two flat-rate ceilings twice for a record that is BASIC in the data
        # year and NEW in the period, and leave it unpaid the other way round.
        pension_type = person("state_pension_type", period)
        types = pension_type.possible_values

        bsp_amount = parameters.gov.dwp.state_pension.basic_state_pension.amount
        nsp_amount = parameters.gov.dwp.state_pension.new_state_pension.amount

        # Each pension type has its own flat-rate ceiling; anything above
        # the ceiling is an add-on:
        #   BASIC → SERPS / S2P (pre-2016 earnings-related top-up)
        #   NEW   → Protected Payment (pre-2016 accrual exceeding the
        #           new flat rate, folded into NSP under current law)
        # state_pension_reported was observed under the legislated rates, so
        # split it at the baseline's data-year rate, not the reformed one.
        # Otherwise a reform that also sets the data year's rate (an undated
        # reform, or any reform in a simulation without a dataset, where the
        # data year is the period) leaves the period-over-data-year ratio at 1,
        # and state_pension does not follow the reform
        # (PolicyEngine/policyengine-uk#2122).
        baseline = getattr(simulation, "baseline", None)
        legislated = (
            baseline.tax_benefit_system.parameters
            if baseline is not None
            else parameters
        ).gov.dwp.state_pension
        max_for_type_data = select(
            [pension_type == types.BASIC, pension_type == types.NEW],
            [
                legislated.basic_state_pension.amount(data_year),
                legislated.new_state_pension.amount(data_year),
            ],
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
        # No State Pension is paid before State Pension age. A computed type
        # is already NONE there; this also holds if the type is an input.
        is_sp_age = person("is_SP_age", period)
        return is_sp_age * amount_in_data_year * uprating * WEEKS_IN_YEAR

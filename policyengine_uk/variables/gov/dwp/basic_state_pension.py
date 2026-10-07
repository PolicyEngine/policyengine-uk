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
        max_sp_data_year = legislated.basic_state_pension.amount(data_year)
        max_sp_period = parameters.gov.dwp.state_pension.basic_state_pension.amount(
            period
        )

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

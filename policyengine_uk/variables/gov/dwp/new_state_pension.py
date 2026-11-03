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
        max_new_data_year = legislated.new_state_pension.amount(data_year)
        max_new_period = parameters.gov.dwp.state_pension.new_state_pension.amount(
            period
        )

        # Pro-rate by reported amount, capped at the flat max so a partial
        # NI record gets the appropriate partial rate. Any reported amount
        # above the flat max is Protected Payment (pre-2016 SERPS/S2P) and
        # flows through ``additional_state_pension`` — mirrors the
        # BASIC / ASP split so ``new_state_pension`` is always the headline
        # flat-rate component.
        share = np.divide(
            min_(reported_weekly, max_new_data_year),
            max_new_data_year,
            out=np.zeros_like(reported_weekly, dtype=float),
            where=max_new_data_year > 0,
        )
        return eligible * share * max_new_period * WEEKS_IN_YEAR

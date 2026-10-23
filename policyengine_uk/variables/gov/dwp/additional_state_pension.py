from policyengine_uk.model_api import *


class additional_state_pension(Variable):
    label = "additional State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/5/section/150",
        "https://www.legislation.gov.uk/ukpga/1992/5/section/151A",
        "https://www.legislation.gov.uk/uksi/2026/148/article/4/made",
        "https://www.legislation.gov.uk/uksi/2026/148/article/6/made",
    )

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

        # Each pension type has its own flat-rate ceiling; anything above
        # the ceiling is an add-on:
        #   BASIC → SERPS / S2P (pre-2016 earnings-related top-up)
        #   NEW   → Protected Payment (pre-2016 accrual exceeding the
        #           new flat rate, folded into NSP under current law)
        # state_pension_reported was observed under the legislated rates, so
        # split it at the baseline's data-year rate, not the reformed one, as
        # basic_state_pension and new_state_pension do. Otherwise a reform
        # that also sets the data year's rate (an undated reform, or any
        # reform in a simulation without a dataset, where the data year is
        # the period) would move part of the reported amount between the
        # flat-rate part and the add-on (PolicyEngine/policyengine-uk#2122).
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
        amount_in_data_year = where(
            pension_type != types.NONE,
            max_(reported - max_for_type_data, 0),
            0,
        )
        # The full rates rise with the triple lock, but the add-on rises with
        # prices: each year's Up-rating Order raises additional pensions and
        # the amounts of new State Pension above the full rate by September
        # CPI (Social Security Administration Act 1992 ss.150(1)(c), 151(1)
        # and 151A; e.g. SI 2026/148 arts 4(3) and 6(3)(b), 3.8%, against
        # 4.8% for the full rates). So it is uprated from the data year by
        # September CPI, not by the full rate, and a reform to the full rates
        # leaves it alone (PolicyEngine/policyengine-uk#1941). The index is
        # read from this simulation's parameters, so a price scenario moves
        # it.
        september_cpi = (
            parameters.gov.economic_assumptions.indices.september_cpi_uprating
        )
        uprating = september_cpi(period) / september_cpi(data_year)
        # No State Pension is paid before State Pension age. A computed type
        # is already NONE there; this also holds if the type is an input.
        is_sp_age = person("is_SP_age", period)
        return is_sp_age * amount_in_data_year * uprating * WEEKS_IN_YEAR

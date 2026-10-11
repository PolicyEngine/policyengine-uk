from policyengine_uk.model_api import *


def state_pension_data_year(person, period) -> int:
    """The year state_pension_reported was observed: the dataset's first year,
    or the period itself in a simulation without a dataset."""
    simulation = person.simulation
    if simulation.dataset is not None:
        try:
            return min(simulation.dataset.years)
        except Exception:
            return period.start.year
    return period.start.year


def receives_age_addition(person, period, age_addition_age, data_year):
    """Whether a person gets the age addition in ``period``: over the age of 80
    and entitled to a retirement pension under the Social Security
    Contributions and Benefits Act 1992 (s.79(1)). A person is over an age once
    they have attained it (s.173). Entitlement is read as a basic State Pension
    type with a State Pension reported in the data year: a new State Pension,
    under Part 1 of the Pensions Act 2014, is not a pension "under this Act"
    (s.79(1) as amended by the Pensions Act 2014 Sch 12 para 85)."""
    pension_type = person("state_pension_type", period)
    basic = pension_type == pension_type.possible_values.BASIC
    has_pension = person("state_pension_reported", data_year) > 0
    over_age = person("age", period) >= age_addition_age
    return basic & has_pension & over_age


class state_pension_age_addition(Variable):
    label = "State Pension age addition"
    documentation = (
        "The age addition: 25p a week added to a retirement pension under the "
        "Social Security Contributions and Benefits Act 1992 (the basic State "
        "Pension) once its recipient is over 80, and never uprated. A new "
        "State Pension gets none. The model is annual and, as for State "
        "Pension age, reads age on 6 October, the middle of the fiscal year: "
        "a person who turns 80 by then gets the whole year's addition, and one "
        "who turns 80 later in the year gets none until the next."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/79",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/173",
        "https://www.legislation.gov.uk/ukpga/1992/4/schedule/4",
        "https://www.legislation.gov.uk/ukpga/2014/19/schedule/12/paragraph/85",
        "https://www.legislation.gov.uk/uksi/2026/148/article/3/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.state_pension.age_addition
        data_year = state_pension_data_year(person, period)
        receives = receives_age_addition(person, period, p.age, data_year)
        return receives * p.amount * WEEKS_IN_YEAR

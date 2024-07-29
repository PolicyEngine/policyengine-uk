from policyengine_uk.model_api import *


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "State Pension age for this person"
    definition_period = YEAR
    unit = "year"

    def formula(person, period, parameters):
        SP = parameters(period).gov.dwp.state_pension
        return where(person("is_male", period), SP.age.male, SP.age.female)


class is_SP_age(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is State Pension Age"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        threshold = person("state_pension_age", period)
        return age >= threshold


class StatePensionType(Enum):
    BASIC = "basic"
    NEW = "new"
    NONE = "none"


class state_pension_type(Variable):
    label = "State Pension type"
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = StatePensionType
    default_value = StatePensionType.BASIC

    def formula(person, period, parameters):
        sp = parameters.gov.dwp.state_pension
        male = person("is_male", period)
        last_entry = sp.new_state_pension.active.values_list[0]
        is_sp_age = person("is_SP_age", period)
        if not last_entry:
            values_if_sp_age = where(
                is_sp_age, StatePensionType.BASIC, StatePensionType.NONE
            )
        else:
            instant = last_entry.instant_str
            years_since_instant = period.start.year - int(instant[:4])
            male_age = sp.age.male(instant) + years_since_instant
            female_age = sp.age.female(instant) + years_since_instant
            age = person("age", period)
            over_age = where(male, age >= male_age, age >= female_age)
            values_if_sp_age = where(
                over_age, StatePensionType.BASIC, StatePensionType.NEW
            )

        return where(is_sp_age, values_if_sp_age, StatePensionType.NONE)


class basic_state_pension(Variable):
    label = "basic State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        if not hasattr(simulation, "dataset"):
            return 0

        data_year = simulation.dataset.time_period
        reported = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        type = person("state_pension_type", period)
        maximum_basic_sp = parameters(
            data_year
        ).gov.dwp.state_pension.basic_state_pension.amount
        amount_in_data_year = where(
            type == StatePensionType.BASIC, min_(reported, maximum_basic_sp), 0
        )
        triple_lock = parameters.gov.dwp.state_pension.triple_lock
        uprating_since_data_year = triple_lock(period) / triple_lock(data_year)
        return amount_in_data_year * uprating_since_data_year * WEEKS_IN_YEAR


class additional_state_pension(Variable):
    label = "additional State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        if not hasattr(simulation, "dataset"):
            return 0

        data_year = simulation.dataset.time_period
        reported = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        type = person("state_pension_type", data_year)
        maximum_basic_sp = parameters(
            data_year
        ).gov.dwp.state_pension.basic_state_pension.amount
        amount_in_data_year = where(
            type == StatePensionType.BASIC,
            max_(reported - maximum_basic_sp, 0),
            0,
        )
        return amount_in_data_year * WEEKS_IN_YEAR


class new_state_pension(Variable):
    label = "new State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        if not hasattr(simulation, "dataset"):
            return 0

        return where(
            person("state_pension_type", period) == StatePensionType.NEW,
            parameters(period).gov.dwp.state_pension.new_state_pension.amount
            * WEEKS_IN_YEAR,
            0,
        )


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported income from the State Pension"
    definition_period = YEAR
    unit = GBP

    def formula_2022(person, period, parameters):
        sp_ly = person("state_pension_reported", period.last_year)
        return sp_ly

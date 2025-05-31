from policyengine_uk.model_api import *


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

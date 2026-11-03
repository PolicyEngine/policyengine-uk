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
        is_sp_age = person("is_SP_age", period)

        # Find the instant the New State Pension was first switched on.
        # values_list is ordered newest→oldest and PolicyEngine-core
        # auto-extrapolates it into the far future, so values_list[0] is a
        # future year's extrapolation rather than the activation date. Walk
        # oldest→newest and take the first `True` value to get the real
        # activation instant (e.g. 2016-01-01 under current law).
        activation_entry = None
        for entry in reversed(sp.new_state_pension.active.values_list):
            if entry.value:
                activation_entry = entry
                break

        if activation_entry is None:
            values_if_sp_age = where(
                is_sp_age, StatePensionType.BASIC, StatePensionType.NONE
            )
        else:
            # Pensions Act 2014 s.1(2): a person who reaches pensionable age
            # before 6 April 2016 is not entitled to the new State Pension,
            # and stays on the basic State Pension instead.
            first_year = int(activation_entry.instant_str[:4])
            months_from_start_to_mid_year = 12 * (period.start.year - first_year) + 6
            reached_before_start = (
                person("months_since_state_pension_age", period)
                > months_from_start_to_mid_year
            )
            values_if_sp_age = where(
                reached_before_start, StatePensionType.BASIC, StatePensionType.NEW
            )

        return where(is_sp_age, values_if_sp_age, StatePensionType.NONE)

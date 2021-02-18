from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class Country(Enum):
    unknown = u"unknown"
    england = u"england"
    wales = u"wales"
    scotland = u"scotland"
    northern_ireland = u"northern_ireland"


class country(Variable):
    value_type = Enum
    possible_values = Country
    default_value = Country.england
    entity = Household
    label = u"Country of the UK"
    definition_period = ETERNITY


class household_weight(Variable):
    value_type = float
    entity = Household
    label = u"Weighting of the household"
    definition_period = ETERNITY


class household_id(Variable):
    value_type = int
    entity = Household
    label = u"ID of the household"
    definition_period = ETERNITY


class Region(Enum):
    north_east = u"north_east"
    north_west = u"north_west"
    yorkshire = u"yorkshire"
    east_midlands = u"east_midlands"
    west_midlands = u"west_midlands"
    east_of_england = u"east_of_england"
    london = u"london"
    south_east = u"south_east"
    south_west = u"south_west"
    wales = u"wales"
    scotland = u"scotland"
    northern_ireland = u"northern_ireland"


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.london
    entity = Household
    label = u"Region of the UK"
    definition_period = ETERNITY


class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        second_adult = household.nb_persons(Household.ADULT) == 2
        num_young_children = household.sum(
            household.members("is_young_child", period)
        )
        num_older_children = household.sum(
            household.members("is_older_child", period)
        )
        weighting = (
            0.67
            + 0.33 * second_adult
            + 0.33 * num_older_children
            + 0.2 * num_young_children
        )
        return weighting


class household_equivalisation_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        second_adult = household.nb_persons(Household.ADULT) == 2
        num_young_children = household.sum(
            household.members("is_young_child", period)
        )
        num_older_children = household.sum(
            household.members("is_older_child", period)
        )
        weighting = (
            0.58
            + 0.42 * second_adult
            + 0.42 * num_older_children
            + 0.2 * num_young_children
        )
        return weighting


class people_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of people in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons()


class adults_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of adults in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons(Household.ADULT)


class working_age_adults_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of adults in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("is_WA_adult", period))


class children_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of children in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons(Household.CHILD)


class seniors_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of senior citizens in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("is_SP_age", period.this_year))


class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = YEAR
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income", period)
            < parameters(period).poverty.absolute_poverty_threshold_bhc * 52
        )


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, after housing costs"
    )
    definition_period = YEAR
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income_ahc", period)
            < parameters(period).poverty.absolute_poverty_threshold_ahc * 52
        )


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = u"The poverty line for the household, before housing costs"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        return parameters(
            period
        ).poverty.absolute_poverty_threshold_bhc * household(
            "household_equivalisation_bhc", period.this_year
        )


class poverty_line_ahc(Variable):
    value_type = float
    entity = Household
    label = u"The poverty line for the household, after housing costs"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        return parameters(
            period
        ).poverty.absolute_poverty_threshold_ahc * household(
            "household_equivalisation_ahc", period.this_year
        )


class poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Positive financial gap between net household income and the poverty line"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        net_income = household(
            "household_net_income", period, options=[DIVIDE]
        )
        return max_(0, household("poverty_line_bhc", period) - net_income)


class poverty_gap_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Positive financial gap between net household income and the poverty line, after housing costs"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        net_income = household(
            "household_net_income_ahc", period, options=[DIVIDE]
        )
        return max_(0, household("poverty_line_ahc", period) - net_income)


# Enums


class household_type(Enum):
    unknown = u"unknown"
    house = u"house"
    flat = u"flat"
    room = u"room"
    other = u"other"

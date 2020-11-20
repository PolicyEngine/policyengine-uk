from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class Country(Enum):
    SCOTLAND = u"Scotland"
    ENGLAND = u"England"
    WALES = u"Wales"
    NI = u"Northern Ireland"


class country(Variable):
    value_type = Enum
    possible_values = Country
    default_value = Country.ENGLAND
    entity = Household
    label = u"Country of the UK"
    definition_period = ETERNITY


class household_weight(Variable):
    value_type = float
    entity = Household
    label = u"Weighting of the household"
    definition_period = ETERNITY


class household_id(Variable):
    value_type = str
    entity = Household
    label = u"ID of the household"
    definition_period = ETERNITY

class Region(Enum):
    NORTH_EAST = u'North East'
    NORTH_WEST = u'North West',
    YORKSHIRE = u'Yorkshire and the Humber'
    EAST_MIDLANDS = u'East Midlands'
    WEST_MIDLANDS = u'West Midlands'
    EAST_OF_ENGLAND = u'East of England'
    LONDON = u'London'
    SOUTH_EAST = u'South East'
    SOUTH_WEST = u'South West'
    WALES = u'Wales'
    SCOTLAND = u'Scotland'
    NORTHERN_IRELAND = u'Northern Ireland'

class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON
    entity = Household
    label = u'Region of the UK'
    definition_period = ETERNITY

    
class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition, before housing costs"
    definition_period = ETERNITY

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
    definition_period = ETERNITY

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
        return household.sum(household.members("is_WA_age_adult", period))


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
        return household.sum(household.members("is_SP_age", period))

class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = WEEK

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income", period, options=[DIVIDE])
            < parameters(period).poverty.absolute_poverty_bhc
        )


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, after housing costs"
    )
    definition_period = WEEK

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income_ahc", period, options=[DIVIDE])
            < parameters(period).poverty.absolute_poverty_ahc
        )
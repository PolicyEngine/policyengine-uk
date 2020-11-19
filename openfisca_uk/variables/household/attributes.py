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

    
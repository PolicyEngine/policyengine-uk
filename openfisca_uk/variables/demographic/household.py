from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class Country(Enum):
    UNKNOWN = u"Unknown"
    SCOTLAND = u"Scotland"
    ENGLAND = u"England"
    WALES = u"Wales"
    NI = u"Northern Ireland"


class country(Variable):
    value_type = Enum
    possible_values = Country
    default_value = Country.UNKNOWN
    entity = Household
    label = u"Country of the UK"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        unknown_region = household("region") == Region.UNKNOWN
        wales = household("region") == Region.WALES
        NI = household("region") = Region.NORTHERN_IRELAND
        scot = household("region") = Region.SCOTLAND
        country = select([unknown_region, scot, wales, NI, True], [Country.UNKNOWN, Country.SCOTLAND, Country.WALES, Country.ENGLAND])
        return country


class Region(Enum):
    UNKNOWN = u"Unknown"
    NORTH_EAST = u"North East"
    NORTH_WEST = u"North West"
    YORKSHIRE = u"Yorkshire and the Humber"
    EAST_MIDLANDS = u"East Midlands"
    WEST_MIDLANDS = u"West Midlands"
    EAST_OF_ENGLAND = u"East of England"
    LONDON = u"London"
    SOUTH_EAST = u"South East"
    SOUTH_WEST = u"South West"
    WALES = u"Wales"
    SCOTLAND = u"Scotland"
    NORTHERN_IRELAND = u"Northern Ireland"


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.UNKNOWN
    entity = Household
    label = u"Region of the UK"
    definition_period = ETERNITY
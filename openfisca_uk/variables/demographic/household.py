from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class households(Variable):
    value_type = float
    entity = Household
    label = u"Variable holding households"
    definition_period = YEAR
    default_value = 1

class num_bedrooms(Variable):
    value_type = float
    entity = Household
    label = u'The number of bedrooms in the house'
    definition_period = YEAR

class is_shared_accommodation(Variable):
    value_type = bool
    entity = Household
    label = u'Whether the household is shared accommodation'
    definition_period = YEAR


class household_weight(Variable):
    value_type = float
    entity = Household
    label = u"Weight factor for the household"
    definition_period = YEAR


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
        ni = household("region") == Region.NORTHERN_IRELAND
        scot = household("region") == Region.SCOTLAND
        country = select(
            [unknown_region, scot, wales, ni, True],
            [
                Country.UNKNOWN,
                Country.SCOTLAND,
                Country.WALES,
                Country.NI,
                Country.ENGLAND,
            ],
        )
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

class TenureType(Enum):
    RENT_FROM_COUNCIL = "Rented from Council"
    RENT_FROM_HA = "Rented from a Housing Association"
    RENT_PRIVATELY = "Rented privately"
    OWNED_OUTRIGHT = "Owned outright"
    OWNED_WITH_MORTGAGE = "Owned with a mortgage"

class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = u'Tenure type of the household'
    definition_period = YEAR

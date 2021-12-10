from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class household_id(Variable):
    value_type = int
    entity = Household
    label = u"ID for the household"
    definition_period = YEAR


class households(Variable):
    value_type = float
    entity = Household
    label = u"Variable holding households"
    definition_period = YEAR
    default_value = 1


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = u"The number of bedrooms in the house"
    definition_period = YEAR


class is_shared_accommodation(Variable):
    value_type = bool
    entity = Household
    label = u"Whether the household is shared accommodation"
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
    NORTHERN_IRELAND = u"Northern Ireland"


class country(Variable):
    value_type = Enum
    possible_values = Country
    default_value = Country.UNKNOWN
    entity = Household
    label = u"Country of the UK"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        unknown_region = household("region", period) == Region.UNKNOWN
        wales = household("region", period) == Region.WALES
        ni = household("region", period) == Region.NORTHERN_IRELAND
        scot = household("region", period) == Region.SCOTLAND
        country = select(
            [unknown_region, scot, wales, ni, True],
            [
                Country.UNKNOWN,
                Country.SCOTLAND,
                Country.WALES,
                Country.NORTHERN_IRELAND,
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
    label = u"Region"
    documentation = "Area of the UK"
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
    label = u"Tenure type of the household"
    definition_period = YEAR


class is_renting(Variable):
    value_type = bool
    entity = Household
    label = u"Is renting"
    definition_period = YEAR

    def formula(household, period, parameters):
        tenure = household("tenure_type", period)
        rent_types = (
            TenureType.RENT_PRIVATELY,
            TenureType.RENT_FROM_COUNCIL,
            TenureType.RENT_PRIVATELY,
        )
        return sum([tenure == rent_type for rent_type in rent_types])


class AccommodationType(Enum):
    HOUSE_DETACHED = "Detached house"
    HOUSE_SEMI_DETACHED = "Semi-detached house"
    HOUSE_TERRACED = "Terraced house"
    FLAT = "Purpose-built flat or maisonette"
    CONVERTED_HOUSE = "Converted house or building"
    MOBILE = "Caravan/Mobile home or houseboat"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class accommodation_type(Variable):
    value_type = Enum
    possible_values = AccommodationType
    default_value = AccommodationType.UNKNOWN
    entity = Household
    label = u"Type of accommodation"
    definition_period = ETERNITY


class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        other_adults = max_(
            household.sum(household.members("is_adult", period)) - 1, 0
        )
        num_young_children = household.sum(
            household.members("is_young_child", period)
        )
        num_older_children = household.sum(
            household.members("is_older_child", period)
        )
        weighting = (
            0.67
            + 0.33 * other_adults
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
        other_adults = max_(
            household.sum(household.members("is_adult", period)) - 1, 0
        )
        num_young_children = household.sum(
            household.members("is_young_child", period)
        )
        num_older_children = household.sum(
            household.members("is_older_child", period)
        )
        weighting = (
            0.58
            + 0.42 * other_adults
            + 0.42 * num_older_children
            + 0.2 * num_young_children
        )
        return weighting


class household_num_people(Variable):
    value_type = int
    entity = Household
    label = u"Number of people"
    definition_period = YEAR
    unit = "person"

    def formula(household, period, parameters):
        return household.nb_persons()


class household_num_benunits(Variable):
    value_type = int
    entity = Household
    label = u"Number of benefit units"
    definition_period = YEAR
    unit = "benefit unit"

    def formula(household, period, parameters):
        return household.sum(household.members("is_benunit_head", period))

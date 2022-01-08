from openfisca_uk.model_api import *


class household_id(Variable):
    value_type = int
    entity = Household
    label = "ID for the household"
    definition_period = YEAR


class households(Variable):
    value_type = float
    entity = Household
    label = "Variable holding households"
    definition_period = YEAR
    default_value = 1


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = "The number of bedrooms in the house"
    definition_period = YEAR


class is_shared_accommodation(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is shared accommodation"
    definition_period = YEAR


class household_weight(Variable):
    value_type = float
    entity = Household
    label = "Weight factor for the household"
    definition_period = YEAR


class Country(Enum):
    UNKNOWN = "Unknown"
    SCOTLAND = "Scotland"
    ENGLAND = "England"
    WALES = "Wales"
    NORTHERN_IRELAND = "Northern Ireland"


class country(Variable):
    value_type = Enum
    possible_values = Country
    default_value = Country.ENGLAND
    entity = Household
    label = "Country of the UK"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        region = household("region", period)
        return select(
            [
                region == Region.UNKNOWN,
                region == Region.SCOTLAND,
                region == Region.WALES,
                region == Region.NORTHERN_IRELAND,
                True,
            ],
            [
                Country.UNKNOWN,
                Country.SCOTLAND,
                Country.WALES,
                Country.NORTHERN_IRELAND,
                Country.ENGLAND,
            ],
        )


class Region(Enum):
    UNKNOWN = "Unknown"
    NORTH_EAST = "North East"
    NORTH_WEST = "North West"
    YORKSHIRE = "Yorkshire and the Humber"
    EAST_MIDLANDS = "East Midlands"
    WEST_MIDLANDS = "West Midlands"
    EAST_OF_ENGLAND = "East of England"
    LONDON = "London"
    SOUTH_EAST = "South East"
    SOUTH_WEST = "South West"
    WALES = "Wales"
    SCOTLAND = "Scotland"
    NORTHERN_IRELAND = "Northern Ireland"


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON
    entity = Household
    label = "Region"
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
    label = "Tenure type of the household"
    definition_period = YEAR


class is_renting(Variable):
    value_type = bool
    entity = Household
    label = "Is renting"
    definition_period = YEAR

    def formula(household, period, parameters):
        tenure = household("tenure_type", period)
        tenures = tenure.possible_values
        RENT_TENURES = [
            tenures.RENT_PRIVATELY,
            tenures.RENT_FROM_COUNCIL,
            tenures.RENT_PRIVATELY,
        ]
        return np.isin(tenure, RENT_TENURES)


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
    label = "Type of accommodation"
    definition_period = ETERNITY


class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = "Equivalisation factor to account for household composition, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        count_other_adults = max_(
            household.sum(household.members("is_adult", period)) - 1, 0
        )
        count_young_children = household.sum(
            household.members("is_young_child", period)
        )
        count_older_children = household.sum(
            household.members("is_older_child", period)
        )
        return (
            0.67
            + 0.33 * count_other_adults
            + 0.33 * count_older_children
            + 0.2 * count_young_children
        )


class household_equivalisation_ahc(Variable):
    value_type = float
    entity = Household
    label = "Equivalisation factor to account for household composition, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        count_other_adults = max_(
            household.sum(household.members("is_adult", period)) - 1, 0
        )
        count_young_children = household.sum(
            household.members("is_young_child", period)
        )
        count_older_children = household.sum(
            household.members("is_older_child", period)
        )
        return (
            0.58
            + 0.42 * count_other_adults
            + 0.42 * count_older_children
            + 0.2 * count_young_children
        )


class household_num_people(Variable):
    value_type = int
    entity = Household
    label = "Number of people"
    definition_period = YEAR
    unit = "person"

    def formula(household, period, parameters):
        return household.nb_persons()


class household_num_benunits(Variable):
    value_type = int
    entity = Household
    label = "Number of benefit units"
    definition_period = YEAR
    unit = "benefit unit"

    def formula(household, period, parameters):
        return household.sum(household.members("is_benunit_head", period))

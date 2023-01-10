from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


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
    definition_period = YEAR

    def formula(household, period, parameters):
        region = household("region", period)
        return select(
            [
                region == Region.UNKNOWN,
                region == Region.SCOTLAND,
                region == Region.WALES,
                region == Region.NORTHERN_IRELAND,
            ],
            [
                Country.UNKNOWN,
                Country.SCOTLAND,
                Country.WALES,
                Country.NORTHERN_IRELAND,
            ],
            default=Country.ENGLAND,
        )


class TenureType(Enum):
    RENT_FROM_COUNCIL = "Rented from Council"
    RENT_FROM_HA = "Rented from a Housing Association"
    RENT_PRIVATELY = "Rented privately"
    OWNED_OUTRIGHT = "Owned outright"
    OWNED_WITH_MORTGAGE = "Owned with a mortgage"


class ONSTenureType(Enum):
    RENT_FROM_COUNCIL = "Rented from Council"
    RENT_FROM_HA = "Rented from a Housing Association"
    RENT_PRIVATELY = "Rented privately"
    OWNER_OCCUPIED = "Owner occupied"


class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = "Tenure type of the household"
    definition_period = YEAR


class ons_tenure_type(Variable):
    label = "ONS tenure type"
    documentation = "Tenure type matching ONS_produced statistical breakdowns."
    entity = Household
    definition_period = YEAR
    value_type = Enum
    possible_values = ONSTenureType
    default_value = ONSTenureType.OWNER_OCCUPIED

    def formula(household, period, parameters):
        tenure = household("tenure_type", period)
        return select(
            [
                tenure == TenureType.RENT_FROM_HA,
                tenure == TenureType.RENT_FROM_COUNCIL,
                tenure == TenureType.RENT_PRIVATELY,
                tenure == TenureType.OWNED_OUTRIGHT,
                tenure == TenureType.OWNED_WITH_MORTGAGE,
            ],
            [
                ONSTenureType.RENT_FROM_HA,
                ONSTenureType.RENT_FROM_COUNCIL,
                ONSTenureType.RENT_PRIVATELY,
                ONSTenureType.OWNER_OCCUPIED,
                ONSTenureType.OWNER_OCCUPIED,
            ],
        )


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
        return is_in(tenure, RENT_TENURES)


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
    definition_period = YEAR


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


class household_count_people(Variable):
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

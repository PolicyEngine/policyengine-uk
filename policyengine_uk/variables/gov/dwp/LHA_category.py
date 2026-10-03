from policyengine_uk.model_api import *


class LHACategory(Enum):
    A = "Shared accommodation"
    B = "One bedroom"
    C = "Two bedrooms"
    D = "Three bedrooms"
    E = "Four or more bedrooms"


class LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = "LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms"
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C

    def formula(benunit, period, parameters):
        num_rooms = benunit("LHA_allowed_bedrooms", period.this_year)
        person = benunit.members
        household = person.household
        is_shared = benunit.any(household("is_shared_accommodation", period.this_year))
        can_only_claim_shared = benunit(
            "is_lha_shared_accommodation_rate_specified_renter", period
        )
        return select(
            [
                is_shared | can_only_claim_shared,
                num_rooms == 1,
                num_rooms == 2,
                num_rooms == 3,
                num_rooms > 3,
            ],
            [
                LHACategory.A,
                LHACategory.B,
                LHACategory.C,
                LHACategory.D,
                LHACategory.E,
            ],
        )

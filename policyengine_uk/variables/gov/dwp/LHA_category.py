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
        num_adults_in_hh = benunit.max(household.sum(person("is_adult", period)))
        eldest_adult_age_in_hh = benunit.max(household.max(person("age", period)))
        has_children = benunit.any(person("is_child", period))
        # Households with only one adult, if under age threshold, can only
        # claim shared if without children:
        # https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28
        p = parameters(period).gov.dwp.LHA
        can_only_claim_shared = (
            (num_adults_in_hh == 1)
            & (eldest_adult_age_in_hh < p.shared_accommodation_age_threshold)
            & ~has_children
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

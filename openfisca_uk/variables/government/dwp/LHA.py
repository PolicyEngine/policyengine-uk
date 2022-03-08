from openfisca_uk.model_api import *


class LHA_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = "Eligibility for Local Housing Allowance"
    documentation = (
        "Whether benefit unit is eligible for Local Housing Allowance"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        renting = benunit("benunit_is_renting", period)
        anyone_in_social_housing = benunit.any(
            benunit.members("in_social_housing", period)
        )
        return renting & ~anyone_in_social_housing


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10/2021-04-06"

    def formula(benunit, period, parameters):
        """
        LHA allows for one room for:
        a) The benefit unit adult(s)
        b) Each person over 16 outside the benefit unit
            but within the household
        Children must share rooms in pairs unless they are
        opposite-sex and one is over 10. The number of bedrooms
        allowed under LHA rules is the minimum number of bedrooms
        required to allocate people satisfying these rules.
        """
        person = benunit.members
        age = person("age", period)
        male = person("is_male", period)
        under_16 = age < 16
        under_10 = age < 10
        child_over_10 = ~under_10 & under_16
        # One room each for over-16s outside the benefit unit
        non_dependants = benunit.max(
            person.household.sum(~under_16)
        ) - benunit.sum(~under_16)
        boys_under_10 = benunit.sum(under_10 & male)
        boys_over_10 = benunit.sum(child_over_10 & male)
        girls_under_10 = benunit.sum(under_10 & ~male)
        girls_over_10 = benunit.sum(child_over_10 & ~male)
        # First, have over-10s share where possible
        over_10_rooms = (boys_over_10 + 1) // 2 + (girls_over_10 + 1) // 2
        # There may children over 10 still not sharing
        space_for_boy_under_10 = boys_over_10 % 2
        space_for_girl_under_10 = girls_over_10 % 2
        # Have those spaces filled where possible by children under 10
        left_over_boys_under_10 = max_(
            boys_under_10 - space_for_boy_under_10, 0
        )
        left_over_girls_under_10 = max_(
            girls_under_10 - space_for_girl_under_10, 0
        )
        # The remaining children must share in pairs
        under_10_rooms = (
            left_over_boys_under_10 + left_over_girls_under_10 + 1
        ) // 2
        return 1 + non_dependants + over_10_rooms + under_10_rooms


class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for LHA"
    documentation = "Applicable amount for Local Housing Allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        cap = benunit("BRMA_LHA_rate", period)
        return min_(rent, cap)


class LHACategory(Enum):
    A = "Shared"
    B = "1 Bed"
    C = "2 Bed"
    D = "3 Bed"
    E = "4+ Bed"


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
        is_shared = benunit.any(
            household("is_shared_accommodation", period.this_year)
        )
        num_adults_in_hh = benunit.max(
            household.sum(person("is_adult", period))
        )
        eldest_adult_age_in_hh = benunit.max(
            household.max(person("age", period))
        )
        # Households with only one adult, if under 35, can only claim shared.
        can_only_claim_shared = (num_adults_in_hh == 1) & (
            eldest_adult_age_in_hh < 35
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


class BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate"
    documentation = "Local Housing Allowance rate"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        BRMA = benunit.value_from_first_person(
            benunit.members.household("BRMA", period).decode_to_str()
        )
        category = benunit("LHA_category", period)
        rate = parameters(period).benefit.LHA.rates[BRMA][category]
        return rate * WEEKS_IN_YEAR

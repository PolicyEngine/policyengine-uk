from openfisca_uk.tools.general import *
from openfisca_uk.entities import *
import pandas as pd


class LHA_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = u"Whether eligible for Local Housing Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("benunit_is_renting", period) * not_(
            benunit.any(benunit.members("in_social_housing", period))
        )


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = u"The number of bedrooms covered by LHA for the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        children_under_10 = benunit.sum(benunit.members("age", period) < 10)
        male = benunit.members("is_male", period)
        under_16_male = benunit.sum(
            male * (benunit.members("age", period) < 16)
        )
        under_16_female = benunit.sum(
            not_(male) * (benunit.members("age", period) < 16)
        )
        return (
            (children_under_10 > 0).astype(int)
            + (under_16_male > 0).astype(int)
            + (under_16_female > 0).astype(int)
            + 1
        )


class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount for LHA"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        cap = benunit("BRMA_LHA_rate", period)
        amount = min_(rent, cap)
        return amount


class LHACategory(Enum):
    A = "Shared"
    B = "1 Bed"
    C = "2 Bed"
    D = "3 Bed"
    E = "4+ Bed"


class LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = u"LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms"
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C

    def formula(benunit, period, parameters):
        num_rooms = min_(
            benunit.value_from_first_person(
                benunit.members.household("num_bedrooms", period.this_year)
            ),
            benunit("LHA_allowed_bedrooms", period.this_year),
        )
        is_shared = (
            benunit.max(
                benunit.members.household(
                    "is_shared_accommodation", period.this_year
                )
            )
            > 0
        )
        can_only_claim_shared = (benunit("num_adults", period) == 1) & (
            benunit("eldest_adult_age", period) < 35
        )
        category = select(
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
        return category


class BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = u"LHA Rate"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        BRMA = benunit.value_from_first_person(
            benunit.members.household("BRMA", period).decode_to_str()
        )
        category = benunit("LHA_category", period)
        rate = parameters(period).benefit.LHA.rates[BRMA][category]
        return rate * WEEKS_IN_YEAR

from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class LHA_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = u"Whether eligible for Local Housing Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("benunit_is_renting", period) * not_(benunit.any(benunit.members("in_social_housing", period)))

class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = Household
    label = u'The number of bedrooms covered by LHA for the household'
    definition_period = YEAR

    def formula(household, period, parameters):
        children_under_10 = household.sum(household.members("age", period) < 10)
        male = household.members("is_male", period)
        under_16_male = household.sum(male * (household.members("age", period) < 16))
        under_16_female = household.sum(not_(male) * (household.members("age", period) < 16))
        return (children_under_10 > 0) + (under_16_male > 0) + (under_16_female > 0) + 1

class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount for LHA"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        rates = parameters(period).benefit.LHA.rate_caps
        rent = benunit.max(benunit.members.household("rent", period))
        num_rooms = min_(benunit.value_from_first_person(benunit.members.household("num_bedrooms", period.this_year)), benunit.value_from_first_person(benunit.members.household("LHA_allowed_bedrooms", period.this_year)))
        is_shared = (
            benunit.max(
                benunit.members.household("is_shared_accommodation", period.this_year)
            )
            > 0
        )
        rate_cap = select(
            [
                is_shared,
                num_rooms == 1,
                num_rooms == 2,
                num_rooms == 3,
                num_rooms > 3,
            ],
            [
                rates.shared,
                rates.beds_1,
                rates.beds_2,
                rates.beds_3,
                rates.beds_4,
            ],
        )
        amount = min_(rent, rate_cap)
        return amount
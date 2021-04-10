from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class LHA_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = u"Whether eligible for Local Housing Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.all(
            not_(benunit.members("living_in_social_housing", period))
            * benunit.members("is_renting", period)
        )


class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount for LHA"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        rates = parameters(period).benefits.LHA.rate_caps
        rent = benunit.max(benunit.members("personal_rent", period))
        num_rooms = benunit.max(
            benunit.members("num_rooms_in_household", period)
        )
        is_shared = (
            benunit.max(
                benunit.members("living_in_shared_accomodation", period)
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

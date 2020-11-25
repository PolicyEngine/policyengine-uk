from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class HousingType(Enum):
    SOCIAL = u"Social housing"
    PRIVATE = u"Private housing"


class housing_type(Variable):
    value_type = Enum
    possible_values = HousingType
    default_value = HousingType.PRIVATE
    entity = Household
    label = u"Whether private or social housing"
    definition_period = ETERNITY


class is_social(Variable):
    value_type = bool
    entity = Household
    label = u"Whether is social housing"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household("housing_type", period) == HousingType.SOCIAL


class is_rented(Variable):
    value_type = bool
    entity = Household
    label = u"Whether rented"
    definition_period = ETERNITY


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Total housing costs per week"
    definition_period = WEEK

    def formula(household, period, parameters):
        return household("rent", period) + household("mortgage", period)


class rent(Variable):
    value_type = float
    entity = Household
    label = u"Rent per week"
    definition_period = WEEK

    def formula(household, period, parameters):
        return household("weekly_rent", period.this_year)


class weekly_rent(Variable):
    value_type = float
    entity = Household
    label = u"Weekly rent for the year"
    definition_period = YEAR


class mortgage(Variable):
    value_type = float
    entity = Household
    label = u"Total mortgage payments"
    definition_period = WEEK


class num_rooms(Variable):
    value_type = int
    entity = Household
    label = u"Number of rooms in the household"
    definition_period = ETERNITY


class is_shared(Variable):
    value_type = bool
    entity = Household
    label = u"Whether using a shared household agreement"
    definition_period = ETERNITY


class council_tax(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax"
    definition_period = YEAR

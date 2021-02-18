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


class Tenure(Enum):
    unknown = u"unknown"
    owned = u"owned"
    mortgage = u"mortgage"
    part_own_part_rent = u"part_own_part_rent"
    rented = u"rented"
    rent_free = u"rent_free"
    squatting = u"squatting"


class tenure(Variable):
    value_type = Enum
    entity = Household
    possible_values = Tenure
    default_value = Tenure.rented
    label = u"The type of housing tenure"
    definition_period = ETERNITY


class total_housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Total housing costs (reported)"
    definition_period = YEAR


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Total housing costs per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        return household("total_housing_costs", period, options=[DIVIDE])


class rent(Variable):
    value_type = float
    entity = Household
    label = u"Rent per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(household, period, parameters):
        return household("weekly_rent", period.this_year)


class weekly_rent(Variable):
    value_type = float
    entity = Household
    label = u"Weekly rent for the year"
    definition_period = YEAR


class mortgage_payments(Variable):
    value_type = float
    entity = Household
    label = u"Total mortgage payments"
    definition_period = WEEK
    set_input = set_input_divide_by_period


class num_rooms(Variable):
    value_type = int
    entity = Household
    label = u"Number of rooms in the household"
    definition_period = ETERNITY


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = u"Number of bedrooms in the household"
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


class council_tax_bill(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax bill, after discounts"
    definition_period = YEAR

    def formula(household, period, parameters):
        return (1 - household("council_tax_discount", period)) * (
            household("council_tax", period)
        )


class council_tax_discount(Variable):
    value_type = float
    entity = Household
    label = u"Discount for Council Tax"
    definition_period = YEAR


class council_tax_benefit(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax Benefit"
    definition_period = YEAR


# Enums


class Council_tax_band(Enum):
    unknown = u"unknown"
    A = u"A"
    B = u"B"
    C = u"C"
    D = u"D"
    E = u"E"
    F = u"F"
    G = u"G"
    H = u"H"
    I = u"I"
    reported_unknown = u"unknown"


class Mortgage_type(Enum):
    unknown = u"unknown"
    endowment = u"endowment"
    repayment = u"repayment"
    pension = u"pension"
    ISA = u"ISA"
    endowment_and_repayment = u"endowment_and_repayment"
    interest_only_inv_linked = u"interest_only_inv_linked"
    interest_only_non_inv_linked = u"interest_only_non_inv_linked"
    other = u"other"


class Furnished(Enum):
    unknown = u"unknown"
    furnished = u"furnished"
    partially_furnished = u"partially_furnished"
    unfirnished = u"unfirnished"


class Landlord(Enum):
    unknown = u"unknown"
    local_authority = u"local_authority"
    housing_association = u"housing_association"
    employer_org = u"employer_org"
    other_org = u"other_org"
    relative_or_friend = u"relative_or_friend"
    employer_individual = u"employer_individual"
    other = u"other"

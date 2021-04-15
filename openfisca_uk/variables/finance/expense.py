from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class weekly_rent(Variable):
    value_type = float
    entity = Household
    label = u'Weekly average rent'
    definition_period = YEAR


class rent(Variable):
    value_type = float
    entity = Household
    label = u"Gross rent for the household"
    definition_period = WEEK

    def formula(household, period, parameters):
        return household("weekly_rent", period.this_year)

class personal_rent(Variable):
    value_type = float
    entity = Person
    label = u'Personal rent'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("rent", period, options=[ADD]) * person("is_household_head", period)



class family_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u'Gross rent for the family'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        personal_rent = benunit.members("personal_rent", period)
        return benunit.sum(personal_rent)


class childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u"Cost of childcare"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("weekly_childcare_cost", period.this_year)


class weekly_childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u"Average cost of childcare per week"
    definition_period = YEAR

class housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Total housing costs per week"
    definition_period = WEEK

    def formula(household, period, parameters):
        return household("rent", period) + household("mortgage", period)

class mortgage(Variable):
    value_type = float
    entity = Household
    label = u"Total mortgage payments"
    definition_period = WEEK

class council_tax(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax"
    definition_period = YEAR

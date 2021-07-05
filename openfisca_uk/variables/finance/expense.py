from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class weekly_rent(Variable):
    value_type = float
    entity = Household
    label = u"Weekly average rent"
    definition_period = YEAR


class rent(Variable):
    value_type = float
    entity = Household
    label = u"Gross rent for the household"
    definition_period = YEAR


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = u"Personal rent"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("rent", period) * person(
            "is_household_head", period
        )


class family_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u"Gross rent for the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        personal_rent = benunit.members("personal_rent", period)
        return benunit.sum(personal_rent)


class childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u"Cost of childcare"
    definition_period = YEAR


class weekly_childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u"Average cost of childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("childcare_cost", period) / WEEKS_IN_YEAR


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Total housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("rent", period) + household("mortgage", period)


class mortgage(Variable):
    value_type = float
    entity = Household
    label = u"Total mortgage payments"
    definition_period = YEAR


class council_tax(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax"
    definition_period = YEAR

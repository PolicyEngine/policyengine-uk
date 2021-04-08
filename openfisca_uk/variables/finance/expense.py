from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class rent(Variable):
    value_type = float
    entity = Household
    label = u'Gross rent for the household'
    definition_period = YEAR

class childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u'Cost of childcare'
    definition_period = WEEK

class weekly_childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u'Average cost of childcare per week'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("childcare_cost", period, options=[ADD]) / WEEKS_IN_YEAR
from policyengine_uk.model_api import *


class weekly_childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = "Average cost of childcare"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return person("childcare_expenses", period) / WEEKS_IN_YEAR

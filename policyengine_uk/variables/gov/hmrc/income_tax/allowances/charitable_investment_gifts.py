from policyengine_uk.model_api import *


class charitable_investment_gifts(Variable):
    value_type = float
    entity = Person
    label = "Gifts of qualifying investment or property to charities"
    definition_period = YEAR
    unit = GBP

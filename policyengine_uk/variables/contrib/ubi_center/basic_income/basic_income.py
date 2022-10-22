from policyengine_uk.model_api import *


class basic_income(Variable):
    label = "Basic income"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        bi_maximum = person("bi_maximum", period)
        bi_phaseout = person("bi_phaseout", period)
        return bi_maximum - bi_phaseout

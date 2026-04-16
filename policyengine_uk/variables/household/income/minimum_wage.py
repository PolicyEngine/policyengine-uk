from policyengine_uk.model_api import *
import datetime
import numpy as np


class minimum_wage(Variable):
    value_type = float
    entity = Person
    label = "Minimum wage"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        MW = parameters(period).gov.hmrc.minimum_wage
        is_apprentice = person("is_apprentice", period)
        age = person("age", period)
        return where(
            is_apprentice,
            MW.apprentice,
            MW.non_apprentice.calc(age),
        )

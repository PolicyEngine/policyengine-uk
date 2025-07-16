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
        p = parameters(period).gov.hmrc.minimum_wage
        return p[person("minimum_wage_category", period)]

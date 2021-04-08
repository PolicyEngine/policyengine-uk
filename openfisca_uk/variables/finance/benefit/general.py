from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

"""
This file contains variables that are commonly used in benefit eligibility calculations.
"""

class is_child(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is a child for benefits purposes'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 16

class is_QYP(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is a qualifying young person for benefits purposes'
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) < 20) * person("in_FE", period)

class is_child_or_QYP(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is a child or qualifying young person for most benefits'
    definition_period = YEAR
    
    def formula(person, period, parameters):
        return person("is_child", period) + person("is_QYP", period)


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is disabled for benefits purposes'
    definition_period = WEEK
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "DLA_M",
            "DLA_SC",
            "PIP_M",
            "PIP_DL",
        ]
        return add(person, period, QUALIFYING_BENEFITS, options=[ADD]) > 0

class is_severely_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is severely disabled for benefits purposes'
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        benefit = parameters(period).benefit
        threshold_safety_gap = 10
        paragraph_3 = person("DLA_SC", period) >= benefit.DLA.self_care.highest - threshold_safety_gap
        paragraph_4 = person("PIP_DL", period) >= benefit.PIP.daily_living.higher - threshold_safety_gap
        paragraph_5 = person("AFCS", period) > 0
        return sum([paragraph_3, paragraph_4, paragraph_5]) > 0


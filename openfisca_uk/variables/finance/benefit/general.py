from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

"""
This file contains variables that are commonly used in benefit eligibility calculations.
"""


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
        paragraph_3 = person("DLA_SC", period, options=[ADD]) / WEEKS_IN_YEAR >= benefit.DLA.self_care.highest - threshold_safety_gap
        paragraph_4 = person("PIP_DL", period, options=[ADD]) / WEEKS_IN_YEAR >= benefit.PIP.daily_living.higher - threshold_safety_gap
        paragraph_5 = person("AFCS", period, options=[ADD]) / WEEKS_IN_YEAR > 0
        return sum([paragraph_3, paragraph_4, paragraph_5]) > 0

class num_disabled_children(Variable):
    value_type = float
    entity = BenUnit
    label = u'Number of disabled children'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = benunit.members("is_disabled_for_benefits", period, options=[ADD]) > 0
        return benunit.sum(child * disabled)

class num_severely_disabled_children(Variable):
    value_type = float
    entity = BenUnit
    label = u'Number of severely disabled children'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = benunit.members("is_severely_disabled_for_benefits", period, options=[ADD]) > 0
        return benunit.sum(child * disabled)

class num_disabled_adults(Variable):
    value_type = float
    entity = BenUnit
    label = u'Number of disabled adults'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        disabled = benunit.members("is_disabled_for_benefits", period, options=[ADD]) > 0
        return benunit.sum(adult * disabled)

class num_severely_disabled_adults(Variable):
    value_type = float
    entity = BenUnit
    label = u'Number of severely disabled adults'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        disabled = benunit.members("is_severely_disabled_for_benefits", period, options=[ADD]) > 0
        return benunit.sum(adult * disabled)
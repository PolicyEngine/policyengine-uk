from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Housing Benefit (reported amount per week)"
    definition_period = WEEK

class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u'Housing Benefit for the family'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["housing_benefit_reported"])

class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for Housing Benefit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit.max(
            benunit.members("living_in_social_housing", period)
            * benunit.members("is_renting", period)
        ) * (benunit("housing_benefit_reported", period.this_year) > 0)


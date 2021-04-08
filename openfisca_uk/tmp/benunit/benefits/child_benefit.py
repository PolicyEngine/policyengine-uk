from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class child_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Child Benefit (reported amount)"
    definition_period = WEEK

class claims_child_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = u'Whether this family is imputed to claim Child Benefit, based on survey response and take-up rates'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["child_benefit_reported"], options=[ADD]) + (random(benunit) < parameters(period).benefit.child_benefit.takeup)

class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        num_children = benunit.nb_persons(BenUnit.CHILD)
        eldest_amount = (
            min_(num_children, 1)
            * parameters(period).benefits.child_benefit.amount.eldest
        )
        additional_amount = (
            max_(num_children - 1, 0)
            * parameters(period).benefits.child_benefit.amount.additional
        )
        return eldest_amount + additional_amount

from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class child_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Child Benefit (reported amount)"
    definition_period = YEAR


class benunit_child_benefit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit (reported amount)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("child_benefit_reported", period))


class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        num_children = benunit.nb_persons(BenUnit.CHILD)
        eldest_amount = (
            min_(num_children, 1)
            * parameters(period).benefits.child_benefit.amount_eldest
        )
        additional_amount = (
            max_(num_children - 1, 0)
            * parameters(period).benefits.child_benefit.amount_additional
        )
        return (eldest_amount + additional_amount) * (
            benunit("benunit_child_benefit_reported", period.this_year) > 0
        )

from openfisca_core.model_api import *
from openfisca_uk.entities import *


class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u"Pension contributions"
    definition_period = YEAR


class childcare(Variable):
    value_type = float
    entity = Person
    label = u"Childcare costs per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(person, period, parameters):
        return person("weekly_childcare", period.this_year)


class weekly_childcare(Variable):
    value_type = float
    entity = Person
    label = u"Weekly childcare for the year"
    definition_period = YEAR


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = u"The personal share of the rent"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(person, period, parameters):
        return person.household("rent", period) * person(
            "is_household_head", period
        )


class personal_housing_costs(Variable):
    value_type = float
    entity = Person
    label = u"The personal share of the rent"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(person, period, parameters):
        return person.household("housing_costs", period) * person(
            "is_household_head", period
        )


class is_renting(Variable):
    value_type = float
    entity = Person
    label = u"Whether renting"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(person, period, parameters):
        return person.household("rent", period) > 0


class maintenance_payments(Variable):
    value_type = float
    entity = Person
    label = u"Amount paid in maintenance per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period


class student_loan_repayment(Variable):
    value_type = float
    entity = Person
    label = u"Amount paid in student loan repayment per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period

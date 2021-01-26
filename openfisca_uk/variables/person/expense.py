from openfisca_core.model_api import *
from openfisca_uk.entities import *


class pension_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Pension contributions"
    definition_period = YEAR


class childcare_cost(Variable):
    value_type = float
    entity = Person
    label = u"Childcare cost"
    definition_period = WEEK
    set_input = set_input_divide_by_period


class weekly_childcare_hours(Variable):
    value_type = float
    entity = Person
    label = u"Weekly childcare hours"
    definition_period = WEEK


class tax_free_childcare_paid_in(Variable):
    value_type = float
    entity = Person
    label = u"Amount paid in to a Tax-Free childcare account"
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


class pension_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for pension contributions"
    definition_period = YEAR


class AVC_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for AVC"
    definition_period = YEAR


class union_fee_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for union fees"
    definition_period = YEAR


class friendly_society_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for Friendly Society fees"
    definition_period = YEAR


class club_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for work social/sports club fees"
    definition_period = YEAR


class loan_repayment_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for loan repayments"
    definition_period = ETERNITY


class medical_insurance_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for medical insurance"
    definition_period = YEAR


class charity_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for charitable donations"
    definition_period = YEAR


class student_loan_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for student loan repayments"
    definition_period = YEAR


class other_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Amount deducted from wages for other purposes"
    definition_period = YEAR


class payments_to_absent_partner(Variable):
    value_type = float
    entity = Person
    label = u"Amount paid to an absent partner"
    definition_period = YEAR


class salary_sacrifice_pension(Variable):
    value_type = float
    entity = Person
    label = u"Amount paid as a part of a Salary Sacrifice Pension scheme"
    definition_period = YEAR

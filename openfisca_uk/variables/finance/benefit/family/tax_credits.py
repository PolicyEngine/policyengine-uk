from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = WEEK


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = WEEK

class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u'Applicable income for Tax Credits'
    definition_period = YEAR
    reference = "The Tax Credits (Definition and Calculation of Income) Regulations 2002 s. 3"

    def formula(benunit, period, parameters):
        TC = parameters(period).benefit.tax_credits
        STEP_1_COMPONENTS = [
            "taxable_pension_income",
            "taxable_savings_interest_income",
            "taxable_dividend_income",
            "taxable_property_income",
        ]
        income = aggr(benunit, period, [STEP_1_COMPONENTS])
        income = amount_over(income, TC.applicable_income.non_earned_allowance)
        STEP_2_COMPONENTS = [
            "taxable_employment_income",
            "taxable_social_security_income",
            "taxable_miscellaneous_income"
        ]
        income += aggr(benunit, period, STEP_2_COMPONENTS)
        income += aggr(benunit, period, ["taxable_employment_income"])
        return income


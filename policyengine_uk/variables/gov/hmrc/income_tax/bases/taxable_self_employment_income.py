from policyengine_uk.model_api import *


class taxable_self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of trading income that is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act (Trading and Other Income) 2005, s. 5",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/5",
    )
    unit = GBP

    def formula(person, period, parameters):
        self_employment_income = person("self_employment_income", period)
        deductions_list = parameters(
            period
        ).gov.hmrc.income_tax.bases.taxable_self_employment_income_deductions
        deductions = add(person, period, deductions_list)
        return max_(0, self_employment_income - deductions)

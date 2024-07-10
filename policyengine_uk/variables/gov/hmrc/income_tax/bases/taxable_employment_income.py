from policyengine_uk.model_api import *


class taxable_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Net taxable earnings"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 11"
    unit = GBP

    def formula(person, period, parameters):
        taxable_earnings = person("employment_income", period)
        deductions = add(person, period, ["employment_deductions"])
        benefits = person("employment_benefits", period)
        return max_(0, taxable_earnings + benefits - deductions)

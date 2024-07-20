from policyengine_uk.model_api import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = "Total Income Tax liability"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    category = TAX

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax

        additions = add(person, period, p.income_tax_additions)
        subtractions = add(person, period, p.income_tax_subtractions)

        return max_(0, additions - subtractions)

from policyengine_uk.model_api import *


class property_income_after_finance_costs(Variable):
    value_type = float
    entity = Person
    label = "property income after finance costs"
    documentation = (
        "property_income less the year's costs of dwelling-related loans "
        "(property_finance_costs): the landlord's profit after mortgage "
        "interest. Income tax does not deduct these costs, and gives the "
        "finance-cost tax reduction instead, but the means tests that count "
        "property income count it after them. Tax credits do so by statute. "
        "The legacy means tests also deduct the person's income tax, which "
        "the reduction lowers, so counting the profit before the costs would "
        "make finance costs raise the income they count. Costs above the "
        "profit leave nil, not a loss set against other income."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="The Tax Credits (Definition and Calculation of Income) Regulations 2002 reg. 11(1) and (2A)",
        href="https://www.legislation.gov.uk/uksi/2002/2006/regulation/11",
    )

    def formula(person, period, parameters):
        profit = person("property_income", period)
        finance_costs = person("property_finance_costs", period)
        return where(profit > 0, max_(profit - finance_costs, 0), profit)

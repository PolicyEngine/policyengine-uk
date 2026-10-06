from policyengine_uk.model_api import *


class tax_credits_property_income(Variable):
    value_type = float
    entity = Person
    label = "property income for tax credits"
    documentation = (
        "Property income as tax credits count it: property_income less the "
        "costs of dwelling-related loans, which the tax credit rules deduct "
        "in full although income tax does not. Finance costs above the "
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

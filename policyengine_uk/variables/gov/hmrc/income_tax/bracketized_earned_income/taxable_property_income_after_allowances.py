from policyengine_uk.model_api import *


class taxable_property_income_after_allowances(Variable):
    value_type = float
    entity = Person
    label = "Property income for Income Tax after allowances"
    documentation = (
        "Taxable property income less the part of the allowances it absorbs. "
        "Allowances go to non-savings, non-dividend income first, and "
        "property income is stacked above the rest of it, so it takes "
        "whatever allowances the other non-savings income leaves."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 25(2)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
    )
    unit = GBP

    def formula(person, period, parameters):
        non_savings_after_allowances = max_(
            0,
            person("adjusted_net_income", period)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
            - person("allowances", period),
        )
        return min_(
            person("taxable_property_income", period), non_savings_after_allowances
        )

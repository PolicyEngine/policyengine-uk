from policyengine_uk.model_api import *


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    unit = GBP

    def formula(person, period, parameters):
        adjusted_net_income_components = parameters(
            period
        ).gov.hmrc.income_tax.adjusted_net_income_components

        # Find adjusted net income
        # Default behavior: Basic income not included in taxable income.
        # Use basic_income_interactions reform to change this.
        ani = add(person, period, adjusted_net_income_components)

        return max_(0, ani)

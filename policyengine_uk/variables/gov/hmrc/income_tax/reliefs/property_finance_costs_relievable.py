from policyengine_uk.model_api import *


class property_finance_costs_relievable(Variable):
    value_type = float
    entity = Person
    label = "residential property finance costs available for relief"
    documentation = (
        "The relievable amount for the finance-cost tax reduction: this "
        "year's finance costs that cannot be deducted from property profits, "
        "plus any amount brought forward from earlier years."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 274A(3)-(4)",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/274A",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.reliefs.property_finance_costs
        current_year = p.disallowed_share * person("property_finance_costs", period)
        return current_year + person("property_finance_costs_brought_forward", period)

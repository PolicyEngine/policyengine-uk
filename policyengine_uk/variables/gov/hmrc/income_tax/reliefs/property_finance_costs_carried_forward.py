from policyengine_uk.model_api import *


class property_finance_costs_carried_forward(Variable):
    value_type = float
    entity = Person
    label = "residential property finance costs carried forward"
    documentation = (
        "Finance costs left unrelieved this year, which become next year's "
        "property_finance_costs_brought_forward: the relievable amount less "
        "the costs relieved. Where the person uses the property allowance, "
        "this year's costs are among the expenses the allowance replaces, so "
        "only the amount brought forward is carried on."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 274AA(4)",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
    )

    def formula(person, period, parameters):
        relievable = where(
            person("uses_property_allowance", period),
            person("property_finance_costs_brought_forward", period),
            person("property_finance_costs_relievable", period),
        )
        return max_(0, relievable - person("property_finance_costs_relieved", period))

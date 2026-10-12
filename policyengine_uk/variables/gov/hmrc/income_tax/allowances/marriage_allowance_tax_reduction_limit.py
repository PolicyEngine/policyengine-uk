from policyengine_uk.model_api import *


class marriage_allowance_tax_reduction_limit(Variable):
    value_type = float
    entity = Person
    label = "Tax available for the Marriage Allowance reduction"
    documentation = (
        "Tax at Step 5 of the income tax calculation left after the person's "
        "other tax reductions. The Marriage Allowance tax reduction cannot "
        "exceed it. Each reduction is limited to the tax left after those "
        "before it, so the order changes how the total is split between "
        "them but not the total, which is the greatest reduction in "
        "liability. Deducting this one last makes it exactly the tax an "
        "election saves the gaining spouse. Double taxation relief should "
        "come after the Marriage Allowance (s. 27(6)), but other_tax_credits "
        "does not separate it out."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 29(2) and (3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
        dict(
            title="Income Tax Act 2007 s. 27(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/27",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        other_reductions = [
            variable
            for variable in income_tax.income_tax_subtractions
            if variable != "marriage_allowance_tax_reduction"
        ]
        step_5_tax = person("income_tax_pre_charges", period)
        return max_(0, step_5_tax - add(person, period, other_reductions))

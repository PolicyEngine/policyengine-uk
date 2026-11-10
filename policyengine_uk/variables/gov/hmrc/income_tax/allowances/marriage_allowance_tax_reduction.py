from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax_reductions import earlier_tax_reductions


class marriage_allowance_tax_reduction(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance tax reduction"
    documentation = (
        "The Marriage Allowance recipient's tax reduction at Step 6 of the "
        "Income Tax calculation: the appropriate percentage of the "
        "transferable amount (ITA 2007 s. 55A(2) and s. 55B(1)). It does not "
        "depend on the rates the recipient's income bears. The formula "
        "deducts it after the reductions listed before it in "
        "step_6_tax_reductions, and only so far as there is Step 5 tax left "
        "(s. 29(2) and (3))."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55A(2)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55A",
        ),
        dict(
            title="Income Tax Act 2007 s. 55B(1) and (3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Income Tax Act 2007 s. 29(2) and (3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        reduction = person("marriage_allowance_appropriate_percentage", period) * (
            person("marriage_allowance", period)
        )
        earlier = earlier_tax_reductions(income_tax, "marriage_allowance_tax_reduction")
        tax_left = max_(
            0,
            person("income_tax_pre_charges", period) - add(person, period, earlier),
        )
        return min_(max_(0, reduction), tax_left)

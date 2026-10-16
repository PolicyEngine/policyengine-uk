from policyengine_uk.model_api import *


class total_income_charged_to_tax(Variable):
    value_type = float
    entity = Person
    label = "Total income charged to Income Tax"
    documentation = (
        "Total income as ITA 2007 s.23 Step 1 defines it: the sum of the "
        "amounts of income on which the person is charged to Income Tax, "
        "before the Step 2 reliefs. These are the model's taxable income "
        "components, which already make the deductions the law makes in "
        "working out each kind of income: employment expenses, capital "
        "allowances, the trading and property allowances, and exempt ISA "
        "interest. Trade losses brought forward (loss_relief) are a Step 2 "
        "relief that the model deducts from trading profits, so they are "
        "added back. Unlike total_income, which sums gross income, this is "
        "the figure the law tests."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax
        profits = person("self_employment_income", period)
        other_deductions = [
            deduction
            for deduction in p.bases.taxable_self_employment_income_deductions
            if deduction != "loss_relief"
        ]
        profits_before_carry_forward = max_(
            0, profits - add(person, period, other_deductions)
        )
        losses_brought_forward_deducted = profits_before_carry_forward - person(
            "taxable_self_employment_income", period
        )
        return (
            person("net_income_before_trade_loss_relief", period)
            + losses_brought_forward_deducted
        )

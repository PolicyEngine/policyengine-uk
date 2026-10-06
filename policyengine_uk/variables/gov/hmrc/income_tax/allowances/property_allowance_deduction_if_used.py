from policyengine_uk.model_api import *


class property_allowance_deduction_if_used(Variable):
    value_type = float
    entity = Person
    label = "Deduction the property allowance gives if used"
    documentation = (
        "What the property allowance would deduct from property profits, "
        "beyond the expenses already deducted in them, if the person used it. "
        "The allowance replaces actual expenses rather than adding to them: "
        "receipts within the allowance are fully relieved, and above it the "
        "person may elect to deduct the allowance from receipts instead of "
        "their expenses, without creating a loss. With gross receipts "
        "supplied, this is the allowance less actual expenses, capped at "
        "profit. Without them, a profit within the allowance is treated as "
        "coming from receipts within it, and a larger profit as already "
        "reflecting the better of actual expenses and the allowance, so "
        "taxable profit jumps from nil to the full profit just above the "
        "allowance. Receipts below profit are inconsistent and treated as "
        "unknown."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BF (full relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BF",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BH (partial relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BH",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BI(4)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BI",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        allowance = parameters(period).gov.hmrc.income_tax.allowances.property_allowance
        receipts = person("property_rental_income", period)
        deductible_finance_costs = person("deductible_property_finance_costs", period)
        # Profit as computed with actual expenses, which include any finance
        # costs still deductible (before 2020-21). The allowance replaces all
        # of them.
        profit = person("property_income", period) - deductible_finance_costs
        expenses = person("property_allowable_expenses", period) + (
            deductible_finance_costs
        )
        # Receipts below profit (including the default zero) mean unknown.
        receipts_known = (receipts > 0) & (
            receipts >= person("property_income", period)
        )
        # Full relief (receipts within the allowance, s. 783BF) makes the
        # profit nil; partial relief (s. 783BH) replaces expenses with the
        # allowance. Both come to the allowance's excess over actual
        # expenses, capped at profit.
        relief_with_receipts = min_(profit, allowance - expenses)
        relief_without_receipts = where(profit <= allowance, profit, 0)
        relief = where(receipts_known, relief_with_receipts, relief_without_receipts)
        return max_(relief, 0)

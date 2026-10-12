from policyengine_uk.model_api import *


class trading_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction applied by the trading allowance"
    documentation = (
        "Relief from the trading allowance beyond the expenses already "
        "deducted in self_employment_income. The allowance replaces actual "
        "expenses and capital allowances rather than adding to them: receipts "
        "within the allowance are fully relieved, and above it the person may "
        "elect to deduct the allowance from receipts instead. With gross "
        "receipts supplied, the deduction is the allowance less actual "
        "expenses and capital allowances, capped at profit. Without them, a "
        "profit within the allowance is treated as coming from receipts within "
        "it, and a larger profit as already reflecting the better of actual "
        "expenses and the allowance, so taxable profit jumps from nil to the "
        "full profit just above the allowance. Receipts below profit are "
        "inconsistent and treated as unknown."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783AF (full relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AF",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783AI (partial relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AI",
        ),
        dict(
            title="HMRC Business Income Manual BIM86050",
            href="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim86050",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        allowance = parameters(period).gov.hmrc.income_tax.allowances.trading_allowance
        profit = person("self_employment_income", period)
        receipts = person("self_employment_gross_receipts", period)
        capital_allowances = person("capital_allowances", period)
        # Receipts below profit (including the default zero) mean unknown.
        receipts_known = (receipts > 0) & (receipts >= profit)
        expenses = max_(receipts - profit, 0)
        # Full relief (receipts within the allowance, s. 783AE-783AF) makes
        # the profit nil; partial relief (s. 783AI) replaces expenses and
        # capital allowances with the allowance. Both come to the allowance's
        # excess over actual deductions, capped at profit.
        relief_with_receipts = min_(profit, allowance - expenses) - capital_allowances
        relief_without_receipts = where(
            profit <= allowance, profit - capital_allowances, 0
        )
        relief = where(receipts_known, relief_with_receipts, relief_without_receipts)
        return max_(relief, 0)

from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


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
        "inconsistent and treated as unknown. The model compares the raw loss "
        "supplied for this tax year, before net-income and relief-cap limits, "
        "with the allowance's effective saving after other deductions. "
        "Ordinary expenses with a loss claim win when that raw loss is "
        "larger; allowance treatment otherwise, including ties. Comparing "
        "the raw loss can preserve an unused carry-forward even when both "
        "choices give nil current net income. Earlier inputs carried and "
        "uprated by the engine do not affect this election. It covers all "
        "the individual's relevant trades "
        "for the tax year. Allowance treatment makes their current losses "
        "nil for Income Tax and Class 4. It does not optimise future loss use "
        "or benefits."
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
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783AL (election)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AL",
        ),
        dict(
            title="HMRC Business Income Manual BIM86076 (loss election)",
            href="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim86076",
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
        relief = max_(relief, 0)
        # Full relief makes every relevant trade's current profit AND loss
        # nil (s.783AF); the opt-out is for the individual/year (s.783AL).
        # Partial relief also replaces every trade's actual expenses. Choose
        # ordinary treatment if the raw supplied current loss exceeds the
        # allowance saving. Before applying net-income and relief-cap limits,
        # this also preserves an unused loss if both choices give nil income.
        # Prior s.83 losses remain separate and may follow partial relief.
        profit_after_other_deductions = max_(
            0, profit - capital_allowances - person("loss_relief", period)
        )
        allowance_saving = min_(relief, profit_after_other_deductions)
        # An earlier input carried/uprated into this year is not a new loss
        # for the election, just as it is not a new Class 4 loss.
        current_loss = supplied_input(person, "trading_loss", period)
        if current_loss is None:
            current_loss = person.empty_array()
        claim_current_loss = current_loss > allowance_saving
        return where(claim_current_loss, 0, relief)

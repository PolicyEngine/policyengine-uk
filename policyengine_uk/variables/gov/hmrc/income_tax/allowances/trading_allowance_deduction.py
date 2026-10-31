from policyengine_uk.model_api import *
from policyengine_uk.utils.trading_allowance import trading_allowance_reliefs


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
        "inconsistent and treated as unknown. trading_allowance_claim_status, "
        "when known, takes precedence over receipts. A claimant's profit "
        "already deducts the allowance in force when it was measured "
        "(gov.simulation.trading_allowance_in_input_profits), so their "
        "receipts are their profit plus it and the deduction is the "
        "allowance's excess over it, capped at profit. A cut below that "
        "amount would raise a claimant's taxable profit by up to the "
        "difference, depending on expenses the data do not hold; the model "
        "leaves it as reported. A non-claimant deducts actual expenses above "
        "it and gets no deduction at any allowance, since electing for the "
        "allowance after a raise is a change in behaviour. "
        "The model compares the raw loss "
        "supplied for this tax year, before net-income and relief-cap limits, "
        "with the allowance's effective saving after other deductions, "
        "including its relief on miscellaneous income. "
        "Ordinary expenses with a loss claim win when that raw loss is "
        "larger; allowance treatment otherwise, including ties. Comparing "
        "the raw loss can preserve an unused carry-forward even when both "
        "choices give nil current net income. Earlier inputs carried and "
        "uprated by the engine do not affect this election. It covers all "
        "the individual's relevant trades "
        "for the tax year. Allowance treatment makes their current losses "
        "nil for Income Tax and Class 4. It does not optimise future loss use "
        "or benefits. The same allowance relieves income not otherwise "
        "charged (miscellaneous_income_trading_allowance_deduction), which "
        "gets only what the trade receipts leave of it."
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
        trade_relief, _ = trading_allowance_reliefs(person, period, parameters)
        return trade_relief

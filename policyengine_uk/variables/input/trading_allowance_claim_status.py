from policyengine_uk.model_api import *


class TradingAllowanceClaimStatus(Enum):
    UNKNOWN = "Unknown"
    CLAIMANT = "Claims the trading allowance"
    NON_CLAIMANT = "Does not claim the trading allowance"


class trading_allowance_claim_status(Variable):
    value_type = Enum
    possible_values = TradingAllowanceClaimStatus
    default_value = TradingAllowanceClaimStatus.UNKNOWN
    entity = Person
    label = "trading allowance claim status in the input data"
    documentation = (
        "Whether the person claimed the trading allowance in the tax year "
        "their input self-employment profit was measured. Survey data record "
        "profit, not gross receipts (turnover), and this says which receipts "
        "lie behind it, so that a change to the allowance reaches the right "
        "people. The year is the dataset's first year, which the engine "
        "projects to later years, or without a dataset the year simulated; "
        "the model reads the allowance legislated for it, which reforms do "
        "not move. The status describes a positive profit: a person with no "
        "profit has no trade receipts for it to describe, and a claimant is "
        "then read as UNKNOWN. CLAIMANT: the profit is receipts less that "
        "allowance, as on a return claiming partial relief (ITTOIA 2005 s. "
        "783AI), so the receipts are that profit plus the allowance, whatever "
        "self_employment_gross_receipts says. Partial relief replaces "
        "expenses and capital allowances, so capital_allowances supplied for "
        "a claimant are not deducted, and their claim was the election (s. "
        "783AM), so they keep the allowance, and give up current trading "
        "losses, at any allowance above nil. "
        "gov.simulation.trading_allowance_claimant_expense_share sets what a "
        "cut adds to their profit. Flag only profits net of the allowance: a "
        "person whose receipts were within it was fully relieved without a "
        "claim, and their profit, if reported, is not net of it; leave them "
        "UNKNOWN. NON_CLAIMANT: the profit is receipts less actual expenses, "
        "with capital_allowances deducted from it separately, and those "
        "deductions exceed the allowance. They did not elect for partial "
        "relief, and electing after a raise is a change in behaviour, so the "
        "allowance relieves their trades and their income not otherwise "
        "charged only through full relief, which needs no election (s. "
        "783AE): where supplied receipts, or that income alone with no "
        "profit, show relevant income within the allowance. UNKNOWN, the "
        "default: the allowance applies to self_employment_gross_receipts "
        "when they are supplied, and otherwise treats a profit within the "
        "allowance as receipts within it. For profits already net of the "
        "allowance, mark claimants and non-claimants here rather than set "
        "trading_allowance_deduction to zero, which keeps any change to the "
        "allowance from reaching them."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AI (partial relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AI",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AM (election for partial relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AM",
        ),
    ]

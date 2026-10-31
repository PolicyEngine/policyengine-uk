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
        "people. CLAIMANT: the profit is receipts less the allowance in force "
        "when it was measured (gov.simulation.trading_allowance_in_input_profits), "
        "as on a return claiming partial relief (ITTOIA 2005 s. 783AI), so the "
        "receipts are that profit plus that allowance. Flag only profits net "
        "of the allowance: a person whose receipts were within it was fully "
        "relieved, and their profit, if reported, is not net of it; leave them "
        "UNKNOWN. NON_CLAIMANT: the profit is receipts less actual expenses and "
        "capital allowances above that allowance. Their receipts are unknown, "
        "and electing for the allowance after a raise is a change in "
        "behaviour, so the allowance relieves neither their trades nor their "
        "income not otherwise charged, at any level. UNKNOWN, the default: "
        "the allowance applies to self_employment_gross_receipts when they "
        "are supplied, and otherwise treats a profit within the allowance as "
        "receipts within it. A claimant or non-claimant status takes "
        "precedence over self_employment_gross_receipts. For profits already "
        "net of the allowance, marking claimants and non-claimants here gives "
        "no deduction while the allowance stays at the input allowance, as "
        "setting trading_allowance_deduction to zero does, but lets a change "
        "to the allowance reach them."
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

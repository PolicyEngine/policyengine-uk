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
        "their input self-employment profit was measured, so that a change to "
        "the allowance reaches the right people when the data record profit "
        "but not receipts. That year is a dataset's first year, or for a "
        "situation the year simulated. The status describes a positive "
        "profit: with no profit, either status is read as UNKNOWN. CLAIMANT: "
        "the profit is receipts less that year's allowance (partial relief, "
        "ITTOIA 2005 s. 783AI). Flag only profits net of the allowance: leave "
        "a person whose receipts were within it, and so fully relieved, at "
        "UNKNOWN. NON_CLAIMANT: the profit is receipts less actual expenses "
        "above the allowance; they get the allowance only through full relief "
        "shown by supplied receipts. UNKNOWN, the default: the current "
        "treatment. Mark claimants here rather than set "
        "trading_allowance_deduction to zero, which keeps any change to the "
        "allowance from reaching them. The rules are in "
        "policyengine_uk/utils/trading_allowance.py."
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

from policyengine_uk.model_api import *


class income_not_otherwise_charged(Variable):
    value_type = float
    entity = Person
    label = "income not otherwise charged"
    documentation = (
        "The part of miscellaneous_income chargeable to income tax under ITTOIA "
        "2005 Part 5 Chapter 8 (s. 687): income from a source no other "
        "provision charges, such as casual income that does not come from a "
        "trade. It is part of miscellaneous_income, not added to it, and counts "
        "up to miscellaneous_income where that is positive. This is the "
        '"miscellaneous income" the trading allowance relieves (s. 783AB), '
        "measured before expenses; the model holds no expenses against it. "
        "Optional: used only to apply the trading allowance. Leave it at zero "
        "when unknown. The survey data do not separate it from the rest of "
        "miscellaneous_income, which also holds royalties, charges under other "
        "Part 5 Chapters and, on SPI records, benefits and termination "
        "payments, none of which the allowance relieves. Without "
        "self_employment_gross_receipts, a trade with a loss or no profit is "
        "taken to have no receipts, so its relevant income is this alone. "
        "A claimant's trade receipts (trading_allowance_claim_status) take up "
        "the allowance first, and a non-claimant gets none of it on this "
        "income."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 687",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/687",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AB",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AB",
        ),
    ]
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

from policyengine_uk.model_api import *
from policyengine_uk.utils.trading_allowance import trading_allowance_reliefs


class miscellaneous_income_trading_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction from miscellaneous income applied by the trading allowance"
    documentation = (
        "The trading allowance's relief on income not otherwise charged "
        "(ITTOIA 2005 Part 5 Chapter 8), the miscellaneous income Part 6A "
        "covers alongside trade receipts. One allowance covers both. When "
        "trade receipts and this income together are within it, both are "
        "relieved in full (ss. 783AE, 783AF and 783AG). Above it, the person "
        "can elect to deduct the allowance, split between them as they "
        "choose, in place of actual expenses (ss. 783AI-783AK); the model "
        "gives the trades their receipts' worth first, so this income gets "
        "the part of the allowance the trade receipts leave, even where trade "
        "losses brought forward would absorb the trade's share (see "
        "utils/trading_allowance.py). Ordinary treatment to claim a current "
        "trading loss (no full relief, s. 783AL, or no partial relief, s. "
        "783AM) leaves it unrelieved. Only "
        "income tax reads this deduction, through taxable_miscellaneous_income; "
        "means tests and gross income bases read "
        "miscellaneous_income_before_trading_allowance. Datasets that hold "
        "income already net of the allowance should set it to zero, as "
        "policyengine-uk-data does for trading_allowance_deduction on SPI "
        "records."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AB",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AB",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AG (full relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AG",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AJ (partial relief)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AJ",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AK (splitting the allowance)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AK",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        _, miscellaneous_relief = trading_allowance_reliefs(person, period, parameters)
        return miscellaneous_relief

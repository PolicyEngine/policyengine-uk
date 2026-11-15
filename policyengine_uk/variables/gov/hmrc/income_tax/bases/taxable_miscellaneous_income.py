from policyengine_uk.model_api import *


class taxable_miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of miscellaneous income that is taxable"
    documentation = (
        "Miscellaneous income charged to income tax: "
        "miscellaneous_income_before_trading_allowance, in which a net loss "
        "counts as nil, less the trading allowance's relief on income not "
        "otherwise charged (miscellaneous_income_trading_allowance_deduction). "
        "Income tax reads this figure; means tests and gross income bases read "
        "the figure before the allowance."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 574",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/574",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 688(2)(za)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/688",
        ),
        dict(
            title="Income Tax Act 2007 s. 152",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/152",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return person("miscellaneous_income_before_trading_allowance", period) - person(
            "miscellaneous_income_trading_allowance_deduction", period
        )

from policyengine_uk.model_api import *


class miscellaneous_income_before_trading_allowance(Variable):
    value_type = float
    entity = Person
    label = "Miscellaneous income before the trading allowance"
    documentation = (
        "Miscellaneous income with a net loss counted as nil, before the "
        "trading allowance relieves income not otherwise charged. Means tests "
        "and gross income bases read this figure, as they read a trade's "
        "profit before the allowance: the allowance is an income tax relief. "
        "Income tax reads taxable_miscellaneous_income, which is this less "
        "miscellaneous_income_trading_allowance_deduction. A loss on a "
        "miscellaneous transaction is relieved only against income under the "
        "same section 1016 provision (ITA 2007 s. 152(4)-(5)) and never set "
        "against other income, which is why a net loss counts as nil. The "
        "model holds one net figure per person, so it assumes the items netted "
        "inside miscellaneous_income can be relieved against each other; that "
        "can undertax a person with a gain under one provision and a loss "
        "under another. The input also covers income from sources outside "
        "section 1016, some of which carry no loss relief at all. Carrying a "
        "loss forward against later years' miscellaneous income is not "
        "modelled."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 574",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/574",
        ),
        dict(
            title="Income Tax Act 2007 s. 152",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/152",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return max_(0, person("miscellaneous_income", period))

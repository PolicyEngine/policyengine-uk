from policyengine_uk.model_api import *


class uses_trading_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Uses the trading allowance"
    documentation = (
        "Whether the person takes the trading allowance for the year, by full "
        "or partial relief, rather than ordinary treatment: the allowance "
        "relieves their trade profits or their income not otherwise charged. "
        "Either relief covers all their relevant income (ITTOIA 2005 s. 783A), "
        "so it makes every relevant trade's current profit or loss its "
        "allowance figure (ss. 783AF and 783AI), and a current trading loss "
        "cannot then be claimed. A person with a larger current loss takes "
        "ordinary treatment and claims it: within the allowance by electing "
        "out of full relief (s. 783AL), above it by not electing for partial "
        "relief (s. 783AM)."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783A",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783A",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AL",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AL",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AM",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AM",
        ),
    ]

    def formula(person, period, parameters):
        return (person("trading_allowance_deduction", period) > 0) | (
            person("miscellaneous_income_trading_allowance_deduction", period) > 0
        )

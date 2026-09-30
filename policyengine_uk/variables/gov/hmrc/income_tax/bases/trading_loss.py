from policyengine_uk.model_api import *


class trading_loss(Variable):
    value_type = float
    entity = Person
    label = "Loss from trading in the current year."
    documentation = (
        "Trading losses made in the year. self_employment_income holds the "
        "profits of trades that made one, so a loss here alongside a profit "
        "comes from a different trade. Like other inputs, a value carries "
        "into later years that are not set, so set them to zero for a "
        "one-off loss."
    )
    reference = dict(
        title="Income Tax Act 2007 s. 64",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/64",
    )
    definition_period = YEAR
    unit = GBP

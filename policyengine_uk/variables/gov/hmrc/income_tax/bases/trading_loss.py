from policyengine_uk.model_api import *


class trading_loss(Variable):
    value_type = float
    entity = Person
    label = "Loss from trading in the current year."
    reference = dict(
        title="Income Tax Act 2007 s. 64",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/64",
    )
    definition_period = YEAR
    unit = GBP

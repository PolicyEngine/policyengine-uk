from policyengine_uk.model_api import *


class taxable_miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of miscellaneous income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 574"
    unit = GBP

    adds = ["miscellaneous_income"]

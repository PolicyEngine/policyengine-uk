from policyengine_uk.model_api import *


class taxable_miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of miscellaneous income that is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act (Trading and Other Income) 2005, s. 574",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/574",
    )
    unit = GBP

    adds = ["miscellaneous_income"]

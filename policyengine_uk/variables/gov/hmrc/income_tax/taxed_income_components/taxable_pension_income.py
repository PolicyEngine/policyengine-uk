from policyengine_uk.model_api import *


class taxable_pension_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of pension income that is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003, s. 567",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/567",
    )
    unit = GBP

    adds = ["private_pension_income"]

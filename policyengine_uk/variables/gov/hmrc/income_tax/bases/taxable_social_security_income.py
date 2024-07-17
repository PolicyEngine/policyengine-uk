from policyengine_uk.model_api import *


class taxable_social_security_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of social security income that is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003, s. 658",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/658",
    )
    unit = GBP

    adds = ["social_security_income"]

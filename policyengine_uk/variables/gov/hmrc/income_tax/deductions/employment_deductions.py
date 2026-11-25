from policyengine_uk.model_api import *


class employment_deductions(Variable):
    value_type = float
    entity = Person
    label = "Deductions from employment income"
    documentation = (
        "Allowable employment expenses under Part 5 of ITEPA and Payroll "
        "Giving donations under Part 12. Each input is the legally allowed "
        "amount. Part 5 expenses are limited to the earnings remaining "
        "after deductions outside that Part (ITEPA s. 329(3))."
    )
    definition_period = YEAR
    reference = (
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 327(3)-(5)",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/327",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 713",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/713",
        ),
    )
    unit = GBP

    adds = ["employment_expenses", "payroll_giving"]

from policyengine_uk.model_api import *


class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = (
        "Cost of expenses necessarily incurred and reimbursed by employment"
    )
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"
    unit = GBP

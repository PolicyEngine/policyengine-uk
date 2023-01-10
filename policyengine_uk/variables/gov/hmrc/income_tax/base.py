from policyengine_uk.model_api import *

"""
The calculation of income tax is specified by the Income Tax Act 2007 s. 23
which outlines the main steps. Step 1 indicates that the components of 'total income'
should be added together, but the Act itself does not specify what those components are.
Instead, other Acts (the Income Tax (Earnings and Pensions) Act 2003 and the Income Tax 
(Trading and Other Income) Act 2005) impose the charges to income tax on each component of
income. The relevant sections of each act imposing charges to income tax are given 
for each component of income below. The components are guided by the article at 
https://www.pruadviser.co.uk/knowledge-literature/knowledge-library/the-seven-steps-required-to-calculate-an-individuals-income-tax-liability/
"""


class total_pension_income(Variable):
    label = "Total pension income"
    documentation = "Private, personal and State Pension income"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["pension_income", "state_pension"]


class social_security_income(Variable):
    value_type = float
    entity = Person
    label = "Income from social security for tax purposes"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    unit = GBP

    adds = [
        "state_pension",
        "incapacity_benefit",
        "JSA_contrib",
        "ESA_contrib",
        "carers_allowance",
    ]

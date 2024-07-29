from policyengine_uk.model_api import *

"""
The section detailing some tax reliefs applicable is section 24 of the Act, but others are described in the 2003 and 2005 Acts as deductions from the respective components.
"""


class capital_allowances(Variable):
    value_type = float
    entity = Person
    label = "Full relief from capital expenditure allowances"
    definition_period = YEAR
    reference = dict(
        title="Capital Allowances Act 2001 s. 1",
        href="https://www.legislation.gov.uk/ukpga/2001/2/section/1",
    )
    unit = GBP

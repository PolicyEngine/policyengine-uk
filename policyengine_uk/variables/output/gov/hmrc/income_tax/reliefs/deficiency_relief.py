from policyengine_uk.model_api import *

"""
The section detailing some tax reliefs applicable is section 24 of the Act, but others are described in the 2003 and 2005 Acts as deductions from the respective components.
"""


class deficiency_relief(Variable):
    value_type = float
    entity = Person
    label = "Deficiency relief"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007, Part 4",
        href="https://www.legislation.gov.uk/ukpga/2007/3/part/4",
    )

from policyengine_uk.model_api import *

"""
The section detailing some tax reliefs applicable is section 24 of the Act, but others are described in the 2003 and 2005 Acts as deductions from the respective components.
"""


class loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Trade losses brought forward"
    reference = dict(
        title="Income Tax Act 2007 s. 83",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/83",
    )
    documentation = (
        "Unrelieved trade losses of earlier years deducted from this year's "
        "profits of the same trade (ITA 2007 s.83). Deducted from "
        "self-employment income only, and never below zero. A loss made in "
        "this year goes in trading_loss, which is relieved against general "
        "income instead (s.64); whatever part of it this year's income cannot "
        "absorb is carried forward by entering it here in later years."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

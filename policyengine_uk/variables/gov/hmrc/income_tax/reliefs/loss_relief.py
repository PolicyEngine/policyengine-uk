from policyengine_uk.model_api import *


"""
The section detailing some tax reliefs applicable is section 24 of the Act, but others are described in the 2003 and 2005 Acts as deductions from the respective components.
"""


class loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Tax relief from trading losses"
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005 s. 59",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/59",
    )
    documentation = "Can be set against general income."
    unit = GBP

    def formula(person, period, parameters):
        current_loss = person("trading_loss", period)
        previous_loss = person("trading_loss", period.last_year)
        return current_loss + previous_loss

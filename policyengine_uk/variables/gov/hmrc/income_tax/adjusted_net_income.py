from policyengine_uk.model_api import *


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = "Adjusted net income"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 58",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/58",
    )
    unit = GBP

    def formula(person, period, parameters):
        # ITA 2007 s.58, Step 2: deduct the gift grossed up at the basic rate.
        # This adjustment affects the PA taper and HICBC, not taxable income.
        return person("net_income", period) - person("gift_aid_grossed_up", period)

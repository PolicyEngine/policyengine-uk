from policyengine_uk.model_api import *


class taxable_property_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of property income that is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 268",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/268",
    )
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            person("property_income", period)
            - person("property_allowance", period),
        )

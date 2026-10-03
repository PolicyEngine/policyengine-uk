from policyengine_uk.model_api import *


class taxable_property_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of property income that is taxable"
    documentation = (
        "Property income less the property allowance, plus rent-a-room "
        "receipts above the rent-a-room limit, which are profits of the same "
        "UK property business but are not relievable receipts for the "
        "property allowance."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 268",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/268",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BB(2)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BB",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            person("property_income", period)
            - person("property_allowance_deduction", period),
        ) + person("taxable_rent_a_room_income", period)

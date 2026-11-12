from policyengine_uk.model_api import *


class taxable_rent_a_room_income(Variable):
    value_type = float
    entity = Person
    label = "taxable rent-a-room income"
    documentation = (
        "Rent-a-room receipts above the individual's limit, brought into "
        "account as profits of a UK property business. They are not "
        "relievable receipts for the property allowance."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2005/5/section/797",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/783BB",
    ]

    def formula(person, period, parameters):
        return person("rent_a_room_receipts", period) - person(
            "rent_a_room_relief", period
        )

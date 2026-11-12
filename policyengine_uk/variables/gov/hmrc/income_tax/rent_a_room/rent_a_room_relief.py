from policyengine_uk.model_api import *


class rent_a_room_relief(Variable):
    value_type = float
    entity = Person
    label = "rent-a-room relief"
    documentation = (
        "Rent-a-room receipts not charged to income tax. Receipts up to the "
        "limit are not brought into account (full relief). Above the limit "
        "the model assumes the individual elects for the alternative method, "
        "under which the limit is deducted from the receipts and no expenses "
        "are allowed; the data hold no expenses for this income."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2005/5/section/793",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/797",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/800",
    ]

    def formula(person, period, parameters):
        return min_(
            person("rent_a_room_receipts", period),
            person("rent_a_room_limit", period),
        )

from policyengine_uk.model_api import *


class rent_a_room_limit(Variable):
    value_type = float
    entity = Person
    label = "rent-a-room relief limit"
    documentation = (
        "The basic amount, or half of it where the individual does not meet "
        "the exclusive receipts condition. The model takes the condition to "
        "fail where the individual and another member of the household both "
        "have rent-a-room receipts from the home."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2005/5/section/789",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/790",
    ]

    def formula(person, period, parameters):
        basic_amount = parameters(period).gov.hmrc.income_tax.rent_a_room.basic_amount
        receives = person("rent_a_room_receipts", period) > 0
        others_receive = person.household.sum(receives) - receives > 0
        return where(receives & others_receive, basic_amount / 2, basic_amount)

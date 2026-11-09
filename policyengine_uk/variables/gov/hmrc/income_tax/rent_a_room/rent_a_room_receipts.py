from policyengine_uk.model_api import *


class rent_a_room_receipts(Variable):
    value_type = float
    entity = Person
    label = "rent-a-room receipts"
    documentation = (
        "Receipts for the use of furnished accommodation in the individual's "
        "only or main residence, including meals and other services supplied "
        "with it: rent from boarders and lodgers who live in the household, "
        "and rent from letting part of the home to someone outside it. The "
        "model treats all of it as furnished accommodation."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2005/5/section/786"
    adds = ["rent_from_boarders_and_lodgers", "sublet_income"]

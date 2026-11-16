from policyengine_uk.model_api import *


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = "sublet income"
    documentation = (
        "Rent this person receives for letting part of the home they live in "
        "to someone who is not a member of the household. Income tax treats "
        "it as rent-a-room receipts, and the legacy means tests count it less "
        "a weekly disregard. Rent from other property is property_income; "
        "rent from boarders and lodgers who live in the household is "
        "rent_from_boarders_and_lodgers."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

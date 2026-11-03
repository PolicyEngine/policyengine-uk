from policyengine_uk.model_api import *


class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent"
    documentation = (
        "Rent that members of this family are liable for: the family's share "
        "of the household's rent, plus anything its members pay the "
        "householder as boarders or lodgers."
    )
    definition_period = YEAR
    unit = GBP
    adds = ["personal_rent"]

from policyengine_uk.model_api import *


class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent"
    documentation = "Gross rent that members of this family are liable for"
    definition_period = YEAR
    unit = GBP

    adds = ["personal_rent"]

from policyengine_uk.model_api import *


class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent"
    documentation = "Gross rent that members of this family are liable for (social housing only)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.social_rent"
    adds = ["personal_rent"]

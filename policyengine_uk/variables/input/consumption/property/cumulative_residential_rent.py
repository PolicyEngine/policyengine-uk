from policyengine_uk.model_api import *


class cumulative_residential_rent(Variable):
    label = "Cumulative residential rent"
    documentation = "Total rent paid over the lifetime of the residential property a tenancy is held for."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

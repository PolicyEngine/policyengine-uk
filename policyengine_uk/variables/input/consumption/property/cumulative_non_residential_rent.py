from policyengine_uk.model_api import *


class cumulative_non_residential_rent(Variable):
    label = "Cumulative non-residential rent"
    documentation = "Total rent paid over the lifetime of the non-residential property a tenancy is held for."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

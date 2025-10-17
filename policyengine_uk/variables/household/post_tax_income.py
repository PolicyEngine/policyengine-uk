from policyengine_uk.model_api import *


class post_tax_income(Variable):
    label = "post-tax income"
    documentation = "The income of a household after taxes have been deducted."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["total_income"]
    subtracts = ["income_tax", "national_insurance"]

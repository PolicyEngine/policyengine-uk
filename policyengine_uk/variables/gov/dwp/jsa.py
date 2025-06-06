from policyengine_uk.model_api import *


class jsa(Variable):
    value_type = float
    entity = BenUnit
    label = "Amount of Jobseeker's Allowance for this family"
    definition_period = YEAR
    unit = GBP
    adds = ["jsa_income", "jsa_contrib"]

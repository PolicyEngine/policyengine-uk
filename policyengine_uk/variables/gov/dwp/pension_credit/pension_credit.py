from policyengine_uk.model_api import *


class pension_credit(Variable):
    label = "Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/contents"
    defined_for = "would_claim_pc"
    adds = ["pension_credit_entitlement"]

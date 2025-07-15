from policyengine_uk.model_api import *


class claims_legacy_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims legacy benefits"
    documentation = "Whether this family is currently receiving legacy benefits (overrides UC claimant status)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        BENEFITS = [
            "child_tax_credit_reported",
            "working_tax_credit_reported",
            "housing_benefit_reported",
            "esa_income_reported",
            "income_support_reported",
            "jsa_income_reported",
        ]

        return add(benunit, period, BENEFITS) > 0

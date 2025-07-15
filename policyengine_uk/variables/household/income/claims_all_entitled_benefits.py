from policyengine_uk.model_api import *


class claims_all_entitled_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims all eligible benefits"
    definition_period = YEAR
    documentation = (
        "Whether this family would claim any benefit they are entitled to"
    )

    def formula(benunit, period, parameters):
        # Return false if we have any reported values in the simulation for benefits.
        return (
            add(
                benunit,
                period,
                [
                    "child_tax_credit_reported",
                    "working_tax_credit_reported",
                    "universal_credit_reported",
                    "housing_benefit_reported",
                    "jsa_income_reported",
                    "income_support_reported",
                    "esa_income_reported",
                ],
            ).sum()
            < 1
        )

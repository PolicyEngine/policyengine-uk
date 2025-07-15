from policyengine_uk.model_api import *


class benefit_cap_reduction(Variable):
    label = "benefit cap reduction"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        CAPPED_BENEFITS = [
            "child_benefit",
            "child_tax_credit",
            "jsa_income",
            "income_support",
            "esa_income",
            "universal_credit_pre_benefit_cap",
            "housing_benefit_pre_benefit_cap",
            "jsa_contrib",
            "incapacity_benefit",
            "esa_contrib",
            "sda",
        ]
        return max_(
            add(benunit, period, CAPPED_BENEFITS)
            - benunit("benefit_cap", period),
            0,
        )

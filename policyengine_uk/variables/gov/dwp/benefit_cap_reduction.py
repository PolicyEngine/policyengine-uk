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
        # The cap applies to "the welfare benefits to which a single person or
        # couple is entitled" (WRA 2012 s. 96(1); UC Regs 2013 reg. 80(1)), so
        # a dependant's own contributory benefit is not part of the total.
        claimants = benunit.members("is_uc_assessed_claimant", period)
        total = add_for_members(benunit, period, CAPPED_BENEFITS, claimants)
        return max_(total - benunit("benefit_cap", period), 0)

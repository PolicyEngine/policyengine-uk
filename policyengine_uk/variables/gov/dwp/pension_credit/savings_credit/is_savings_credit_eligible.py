from policyengine_uk.model_api import *


class is_savings_credit_eligible(Variable):
    label = "Eligible for Savings Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/3"

    def formula(benunit, period, parameters):
        # Check if any member reached SPA before the cutoff year
        has_pre_cutoff_spa_member = benunit.any(
            benunit.members("meets_savings_credit_age_requirement", period)
        )
        income = benunit("savings_credit_income", period)
        sc = parameters(period).gov.dwp.pension_credit.savings_credit
        relation_type = benunit("relation_type", period)
        threshold = sc.threshold[relation_type]
        meets_income_threshold = income >= threshold
        return has_pre_cutoff_spa_member & meets_income_threshold

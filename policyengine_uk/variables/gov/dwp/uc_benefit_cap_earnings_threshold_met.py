from policyengine_uk.model_api import *


class uc_benefit_cap_earnings_threshold_met(Variable):
    value_type = bool
    entity = BenUnit
    label = "Earned income reaches the Universal Credit benefit cap earnings threshold"
    documentation = (
        "Whether the claimant's earned income, or a couple's combined earned "
        "income, is at least the pay for 16 hours a week at the national "
        "living wage (UC Regs 2013 reg. 82(1)(a)). The benefit cap earnings "
        "exception also needs an award of Universal Credit."
    )
    definition_period = YEAR
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 82(1)(a)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
    )

    def formula(benunit, period, parameters):
        earned_income = benunit("benefit_cap_earned_income", period)
        threshold = benunit("benefit_cap_earnings_threshold", period)
        return earned_income >= threshold

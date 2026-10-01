from policyengine_uk.model_api import *


class is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether excepted from the benefit cap because of earnings"
    documentation = (
        "The Universal Credit earnings exception: the benefit cap does not "
        "apply where the claimant's earned income, or a couple's combined "
        "earned income, reaches the pay for 16 hours a week at the national "
        "living wage. The nine-month grace period after twelve months of "
        "such earnings is not modelled."
    )
    definition_period = YEAR
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 82(1)(a)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
    )

    def formula(benunit, period, parameters):
        # Only earned income is read, not the Universal Credit award, which
        # depends on the cap.
        earned_income = benunit("benefit_cap_earned_income", period)
        threshold = benunit("benefit_cap_earnings_threshold", period)
        return earned_income >= threshold

from policyengine_uk.model_api import *


class is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether excepted from the benefit cap because of earnings"
    documentation = (
        "The Universal Credit earnings exception: the benefit cap does not "
        "apply to an award of Universal Credit where the claimant's earned "
        "income, or a couple's combined earned income, reaches the pay for "
        "16 hours a week at the national living wage. It does not apply to "
        "Housing Benefit, whose cap has its own exceptions (HB Regs 2006 "
        "regs. 75E and 75F; entitlement to Working Tax Credit is in "
        "is_benefit_cap_exempt_health_disability). The nine-month grace "
        "period is not modelled."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 82(1)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        ),
        dict(
            title="Housing Benefit Regulations 2006 reg. 75E",
            href="https://www.legislation.gov.uk/uksi/2006/213/regulation/75E",
        ),
    ]

    def formula(benunit, period, parameters):
        # Reg. 82(1): "The benefit cap does not apply to an award of
        # universal credit ...". The award before the cap is read, since the
        # award after it depends on this exception.
        has_uc_award = benunit("universal_credit_pre_benefit_cap", period) > 0
        threshold_met = benunit("uc_benefit_cap_earnings_threshold_met", period)
        return has_uc_award & threshold_met

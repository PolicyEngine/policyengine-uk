from policyengine_uk.model_api import *


class is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the benefit cap because of earnings"
    definition_period = YEAR
    reference = "https://www.gov.uk/benefit-cap/when-youre-not-affected"

    def formula(benunit, period, parameters):
        person = benunit.members

        # Earnings exemption for UC (£846/month = £10,152/year)
        # Note: Only check earned income, not UC amount itself to avoid circular dependency
        # UC Regs 2013 reg. 82(1)(a) tests "the claimant's earned income or,
        # if the claimant is a member of a couple, the couple's combined
        # earned income": a dependant's earnings do not count.
        claimant = person("is_uc_assessed_claimant", period)
        # Use actual earnings under regs. 55, 57 and 77, before the MIF.
        # This nets concurrent trades (including the company's trade) and
        # keeps trade-only tax/NI deductions from reducing employed earnings.
        uc_earned = benunit.sum(
            person("uc_individual_earned_income_before_mif", period) * claimant
        )
        earnings_threshold = 10_152
        return uc_earned >= earnings_threshold

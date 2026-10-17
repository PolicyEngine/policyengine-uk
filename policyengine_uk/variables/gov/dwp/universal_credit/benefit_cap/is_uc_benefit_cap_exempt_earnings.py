from policyengine_uk.model_api import *


class is_uc_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Universal Credit benefit cap because of earnings"
    documentation = (
        "Whether the claimant's earned income, or a couple's combined earned "
        "income, reaches the earnings threshold (UC Regs 2013 reg. 82(1)(a)). "
        "The measure is the assessed claimants' actual net earned income for "
        "Universal Credit: it includes statutory pay and deducts their own "
        "relievable pension contributions and tax and National Insurance on "
        "earnings. Income imputed by the minimum income floor (reg. 82(4)) "
        "and a dependant's earnings do not count. For a member of a couple "
        "claiming as a single person the couple's earnings combine. The "
        "grace period (reg. 82(1)(b)) is not modelled. Housing Benefit has "
        "no earnings exception: its work exception is entitlement to working "
        "tax credit (HB Regs 2006 reg. 75E)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
    )

    def formula(benunit, period, parameters):
        person = benunit.members

        # Earnings exemption for UC (£846/month = £10,152/year)
        # Only check earned income, not the UC amount, to avoid a circular dependency.
        # UC Regs 2013 reg. 82(1)(a) tests "the claimant's earned income or,
        # if the claimant is a member of a couple, the couple's combined
        # earned income": a dependant's earnings do not count.
        claimant = person("is_uc_assessed_claimant", period)
        # Reg. 82(4) excludes earnings imputed under the minimum income
        # floor (reg. 62). Use actual UC earnings, before both that floor
        # and the work allowance, with the reg. 55 and 57 deductions.
        uc_earned = benunit.sum(
            person("uc_individual_earned_income_before_mif", period) * claimant
        )
        earnings_threshold = 10_152
        return uc_earned >= earnings_threshold

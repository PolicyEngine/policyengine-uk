from policyengine_uk.model_api import *


class is_uc_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Universal Credit benefit cap because of earnings"
    documentation = (
        "Whether the claimant's earned income, or a couple's combined earned "
        "income, reaches the earnings threshold (UC Regs 2013 reg. 82(1)(a), "
        "uc_benefit_cap_earnings_exception_threshold), which follows the "
        "national living wage each year. "
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
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        "https://www.legislation.gov.uk/ukpga/2004/12/section/188",
    )

    def formula(benunit, period, parameters):
        # UC Regs 2013 reg. 82(1)(a) excepts an award where "the claimant's
        # earned income or, if the claimant is a member of a couple, the
        # couple's combined earned income" reaches 16 hours a week at the
        # National Living Wage. A dependant's earnings do not count.
        #
        # Earned income is each claimant's own, after the reg. 55(5) and
        # 57(2) deductions, so one partner's deductions never come off the
        # other partner's earnings, tax on pension, property, savings or
        # dividend income is not deducted, and contributions paid after 75
        # are not relievable (Finance Act 2004 s. 188(3)(a)). It is read
        # before the minimum income floor and the work allowance, because
        # reg. 82(4) excludes earnings imputed under reg. 62.
        #
        # Only earned income is read, not the Universal Credit award itself,
        # to avoid a circular dependency with the cap.
        person = benunit.members
        claimant = person("is_uc_assessed_claimant", period)
        uc_earned = benunit.sum(
            person("uc_individual_earned_income_before_mif", period) * claimant
        )
        return uc_earned >= benunit(
            "uc_benefit_cap_earnings_exception_threshold", period
        )

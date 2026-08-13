from policyengine_uk.model_api import *


class is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap because of earnings"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/82"

    def formula(benunit, period, parameters):
        # Regulation 82 of the Universal Credit Regulations 2013 excepts a
        # claimant (or couple, on their combined income) from the benefit cap
        # where their earned income reaches 16 hours a week at the National
        # Living Wage. Earned income here is employed and self-employed
        # earnings net of the income tax, National Insurance and relievable
        # pension contributions attributable to those earnings (reg. 55(5),
        # reg. 57), not net of total tax on all income.
        #
        # Reg. 82(1)(a) tests "the claimant's earned income or, if the
        # claimant is a member of a couple, the couple's combined earned
        # income": a dependant's earnings do not count.
        #
        # Only earned income is read, not the Universal Credit award itself,
        # to avoid a circular dependency with the cap.
        person = benunit.members
        claimant = person("is_uc_assessed_claimant", period)
        earnings = person("employment_income", period) + person(
            "self_employment_income", period
        )
        # earned_income_tax is the tax on non-savings, non-dividend income,
        # which excludes property, savings and dividend income. It is the
        # closest available measure of tax on earnings; it still includes tax
        # on private and state pension income, which is the approximation we
        # accept here (households with pension income are generally already
        # exempt through the state pension age exception).
        deductions = (
            person("earned_income_tax", period)
            + person("national_insurance", period)
            + person("pension_contributions", period)
        )
        net_earnings = max_(0, benunit.sum((earnings - deductions) * claimant))

        monthly_threshold = parameters(period).gov.dwp.benefit_cap_earnings_exemption
        return net_earnings >= monthly_threshold * MONTHS_IN_YEAR

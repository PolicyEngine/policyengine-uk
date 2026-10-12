from policyengine_uk.model_api import *


class is_benefit_cap_exempt_earnings(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap because of earnings"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        "https://www.legislation.gov.uk/ukpga/2004/12/section/188",
    )

    def formula(benunit, period, parameters):
        # Regulation 82(1)(a) of the Universal Credit Regulations 2013
        # excepts an award from the benefit cap where "the claimant's earned
        # income or, if the claimant is a member of a couple, the couple's
        # combined earned income" reaches 16 hours a week at the National
        # Living Wage. A dependant's earnings do not count.
        #
        # Earned income is each claimant's own: their employed earnings less
        # their relievable pension contributions and the income tax and
        # primary Class 1 contributions paid in respect of the employment
        # (reg. 55(5)), and their self-employed earnings after the reg. 57(2)
        # steps, which make a loss or a nil result nil. So one partner's
        # deductions never come off the other partner's earnings, tax on
        # pension, property, savings or dividend income is not deducted, and
        # contributions paid after 75 are not relievable (Finance Act 2004
        # s. 188(3)(a)). uc_individual_earned_income_before_mif applies all
        # of this per person. It is read before the minimum income floor,
        # because reg. 82(4) excludes income treated as earned under reg. 62.
        #
        # Only earned income is read, not the Universal Credit award itself,
        # to avoid a circular dependency with the cap.
        person = benunit.members
        claimant = person("is_uc_assessed_claimant", period)
        earned_income = benunit.sum(
            person("uc_individual_earned_income_before_mif", period) * claimant
        )
        monthly_threshold = parameters(period).gov.dwp.benefit_cap_earnings_exemption
        return earned_income >= monthly_threshold * MONTHS_IN_YEAR

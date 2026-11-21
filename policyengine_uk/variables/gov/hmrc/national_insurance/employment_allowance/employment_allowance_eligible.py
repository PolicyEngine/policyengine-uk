from policyengine_uk.model_api import *


class employment_allowance_eligible(Variable):
    value_type = bool
    entity = Firm
    label = "Eligible for the Employment Allowance"
    documentation = (
        "Whether the firm can claim the Employment Allowance. It cannot if it "
        "is a public authority that is not a charity (s.2(1)), a company "
        "whose only employee paid Class 1 earnings is a director (s.2(4A), "
        "from 2016-17), a connected company or charity other than the one "
        "its group chooses to claim (s.3), or, from 2020-21 to 2024-25, an "
        "employer whose previous-year secondary Class 1 liabilities were "
        "£100,000 or more (s.2(4B)), tested on "
        "firm_prior_year_secondary_class_1_liabilities. The de minimis "
        "state aid test (s.2(4F)) and the exclusions for care workers and "
        "transferred businesses are not modelled."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="National Insurance Contributions Act 2014 s.2",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/2",
        ),
        dict(
            title="National Insurance Contributions Act 2014 s.3",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/3",
        ),
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.national_insurance.employment_allowance
        excluded_public_body = firm("firm_is_public_body", period) & ~firm(
            "firm_is_charity", period
        )
        excluded_single_director = (
            firm("firm_is_single_director_company", period)
            & p.excludes_single_director_companies
        )
        prior_year_liabilities = firm(
            "firm_prior_year_secondary_class_1_liabilities", period
        )
        excluded_by_prior_year_liabilities = (
            prior_year_liabilities >= p.prior_year_liabilities_limit
        )
        return (
            firm("firm_claims_employment_allowance", period)
            & ~excluded_public_body
            & ~excluded_single_director
            & ~excluded_by_prior_year_liabilities
        )

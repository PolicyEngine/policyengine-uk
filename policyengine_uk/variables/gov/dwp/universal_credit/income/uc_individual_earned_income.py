from policyengine_uk.model_api import *


class uc_individual_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit earned income of the person"
    documentation = (
        "The person's earned income for Universal Credit, after the "
        "deductions for their own relievable pension contributions and their "
        "own income tax and National Insurance in respect of their employment "
        "and self-employment, before the work allowance."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Finance Act 2004 s. 188 (relievable pension contributions)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
        ),
    ]

    def formula(person, period, parameters):
        # The deductions are the person's own and come off only their own
        # earnings, so one partner's tax, NI or pension contributions never
        # reduce the other partner's earned income.
        gross_earnings = person("uc_mif_capped_earned_income", period)
        # Contributions paid after the person reaches 75 are not relievable
        # (Finance Act 2004 s. 188(3)(a)).
        age_limit = parameters(
            period
        ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        relievable_pension_contributions = person("pension_contributions", period) * (
            person("age", period) < age_limit
        )
        tax_and_national_insurance = add(
            person,
            period,
            ["uc_income_tax_on_earnings", "uc_national_insurance_on_earnings"],
        )
        return max_(
            0,
            gross_earnings
            - relievable_pension_contributions
            - tax_and_national_insurance,
        )

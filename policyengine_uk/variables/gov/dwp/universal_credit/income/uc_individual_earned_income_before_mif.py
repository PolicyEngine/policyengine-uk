from policyengine_uk.model_api import *


class uc_individual_earned_income_before_mif(Variable):
    value_type = float
    entity = Person
    label = (
        "Universal Credit earned income of the person, before the minimum income floor"
    )
    documentation = (
        "The person's actual earned income for Universal Credit: their "
        "earnings less their own relievable pension contributions and their "
        "own income tax and National Insurance in respect of their employment "
        "and self-employment. The minimum income floor compares this with "
        "the net threshold."
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
    ]

    def formula(person, period, parameters):
        # The deductions are the person's own and come off only their own
        # earnings, so one partner's tax, NI or pension contributions never
        # reduce the other partner's earned income.
        earnings_components = ["employment_income", "miscellaneous_income"]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            earnings_components.append("basic_income")
        # A trading loss makes self-employed earnings nil (reg. 57(2)); it
        # is not set against employed earnings.
        self_employed = max_(0, person("self_employment_income", period))
        earnings = add(person, period, earnings_components) + self_employed
        deductions = add(
            person,
            period,
            [
                "pension_contributions",
                "uc_income_tax_on_earnings",
                "uc_national_insurance_on_earnings",
            ],
        )
        return max_(0, earnings - deductions)

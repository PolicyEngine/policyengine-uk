from policyengine_uk.model_api import *


class tax_free_childcare_meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "Income requirements and calculations for tax-free childcare"
    documentation = "Whether this person meets the income requirements for tax-free childcare based on age and income thresholds"
    definition_period = YEAR

    def formula(person, period, parameters):
        """
        Calculate if a person meets income requirements based on their age and income.

        Returns:
            bool: True if they meet the income conditions for their age group
        """
        # Get person's characteristics
        age = person("age", period)

        # Calculate eligible income
        total_income = person("total_income", period)
        # Extract investment incomes to subtract
        investment_income = add(
            person,
            period,
            [
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
                "property_income",
            ],
        )

        yearly_eligible_income = max_(total_income - investment_income, 0)
        quarterly_income = yearly_eligible_income / 4

        # Get required income threshold based on age
        income_limits = parameters(
            period
        ).gov.hmrc.tax_free_childcare.income_thresholds

        required_threshold = income_limits.calc(age)

        max_income_threshold = parameters(
            period
        ).gov.hmrc.tax_free_childcare.max_income_thresholds

        max_income_threshold_quarterly = max_income_threshold / 4

        # Compare quarterly income to required threshold and convert to boolean
        return (
            (quarterly_income > required_threshold)
            & (quarterly_income < max_income_threshold_quarterly)
        ).astype(bool)

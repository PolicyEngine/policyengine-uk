from policyengine_uk.model_api import *


class meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "Income requirements and calculations"
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

        yearly_eligible_income = total_income - investment_income

        # Get income thresholds from parameters
        income_limits = parameters(
            period
        ).gov.hmrc.childcare_subsidies.tax_free_childcare.income_thresholds
        quarterly_income = yearly_eligible_income / 4

        # Age >= 21
        meets_adult_condition = (age >= income_limits.adult.min_age) & (
            quarterly_income >= income_limits.adult.quarterly_income
        )

        # Age 18-20
        meets_young_adult_condition = (
            (age >= income_limits.young_adult.min_age)
            & (age <= income_limits.young_adult.max_age)
            & (quarterly_income >= income_limits.young_adult.quarterly_income)
        )

        # Age < 18
        meets_youth_condition = (age < income_limits.young_adult.min_age) & (
            quarterly_income >= income_limits.youth.quarterly_income
        )

        # Combine all conditions
        return (
            meets_adult_condition
            | meets_young_adult_condition
            | meets_youth_condition
        )

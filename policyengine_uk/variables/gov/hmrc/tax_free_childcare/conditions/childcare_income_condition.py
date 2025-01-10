from policyengine_uk.model_api import *


class meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "Income requirements and calculations"
    documentation = "Whether this person meets the income requirements for tax-free childcare based on age and income thresholds"
    definition_period = YEAR

    def formula(person, period):
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
            ]
        )
        
        yearly_eligible_income = total_income - investment_income

        # Income thresholds by age group
        quarterly_income = yearly_eligible_income / 4

        # Age >= 21
        meets_adult_condition = (
            (age >= 21) & 
            (quarterly_income >= 2379)
        )

        # Age 18-20
        meets_young_adult_condition = (
            (age >= 18) & 
            (age <= 20) & 
            (quarterly_income >= 1788)
        )

        # Age < 18
        meets_youth_condition = (
            (age < 18) &
            (quarterly_income >= 1331)
        )

        # Combine all conditions
        return (
            meets_adult_condition |
            meets_young_adult_condition |
            meets_youth_condition
        )
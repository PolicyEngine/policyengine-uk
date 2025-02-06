from policyengine_uk.model_api import *


class extended_childcare_entitlement_income_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Extended childcare entitlement income requirements"
    documentation = "Whether this person meets the income requirements for extended childcare entitlement based on age and income thresholds"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Get person's characteristics
        age = person("age", period)

        # for this part you can see the details in here: https://www.legislation.gov.uk/ukpga/2014/28/notes/division/6/3/4
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

        # Get required income threshold based on age
        income_limits = parameters(
            period
        ).gov.dwp.extended_childcare_entitlement.income_thresholds

        required_threshold = income_limits.calc(age) * 4

        # Get max income threshold to check if they exceed it
        max_income_threshold = parameters(
            period
        ).gov.dwp.extended_childcare_entitlement.max_income_thresholds

        # Get adjusted net income
        ani = person("adjusted_net_income", period)

        # Check if they meet the conditions:
        # 1. Quarterly income is above the required threshold
        # 2. Adjusted net income is below the max threshold
        return (yearly_eligible_income > required_threshold) & (
            ani < max_income_threshold
        )

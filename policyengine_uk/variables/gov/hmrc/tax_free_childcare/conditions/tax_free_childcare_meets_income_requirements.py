from policyengine_uk.model_api import *


class tax_free_childcare_meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "Income eligible for the tax-free childcare"
    documentation = "Whether this person meets the income requirements for tax-free childcare based on age and income thresholds"
    definition_period = YEAR

    # Legislation: https://www.legislation.gov.uk/ukdsi/2015/9780111127063 , part 9
    # Also, you can check here: https://www.gov.uk/tax-free-childcare?step-by-step-nav=d78aeaf6-1747-4d72-9619-f16efb4dd89d , part "your income"

    def formula(person, period, parameters):
        # Calculate eligible income
        total_income = person("total_income", period)

        # Get investment income types from parameters
        investment_income_types = parameters(
            period
        ).gov.hmrc.tax_free_childcare.investment_income_types

        # Extract investment incomes to subtract
        investment_income = add(person, period, investment_income_types)

        # Calculate eligible income after removing investment income
        yearly_eligible_income = max_(total_income - investment_income, 0)
        quarterly_income = yearly_eligible_income / 4

        # Get minimum wage rate using existing variable
        min_wage_rate = person("minimum_wage", period)

        # Get weekly hours requirement from parameters
        weekly_hours = parameters(
            period
        ).gov.hmrc.tax_free_childcare.minimum_weekly_hours

        # Calculate required threshold (weekly hours * 13 weeks (a quarter) * minimum wage)
        required_threshold = min_wage_rate * weekly_hours * 13

        # Get adjusted net income and check against max threshold
        ani = person("adjusted_net_income", period)
        p = parameters(period).gov.hmrc.tax_free_childcare

        return (quarterly_income > required_threshold) & (
            ani < p.max_income_thresholds
        )

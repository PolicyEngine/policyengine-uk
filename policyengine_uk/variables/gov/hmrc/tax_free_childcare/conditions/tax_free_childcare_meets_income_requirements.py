from policyengine_uk.model_api import *


class tax_free_childcare_meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "income eligible for the tax-free childcare"
    definition_period = YEAR

    # Legislation: https://www.legislation.gov.uk/ukdsi/2015/9780111127063 , part 9 and 10
    # Also, you can check here: https://www.gov.uk/tax-free-childcare

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare

        # Calculate eligible income by summing countable sources
        yearly_eligible_income = add(
            person, period, p.income.countable_sources
        )
        quarterly_income = yearly_eligible_income / 4

        # Get minimum wage rate using existing variable
        min_wage_rate = person("minimum_wage", period)

        # Calculate required threshold (weekly hours * 13 weeks (a quarter) * minimum wage)
        # Reference for the quarterly logic: part 9.3 in https://www.legislation.gov.uk/uksi/2015/448/regulation/9
        required_threshold = min_wage_rate * p.minimum_weekly_hours * 13

        # Get adjusted net income and check against max threshold
        ani = person("adjusted_net_income", period)

        return (quarterly_income > required_threshold) & (
            ani < p.income.income_limit
        )

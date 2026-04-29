from policyengine_uk.model_api import *


class tax_free_childcare_meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "income eligible for the tax-free childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare

        expected_income = person(
            "tax_free_childcare_expected_declaration_period_income",
            period,
        )

        # Get minimum wage rate using existing variable
        min_wage_rate = person("minimum_wage", period)

        required_threshold = (
            min_wage_rate * p.minimum_weekly_hours * p.income.declaration_period_weeks
        )
        meets_minimum_income = expected_income >= required_threshold
        in_start_up_period = person(
            "tax_free_childcare_self_employment_start_up_period",
            period,
        )

        # Get adjusted net income and check against max threshold
        ani = person("adjusted_net_income", period)

        return (meets_minimum_income | in_start_up_period) & (
            ani <= p.income.income_limit
        )

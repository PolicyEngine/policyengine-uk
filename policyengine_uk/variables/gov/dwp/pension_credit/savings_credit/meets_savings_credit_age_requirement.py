from policyengine_uk.model_api import *


class meets_savings_credit_age_requirement(Variable):
    value_type = bool
    entity = Person
    label = "whether the person reached State Pension Age before the Savings Credit cutoff year"
    definition_period = YEAR

    def formula(person, period, parameters):
        # https://www.legislation.gov.uk/ukpga/2002/16/section/3
        p = parameters(period).gov.dwp.pension_credit.savings_credit
        current_age = person("age", period)
        # State pension age
        spa = person("state_pension_age", period)
        # The year we're evaluating
        evaluation_year = period.start.year
        # Calculate what year the person reached/will reach SPA
        birth_year = evaluation_year - current_age
        spa_year = birth_year + spa
        # Get the cutoff year from parameters
        return spa_year < p.cutoff_year

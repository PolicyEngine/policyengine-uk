from policyengine_uk.model_api import *


class meets_savings_credit_age_requirement(Variable):
    value_type = bool
    entity = Person
    label = "whether the person reached State Pension Age before the Savings Credit cutoff year"
    documentation = (
        "Whether the person attained State Pension age before 6 April of the "
        "Savings Credit cutoff year and has attained the minimum age."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/3"

    def formula(person, period, parameters):
        # State Pension Credit Act 2002 s.3(1)(a): the claimant "has attained
        # pensionable age before 6 April 2016 and has attained the age of 65".
        p = parameters(period).gov.dwp.pension_credit.savings_credit
        months_from_cutoff_to_mid_year = 12 * (period.start.year - p.cutoff_year) + 6
        reached_before_cutoff = (
            person("months_since_state_pension_age", period)
            > months_from_cutoff_to_mid_year
        )
        # float64, so that exact ages compare cleanly with State Pension age.
        age = np.floor(person("age", period)).astype(np.float64)
        months = person("months_since_last_birthday", period).astype(np.float64)
        age_in_months = 12 * age + months
        return reached_before_cutoff & (age_in_months >= 12 * p.minimum_age)

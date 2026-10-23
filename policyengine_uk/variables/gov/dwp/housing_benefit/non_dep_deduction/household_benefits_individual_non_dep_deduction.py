from policyengine_uk.model_api import *


class household_benefits_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/6",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/6",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        income = person("housing_benefit_non_dep_gross_income", period)
        weekly_income = income / WEEKS_IN_YEAR
        on_income_related_benefit = (
            person("is_on_income_support", period)
            | person("is_on_income_based_jsa", period)
            | person("is_on_income_related_esa", period)
        )
        in_remunerative_work = (
            person("weekly_hours", period) >= p.remunerative_work_hours
        ) & ~on_income_related_benefit
        # Reg 74(1)(b), or pension-age reg 55(1)(b), applies outside
        # remunerative work. Reg 6(6) excludes income-related recipients.
        deduction = where(
            in_remunerative_work,
            p.amount.calc(weekly_income, right=True),
            p.amount.amounts[0],
        )
        return deduction * WEEKS_IN_YEAR

from policyengine_uk.model_api import *


class household_benefits_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    documentation = (
        "A non-dependant in remunerative work pays the deduction for the band "
        "containing their normal gross weekly income, counting a couple's "
        "joint income; bands include their lower edge. A non-dependant not in "
        "remunerative work pays the lowest amount. Gross income is taxable "
        "total income, so the disregarded disability benefits are excluded."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        income = max_(0, person("total_income", period))
        counted = person("age", period) >= p.age_threshold
        weekly_income = person.benunit.sum(income * counted) / WEEKS_IN_YEAR
        in_remunerative_work = (
            person("weekly_hours", period) >= p.remunerative_work_hours
        )
        banded = p.amount.calc(weekly_income)
        not_in_remunerative_work = p.amount.calc(np.zeros_like(weekly_income))
        weekly = where(in_remunerative_work, banded, not_in_remunerative_work)
        return weekly * WEEKS_IN_YEAR

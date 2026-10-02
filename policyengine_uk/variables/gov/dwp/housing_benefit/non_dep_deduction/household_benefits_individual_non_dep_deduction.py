from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    non_dependant_weekly_gross_income,
)


class household_benefits_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    documentation = (
        "A non-dependant in remunerative work pays the deduction for the band "
        "containing their normal gross weekly income (a couple's joint income "
        "for a claimant or partner of the non-dependant's family); bands "
        "include their lower edge. A non-dependant not in remunerative work, "
        "including one on Income Support, income-based JSA or income-related "
        "ESA (reg 6(6)), pays the lowest amount."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/6",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        weekly_income = non_dependant_weekly_gross_income(person, period)
        on_income_related_benefit = person("is_claimant_or_partner", period) & (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
        )
        in_remunerative_work = (
            person("weekly_hours", period) >= p.remunerative_work_hours
        ) & ~on_income_related_benefit
        banded = p.amount.calc(weekly_income)
        not_in_remunerative_work = p.amount.calc(np.zeros_like(weekly_income))
        weekly = where(in_remunerative_work, banded, not_in_remunerative_work)
        return weekly * WEEKS_IN_YEAR

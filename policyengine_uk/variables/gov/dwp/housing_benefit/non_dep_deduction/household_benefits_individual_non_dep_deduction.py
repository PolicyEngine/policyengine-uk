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
        banded = p.amount.calc(weekly_income, right=True)
        # Reg 74(1)(b), or pension-age reg 55(1)(b), gives a non-dependant
        # outside remunerative work the flat amount, the scale's first,
        # instead of an income band. Reg 6(6) excludes income-related
        # recipients from remunerative work. The gate only lowers a
        # deduction: a non-worker with no banding income keeps the scale's
        # zero, because the exemptions in reg 74(6), (7), (8) and (10),
        # and reg 55(6)-(9) (a claimant on Attendance Allowance; a
        # non-dependant on Pension Credit, or under 25 on Income Support;
        # a full-time student) are not modelled, and the income-related
        # benefits are not banding income, so many such non-dependants
        # have none.
        # #2007 adds the exemptions and the flat charge together.
        deduction = where(
            in_remunerative_work,
            banded,
            min_(banded, p.amount.amounts[0]),
        )
        return deduction * WEEKS_IN_YEAR

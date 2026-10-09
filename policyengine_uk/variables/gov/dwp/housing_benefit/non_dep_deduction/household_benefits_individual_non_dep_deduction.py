from policyengine_uk.model_api import *


class household_benefits_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/6",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/6",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        # The gross-income bands apply only to a non-dependant "to whom
        # paragraph (1)(a) applies because he is in remunerative work" (HB
        # Regs 2006 reg 74(2); SPC Regs reg 55(2)). Anyone else takes the
        # minimum deduction under reg 74(1)(b) / 55(1)(b), whatever their
        # income. Remunerative work is at least 16 paid hours a week (reg
        # 6(1) of both sets of Regulations). The first bracket of the table
        # is the reg 74(1)(b) amount; reg 74(2)(a) also gives it to a worker
        # whose income is below the first threshold, including zero. Reg
        # 6(5)-(8) (absences, income-based benefit receipt, leave, sports
        # awards) are not modelled.
        in_remunerative_work = (
            person("weekly_hours", period) >= p.remunerative_work_hours
        )
        weekly_income = person("total_income", period) / WEEKS_IN_YEAR
        minimum = p.amount.amounts[0]
        banded = max_(p.amount.calc(weekly_income, right=True), minimum)
        deduction = where(in_remunerative_work, banded, minimum)
        return deduction * WEEKS_IN_YEAR

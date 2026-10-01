from policyengine_uk.model_api import *


class pension_credit_income(Variable):
    label = "Income for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/15"

    def formula(benunit, period, parameters):
        pc = parameters(period).gov.dwp.pension_credit
        sources = pc.guarantee_credit.income
        total = add(benunit, period, sources)
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            total += add(benunit, period, ["basic_income"])
        pension_contributions = add(benunit, period, ["pension_contributions"])
        # Reg 17(10)(a) disregards tax only on income taken into account, and
        # Schedule IV paragraph 18 disregards actual income from capital.
        tax = add(
            benunit, period, ["legacy_means_test_income_tax", "national_insurance"]
        )
        pen_con_deduction_rate = pc.income.pension_contributions_deduction
        deductions = tax + pension_contributions * pen_con_deduction_rate
        return max_(0, total - deductions)

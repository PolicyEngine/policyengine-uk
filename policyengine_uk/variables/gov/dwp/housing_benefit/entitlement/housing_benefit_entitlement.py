from policyengine_uk.model_api import *


class housing_benefit_entitlement(Variable):
    label = "Housing Benefit entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        # Charges for meals are not eligible to be met by Housing Benefit
        # (HB Regs 2006 reg 12B(2)(b) and Sch 1 paras 1(a)(i) and 2), except
        # on the Local Housing Allowance route, where the cap rent is the
        # gross liability (regs 12D, 13D(12)); a rent officer's board and
        # attendance finding takes a private renter off that route (reg
        # 13C(5)(e)), as LHA_cap applies.
        lha_eligible = benunit("LHA_eligible", period.this_year)
        gross_rent = benunit("benunit_rent", period)
        rent_less_meals = max_(
            0, gross_rent - benunit("housing_benefit_meals_deduction", period)
        )
        lha_route = lha_eligible & ~benunit(
            "housing_benefit_board_and_attendance_determination", period
        )
        rent = where(lha_route, gross_rent, rent_less_meals)
        applicable_amount = benunit("housing_benefit_applicable_amount", period)
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.withdrawal_rate
        reduced_income = max_(0, income - applicable_amount)
        final_amount = max_(0, rent - reduced_income * withdrawal_rate)
        capped_final_amount = min_(final_amount, benunit("LHA_cap", period))
        amount = where(lha_eligible, capped_final_amount, final_amount)
        return max_(0, amount - benunit("housing_benefit_non_dep_deductions", period))

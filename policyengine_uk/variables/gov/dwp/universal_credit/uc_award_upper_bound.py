from policyengine_uk.model_api import *


class uc_award_upper_bound(Variable):
    value_type = float
    entity = BenUnit
    label = "Upper bound on the Universal Credit award"
    documentation = (
        "The model calculates this upper bound without reading the "
        "non-dependant deduction. Its formula for "
        "universal_credit_pre_benefit_cap never returns a larger award. DWP "
        "awards the maximum amount less the income reduction (UC Regs 2013 "
        "reg 22). The maximum amount includes the housing costs element "
        "(uc_housing_costs_element): the rent a renter may claim less DWP's "
        "non-dependant deductions. Where that element exceeds nil, DWP "
        "applies the lower work allowance (reg 22(2)(b)). Where DWP deducts "
        "less than the rent, the award stays at or below the award with no "
        "deduction. Where it deducts at least the rent, DWP calculates the "
        "award with no housing costs element and the higher work allowance "
        "(reg 22(2)(a); Sch 4 para 13). The formula takes the larger of those "
        "two awards. It repeats the award's steps in their order, rounding "
        "where they store a value, so the bound never falls below the award "
        "the model's formulas calculate. An input or a scenario can store a "
        "larger award; the carer test then reads the stored award "
        "(has_uc_award_with_carer_element). A family whose bound comes to nil "
        "has a nil award, and so no award: Parliament makes an amount "
        "payable of at least the prescribed minimum a financial condition "
        "(Welfare Reform Act 2012 s.5(1)(b) and (2)(b)), and DWP sets that "
        "minimum at one penny (reg 17). DWP makes no deduction for a "
        "non-dependant who receives Pension Credit (Sch 4 para 16(2)(b)), so "
        "the model's deduction reads Pension Credit, whose severe disability "
        "addition reads who has an award with the carer element. The bound "
        "reads neither, so has_uc_award_with_carer_element can read it. The "
        "bound can exceed a nil award in three ways (#2795). A non-dependant "
        "deduction can take the award to nil. A family that takes Tax-Free "
        "Childcare instead gets no award "
        "(forgoes_universal_credit_for_tax_free_childcare). And for a family "
        "with a work allowance and a small housing costs element, the "
        "calculation without housing costs applies the higher work allowance, "
        "whose extra earnings disregard can outweigh the housing costs it "
        "drops; that calculation can stay positive when the award comes to "
        "nil, even with no non-dependant deduction."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "is_uc_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/13",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/17",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test
        # Housing costs before any non-dependant deduction, as in
        # uc_housing_costs_element.
        tenure_type = benunit("benunit_tenure_type", period)
        tenure_types = tenure_type.possible_values
        rent = benunit("benunit_rent", period)
        capped_rent_amount = min_(benunit("uc_LHA_cap", period), rent)
        max_housing_costs = select(
            [
                (tenure_type == tenure_types.RENT_FROM_COUNCIL)
                | (tenure_type == tenure_types.RENT_FROM_HA),
                tenure_type == tenure_types.RENT_PRIVATELY,
            ],
            [rent, capped_rent_amount],
            default=0,
        )
        no_deduction = max_(max_housing_costs, 0).astype(np.float32)
        elements = [
            benunit(name, period)
            for name in (
                "uc_standard_allowance",
                "uc_child_element",
                "uc_disability_elements",
                "uc_carer_element",
            )
        ]
        childcare = benunit("uc_childcare_element", period)
        earned_income = benunit("uc_earned_income_before_work_allowance", period)
        unearned_income = benunit("uc_unearned_income", period)
        work_allowance_eligible = benunit("is_uc_work_allowance_eligible", period)
        awards = []
        for housing in (no_deduction, np.zeros_like(no_deduction)):
            # The steps of uc_maximum_amount (its adds, in order),
            # uc_work_allowance, uc_earned_income, uc_income_reduction and
            # universal_credit_pre_benefit_cap, each rounded to float32 where
            # that variable stores its value, so no rounding puts the bound
            # below the award.
            maximum = 0
            for element in elements:
                maximum = maximum + element
            maximum = maximum + housing + childcare
            monthly_allowance = where(
                housing > 0,
                p.work_allowance.with_housing,
                p.work_allowance.without_housing,
            )
            work_allowance = where(
                work_allowance_eligible,
                (monthly_allowance * MONTHS_IN_YEAR).astype(np.float32),
                0,
            ).astype(np.float32)
            earned = max_(0, earned_income - work_allowance)
            total_reduction = p.reduction_rate * earned + unearned_income
            reduction = min_(maximum, total_reduction).astype(np.float32)
            awards.append(maximum - reduction)
        return max_(awards[0], awards[1])

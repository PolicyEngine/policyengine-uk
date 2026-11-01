from policyengine_uk.model_api import *


class uc_award_upper_bound(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit award before the non-dependant deduction"
    documentation = (
        "The family's award before the benefit cap "
        "(universal_credit_pre_benefit_cap) never exceeds this amount, which "
        "leaves out the non-dependant deduction. DWP awards the maximum "
        "amount less the income reduction (UC Regs 2013 reg 22). The maximum "
        "amount includes the housing costs element (uc_housing_costs_element): "
        "the rent a renter may claim less DWP's non-dependant deductions. "
        "Where that element is positive, DWP applies the work allowance with "
        "housing. Where DWP deducts less than the rent, the award stays at or "
        "below the award with no deduction; where it deducts at least the "
        "rent, the award loses the housing costs element and takes the work "
        "allowance without housing. This amount takes the larger of those two "
        "awards. It repeats the award's steps in their order, rounding where "
        "they store a value, so it never falls below the award. A family "
        "whose bound comes to nil has a nil award, and so no award: "
        "Parliament makes an amount payable of at least the prescribed "
        "minimum a financial condition (Welfare Reform Act 2012 s.5(1)(b) "
        "and (2)(b)), and DWP sets that minimum at one penny (reg 17). The "
        "deduction spares a non-dependant on Pension Credit, so it reads "
        "Pension Credit, whose severe disability addition reads who has an "
        "award with the carer element. This amount reads neither, so that "
        "test can read it (has_uc_award_with_carer_element). It can exceed a "
        "nil award: a non-dependant deduction can take the award to nil, and "
        "a family that takes Tax-Free Childcare instead gets none "
        "(forgoes_universal_credit_for_tax_free_childcare)."
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

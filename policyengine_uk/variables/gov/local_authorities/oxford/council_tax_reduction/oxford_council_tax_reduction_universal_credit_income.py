from policyengine_uk.model_api import *


class oxford_council_tax_reduction_universal_credit_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Oxford Council Tax Reduction income of a Universal Credit applicant"
    documentation = (
        "The yearly income on which Oxford City Council bands a working-age "
        "applicant who receives Universal Credit (Appendix 3); the council "
        "bands a fifty-second of it each week. The council adds the "
        "applicant's and partner's net earned income, as DWP provides it, to "
        "the Universal Credit awarded, and counts other (unearned) income "
        "weekly. The model reads DWP's net earned income from its Universal "
        "Credit calculation of earned income "
        "(uc_earned_income_before_work_allowance): DWP deducts income tax, "
        "National Insurance and relievable pension contributions in full from "
        "earnings (UC Regs 2013 reg. 55(5)(a) and reg. 57(2) step 4) and "
        "applies the work allowance only in the award (reg. 22). So the "
        "council's own share of pension contributions (Part 1 para. 18) does "
        "not reach these applicants. The model reads other income from "
        "oxford_council_tax_reduction_universal_credit_other_income, and the "
        "award as the amount DWP awards before it takes deductions for debts "
        "(uc_deductions) out of the payment. The council also ignores £48.15 "
        "a week of each carer element and £84.46 a week of each disabled child "
        "element, which the model takes off the award but not below nil. For "
        "a disabled applicant the council ignores an amount equal to any "
        "disability premium payable before the move to Universal Credit; the "
        "model holds no record of that earlier award and ignores nothing for "
        "it, so it can overstate the income. The council ignores any "
        "transitional element in the award, and the model computes none "
        "(uc_maximum_amount). The council applies paragraphs 14 to 27, "
        "Annexes 5 and 6 and Appendix 5 only to applicants without Universal "
        "Credit, so its tariff income from capital (para. 15) and its Child "
        "Benefit disregard do not reach these applicants. DWP's figures and "
        "the award belong to the benefit unit's claimant and partner, so the "
        "model counts none of them where the household head applies alone. "
        "oxford_council_tax_reduction bands on this income from April 2026 "
        "(gov.local_authorities.oxford.council_tax_reduction.universal_credit."
        "in_effect)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27",
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
    )

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.local_authorities.oxford.council_tax_reduction.universal_credit
        earned_income = benunit("uc_earned_income_before_work_allowance", period)
        other_income = benunit(
            "oxford_council_tax_reduction_universal_credit_other_income", period
        )
        # Oxford City Council ignores £48.15 of the carer element and £84.46
        # of the disabled child element (Appendix 3). DWP includes a carer
        # element for each claimant who cares (reg. 29) and a disabled child
        # addition for each disabled child (reg. 24(2)), and the two amounts
        # equal the 2026-27 carer and disabled child premiums, which councils
        # include in Housing Benefit for each carer and each disabled child
        # (SI 2006/213 Sch 3 para 20(7) and (8)). So the model ignores up to
        # each amount for each element and takes the disregards off the
        # award, not below nil.
        carers = add(benunit, period, ["uc_carer_element_included_for_claimant"])
        carer_disregard = min_(
            benunit("uc_carer_element", period),
            carers * p.carer_element_disregard * WEEKS_IN_YEAR,
        )
        person = benunit.members
        disabled_child_element = add(
            person,
            period,
            [
                "uc_individual_disabled_child_element",
                "uc_individual_severely_disabled_child_element",
            ],
        )
        disabled_child_disregard = benunit.sum(
            min_(
                disabled_child_element,
                p.disabled_child_element_disregard * WEEKS_IN_YEAR,
            )
        )
        # Oxford City Council counts "the amount of Universal Credit awarded"
        # (Appendix 3). DWP takes the deductions for debts (uc_deductions) out
        # of the payment, not the award, so the model adds them back; DWP
        # applies the benefit cap to the award itself.
        award = benunit("universal_credit", period) + benunit("uc_deductions", period)
        award = max_(0, award - carer_disregard - disabled_child_disregard)
        # DWP's figures and the award belong to the claimant and partner, not
        # to a household head who applies alone.
        applicant_family = ~benunit("council_tax_reduction_head_applies_alone", period)
        return max_(0, applicant_family * (earned_income + award) + other_income)

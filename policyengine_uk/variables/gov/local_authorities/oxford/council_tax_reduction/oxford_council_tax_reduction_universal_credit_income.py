from policyengine_uk.model_api import *


class oxford_council_tax_reduction_universal_credit_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Oxford Council Tax Reduction income of a Universal Credit applicant"
    documentation = (
        "The yearly income on which Oxford's working-age scheme bands an "
        "applicant who receives Universal Credit (Appendix 3); the scheme "
        "bands a fifty-second of it each week. Appendix 3 adds the "
        "applicant's and partner's net earned income, as DWP provides it, "
        "to the Universal Credit awarded, and counts other (unearned) income "
        "weekly. DWP's net earned income is the Universal Credit calculation "
        "of earned income (uc_earned_income_before_work_allowance): earnings "
        "less income tax, National Insurance and relievable pension "
        "contributions in full (UC Regs 2013 reg. 55(5)(a) and reg. 57(2) "
        "step 4), before the work allowance, which belongs to the award "
        "(reg. 22). So Oxford's own share of pension contributions (Part 1 "
        "para. 18) does not reach these applicants. Other income is the "
        "Universal Credit calculation of unearned income (uc_unearned_income, "
        "reg. 66), which already leaves out the benefits Appendix 3 lists as "
        "ignored. Appendix 3 counts all other unearned income, which can go "
        "beyond reg. 66 (Child Benefit, for one, is not on its list); the "
        "model counts the reg. 66 amount only. Appendix 3 also ignores "
        "£48.15 a week of each carer element and £84.46 a week of each "
        "disabled child element, which come off the award (but not below "
        "nil), and, for a disabled applicant, an amount equal to any "
        "disability premium payable before the move to Universal Credit. "
        "The model holds no record of that earlier award, so it does not "
        "ignore that amount. Appendix 3 ignores any "
        "transitional element in the award. The model computes no "
        "transitional element (uc_maximum_amount), so the award has none to "
        "take out. Paragraphs 14 to 27, Annexes 5 and 6 and Appendix 5 apply "
        "only to applicants without Universal Credit, so Oxford's tariff "
        "income from capital (para. 15) and its Child Benefit disregard do "
        "not apply here. The four other councils the model runs assess "
        "Universal Credit applicants on the same three amounts (_legacy.py)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27",
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
    )

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.local_authorities.oxford.council_tax_reduction.universal_credit
        earned_income = benunit("uc_earned_income_before_work_allowance", period)
        unearned_income = benunit("uc_unearned_income", period)
        # Appendix 3 ignores £48.15 of the carer element and £84.46 of the
        # disabled child element. An award has a carer element for each
        # claimant who cares (reg. 29) and a disabled child addition for each
        # disabled child (reg. 24(2)), and the two amounts are the 2026-27
        # carer and disabled child premiums, one for each carer and each
        # disabled child, so each element has its own disregard, up to the
        # element. They come off the award, which cannot fall below nil.
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
        award = max_(
            0,
            benunit("universal_credit", period)
            - carer_disregard
            - disabled_child_disregard,
        )
        return max_(0, earned_income + unearned_income + award)

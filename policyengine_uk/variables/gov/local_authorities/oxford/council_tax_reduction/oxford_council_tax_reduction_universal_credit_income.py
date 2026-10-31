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
        "model counts the reg. 66 amount only. Appendix 3 ignores any "
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
        earned_income = benunit("uc_earned_income_before_work_allowance", period)
        unearned_income = benunit("uc_unearned_income", period)
        award = benunit("universal_credit", period)
        return max_(0, earned_income + unearned_income + award)

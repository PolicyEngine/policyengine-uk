from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)


class council_tax_reduction_working_age_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction income"
    documentation = (
        "Annual income of a working-age applicant in Scotland or Wales, "
        "compared with the applicable amount. An applicant on Income Support, "
        "income-based Jobseeker's Allowance or income-related Employment and "
        "Support Allowance, and not on Universal Credit, has no income for "
        "this purpose and gets the maximum reduction. A Welsh applicant with "
        "Universal Credit counts the Secretary of State's Universal Credit "
        "income figure (earnings before the work allowance, plus Universal "
        "Credit unearned income) plus the Universal Credit award. Everyone "
        "else counts net earnings less disregards, unearned income (in "
        "Wales, less tax on it), tariff income from capital and, in Scotland, "
        "the relevant Universal Credit payments, less relevant childcare "
        "charges. Wales deducts the charges from earnings, so they never take "
        "earnings below zero or reduce other income (WSI 2013/3029 Sch 6 para "
        "20(1)(c)). Scotland deducts them from the total of earned and "
        "unearned income, with or without Universal Credit (SSI 2021/249 "
        "regs 38(2) and 42(2)). Income never falls below zero."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/13",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/38",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/42",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/20",
    )

    def formula(benunit, period, parameters):
        wales = is_wales_scheme(benunit.household("country", period))
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        passported = benunit("council_tax_reduction_working_age_passported", period)
        earnings = benunit("council_tax_reduction_working_age_earned_income", period)
        award = benunit(
            "council_tax_reduction_working_age_universal_credit_award", period
        )
        wales_universal_credit_income = (
            earnings + benunit("uc_unearned_income", period) + award
        )
        disregard = benunit(
            "council_tax_reduction_working_age_earnings_disregard", period
        )
        childcare = benunit(
            "council_tax_reduction_working_age_childcare_deduction", period
        )
        # Wales deducts childcare charges "from any earnings" (WSI 2013/3029
        # Sch 6 para 20(1)(c)), after the disregards. Scotland estimates
        # earned income, adds unearned income and then deducts the charges
        # (SSI 2021/249 reg 38(2) without Universal Credit, reg 42(2) with
        # it), so they can reduce unearned income too.
        from_earnings = wales & ~has_universal_credit
        earnings_after_deductions = max_(
            0, earnings - disregard - where(from_earnings, childcare, 0)
        )
        unearned = benunit("council_tax_reduction_working_age_unearned_income", period)
        # Wales disregards tax on unearned income (Sch 9 para 4); Scotland
        # counts unearned income gross (reg 57).
        unearned_tax = where(
            wales & ~has_universal_credit,
            min_(
                benunit(
                    "council_tax_reduction_working_age_unearned_income_tax", period
                ),
                unearned,
            ),
            0,
        )
        own_rules_income = (
            earnings_after_deductions
            + unearned
            - unearned_tax
            + add(
                benunit,
                period,
                [
                    "council_tax_reduction_working_age_tariff_income",
                    "council_tax_reduction_relevant_universal_credit_payments",
                ],
            )
            - where(from_earnings, 0, childcare)
        )
        income = where(
            wales & has_universal_credit,
            wales_universal_credit_income,
            own_rules_income,
        )
        return where(passported, 0, max_(0, income))

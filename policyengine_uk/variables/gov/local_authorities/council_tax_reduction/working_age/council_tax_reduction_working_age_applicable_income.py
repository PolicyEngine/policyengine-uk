from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
    is_wales_scheme,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
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
        "Wales, less tax on it), tariff income from capital "
        "(council_tax_reduction_tariff_income), rent for letting part of the "
        "home (council_tax_reduction_home_letting_income) where the scheme "
        "counts it and, in Scotland, the relevant Universal Credit payments, "
        "less relevant childcare charges. From April 2022 Scotland also takes "
        "£15 weekly for each applicant or partner who receives Widowed "
        "Parent's Allowance from the total of unearned income, tariff income "
        "and relevant Universal Credit payments, never below nil (SSI "
        "2021/249 reg 57(4)). Wales deducts the charges from earnings after "
        "the disregards, never below zero (WSI 2013/3029 Sch 6 para "
        "20(1)(c)). Where those earnings are below the capped charges and the "
        "applicant or partner receives working tax credit or child tax "
        "credit, para 20 also deducts the rest from that credit; the model "
        "does not, so in Wales the charges never reduce other income "
        "(#2936). From April 2022 Scotland deducts them from the "
        "total of earned and unearned income, with or without Universal "
        "Credit (SSI 2021/249 regs 38(2) and 42(2)). The model applies that "
        "rule to earlier Scottish claims too, although SSI 2012/303 reg "
        "27(1)(c) and (2) deducted them as para 20 does and, from 25 November "
        "2013, reg 28(1A) gave Universal Credit claims no deduction "
        "(#2937). Income never falls below zero."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/13",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/38",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/42",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/20",
    )

    def formula(benunit, period, parameters):
        country = benunit.household("country", period)
        wales = is_wales_scheme(country)
        scotland = is_scotland_scheme(country)
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
        # Wales deducts childcare charges "from any earnings" after the
        # disregards (WSI 2013/3029 Sch 6 para 20(1)(c)). Where those earnings
        # are below the capped charges and the applicant or partner receives
        # working tax credit or child tax credit, para 20(1)(c) and (2) also
        # deduct the rest from that credit; the model does not
        # (#2936). From April 2022 Scotland estimates earned
        # income, adds unearned income and then deducts the charges (SSI
        # 2021/249 reg 38(2) without Universal Credit, reg 42(2) with it), so
        # they can reduce unearned income too. Before then SSI 2012/303 reg
        # 27(1)(c) and (2) deducted them as para 20 does, and from 25
        # November 2013 reg 28(1A) gave Universal Credit claims no deduction.
        # The model applies the April 2022 rule to Scottish claims in every
        # year (#2937).
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
        # Rent for letting part of the home counts without Universal Credit,
        # in Wales and in Scotland before SSI 2021/249 (whose reg 57(1) list
        # has no head for it); the Universal Credit routes take income from
        # the Secretary of State's assessment, which does not count it.
        p_scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.means_test
        counts_home_letting = ~has_universal_credit & (
            wales | (scotland & p_scotland.working_age_counts_home_letting_income)
        )
        home_letting = where(
            counts_home_letting,
            benunit("council_tax_reduction_home_letting_income", period),
            0,
        )
        other_unearned = add(
            benunit,
            period,
            [
                "council_tax_reduction_tariff_income",
                "council_tax_reduction_relevant_universal_credit_payments",
            ],
        )
        # From April 2022 Scotland disregards £15 weekly "from the
        # applicant's weekly unearned income" where the applicant receives
        # Widowed Parent's Allowance (reg 57(4)), so the disregard comes off
        # the reg 57 total, which includes tariff income (reg 57(1)(l), the
        # assumed yield from capital) and the relevant Universal Credit
        # payments (reg 57(1)(p)), not only the allowance.
        # council_tax_reduction_working_age_unearned_income counts the
        # allowance gross in that case. Each applicant or partner who
        # receives it gets a disregard (reg 36(1)).
        person = benunit.members
        recipients = benunit.sum(
            working_age_applicant_or_partner(person, period)
            & (person("widowed_parents_allowance", period) > 0)
        )
        widowed_parents_allowance_disregard = where(
            scotland
            & p_scotland.working_age_widowed_parents_allowance_disregard_from_unearned_income,
            min_(
                recipients
                * parameters(
                    period
                ).gov.local_authorities.council_tax_reduction.income_disregards.widowed_parents_allowance
                * WEEKS_IN_YEAR,
                max_(0, unearned + other_unearned),
            ),
            0,
        )
        own_rules_income = (
            earnings_after_deductions
            + unearned
            - unearned_tax
            + home_letting
            + other_unearned
            - widowed_parents_allowance_disregard
            - where(from_earnings, 0, childcare)
        )
        income = where(
            wales & has_universal_credit,
            wales_universal_credit_income,
            own_rules_income,
        )
        return where(passported, 0, max_(0, income))

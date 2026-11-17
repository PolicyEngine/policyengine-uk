from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Council Tax Reduction means test"
    documentation = (
        "We count the applicant's and partner's income "
        "(is_council_tax_reduction_applicant_or_partner) in the Council Tax "
        "Reduction means test. Under the pensioner schemes, councils "
        "disregard the whole income of an applicant who, or whose partner, is "
        "in receipt of Pension Credit guarantee credit, and use the Secretary "
        "of State's Pension Credit assessment of income, plus the savings "
        "credit payable, where the award is savings credit only. Otherwise we "
        "deduct the pensioner earnings disregards from a pension-age family's "
        "net earnings, and add its tariff income from capital "
        "(council_tax_reduction_tariff_income). Councils in Great "
        "Britain also exclude Child Benefit from a pensioner's general-rule "
        "income and count statutory sick and maternity pay as earnings. We "
        "omit the other "
        "adjustments these provisions allow (childcare charges, the £20 "
        "earnings disregards and the rest). Spousal maintenance counts less one "
        "£15 weekly disregard where the applicant's family includes a child "
        "or young person (the statutory family-premium condition in England's "
        "default and Welsh schemes). "
        "Widowed Parent's Allowance counts less £15 weekly per recipient. "
        "We count no child maintenance. Scotland's working-age maintenance "
        "rule, like Universal Credit, requires a court order or agreement; "
        "we assume the input meets that condition. "
        "Where the household head applies alone "
        "(council_tax_reduction_head_applies_alone), the benefit unit's own "
        "awards (Child Benefit, Income Support, income-based JSA, "
        "income-related ESA, Universal Credit, tax credits, Pension Credit) "
        "and its children belong to its claimant and partner, not to the "
        "head, so none of them counts. Industrial injuries disablement "
        "benefit, severe disablement allowance and incapacity benefit count "
        "in every scheme, for the applicant and partner only, not for "
        "children or young persons. We disregard war pensions and Armed "
        "Forces Compensation Scheme payments in full: Scottish councils count "
        "none of them, and English and Welsh councils may relieve them beyond "
        "the prescribed £10 a week. "
        "The formula counts no income derived from capital, such as rent "
        "from property other than the home, interest and dividends. In each "
        "pensioner scheme, a council disregards any actual income from "
        "capital, except income from the capital that Part 2 of the capital "
        "Schedule lists: life interests and liferents, rights to rent where "
        "the applicant has no reversionary interest, annuities, and property "
        "held under a trust that pays or may pay the applicant or partner. It "
        "disregards that income too while such capital totals £10,000 or "
        "less. The model has no input that marks capital as Part 2 capital, "
        "and other_investment_income takes in interest from trusts and "
        "settlements, so on the pensioner route the formula counts none of "
        "the interest, other investment income, dividends or rent from "
        "property, and council_tax_reduction_tax_deduction deducts no tax on "
        "any of it. The model makes that general approximation of the income "
        "rules: where Part 2 capital above £10,000 yields such income, a "
        "council counts it and the model doesn't. The Welsh working-age "
        "scheme and the English default scheme treat income from capital as "
        "capital; the Scottish working-age scheme counts only the unearned "
        "income it lists, which includes the assumed yield from capital but "
        "not actual rent, interest or dividends. Instead, the national "
        "schemes (England for pensioners, Wales and Scotland) count the "
        "tariff income they treat capital as yielding "
        "(council_tax_reduction_tariff_income), and in the pensioner schemes "
        "a council leaves Part 2 capital out of it. The English local schemes "
        "for people under pension age add their own tariff income. "
        "Rent the applicant and partner receive for letting part of the home "
        "counts, less the sub-tenant disregard, on the schemes' own income "
        "rules (council_tax_reduction_home_letting_income), with rent from "
        "boarders and lodgers paid to an applicant or partner who heads the "
        "household, less the board and lodging and lodger disregards. It does not count "
        "where a working-age applicant has an award of Universal Credit, "
        "whose income the schemes take from the Secretary of State's "
        "Universal Credit assessment (which does not count it), or in the "
        "Scottish scheme for people under pension age from April 2022, which "
        "does not list it. "
        "The formula deducts the income tax and National Insurance each "
        "scheme allows (council_tax_reduction_tax_deduction): on earnings "
        "only in Scotland's working-age scheme, on income taken into account "
        "in the pensioner schemes, and in the other schemes the income tax "
        "the legacy means tests deduct (legacy_means_test_deducted_income_tax), "
        "less, on the Universal Credit route, the tax uncounted rent would "
        "bear without earnings (rent_a_room_income_tax_without_earnings)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/37",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/31",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/10",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/7",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/20",
        "https://www.legislation.gov.uk/uksi/2012/2886/appendix/8/paragraph/21",
        "https://www.legislation.gov.uk/uksi/2012/2886/appendix/8/paragraph/49",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/4/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/4/paragraph/20",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/21",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/49",
        "https://www.legislation.gov.uk/wsi/2013/3035/schedule/5/paragraph/20",
        "https://www.legislation.gov.uk/wsi/2013/3035/schedule/7/paragraph/49",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3/paragraph/19",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/4",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/3",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/37",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/64",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/4",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/4/part/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/6/part/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/5/part/2",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/21",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/36",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/39",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/54",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/34",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/17",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3/paragraph/1",
        "https://www.legislation.gov.uk/ukpga/1992/14/schedule/1A/paragraph/2",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/13A",
        "https://www.newham.gov.uk/downloads/file/209/discretionary-council-tax-reductions-for-individual-council-tax-payers",
    ]

    def formula(benunit, period, parameters):
        # Members whose income counts: the applicant and partner (CTR
        # (Prescribed Requirements) (England) Regs 2012 Sch 1 para 11; WSI
        # 2013/3029 Sch 1 para 5; SSI 2012/319 reg 21; SSI 2021/249 reg 36(1)).
        # "The income and capital of a child or young person is not to be
        # treated as the income and capital of the applicant" (SSI 2012/319 reg
        # 21(3); SSI 2021/249 reg 36(2)); the other schemes count the
        # applicant's and partner's alone. Anyone else in the benefit unit does
        # not count either. A household head who applies alone is the
        # applicant, whatever else the benefit unit reads them as.
        person = benunit.members
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        applicant_family = ~head_applies_alone
        members = person("is_council_tax_reduction_applicant_or_partner", period)
        # Only the claimant's and partner's income-related awards: the scheme
        # counts the applicant's and partner's income (Sch 1 para 11 above). A
        # member outside the family who has an award of their own claims in their
        # own right. Income Support already needs the claimant's or partner's own
        # award (income_support_eligible).
        benunit_means_tested_benefits = [
            "child_benefit",
            "income_support",
            "claimant_or_partner_jsa_income",
            "claimant_or_partner_esa_income",
            "universal_credit",
        ]
        personal_benefits = [
            "carers_allowance",
            # Scottish carers receive Carer Support Payment in place of Carer's
            # Allowance. Scottish Council Tax Reduction counts it, with no cap at
            # the Carer's Allowance amount:
            # SSI 2021/249 reg 57(1)(b)(iva) at working age and SSI 2012/319
            # reg 27(1)(j) at pension age. Neither counts the Scottish Carer
            # Supplement (reg 57(1) does not list it; reg 27(1)(j)(xxib)
            # excepts it), so scottish_carer_supplement is not listed.
            # Scottish working-age claims follow the devolved route, which
            # counts CSP after the CSP Regs (SSI 2023/302) reg 16(2)
            # overlapping-benefit reduction
            # (council_tax_reduction_working_age_unearned_income). For the
            # pension-age scheme the question stays open: SSI 2012/319 reg
            # 27(3) counts a benefit before any deduction other than the reg
            # 27(5) adjustments, and reg 27(5) doesn't list reg 16(2), while
            # the Pension Credit and pension-age Housing Benefit regulations
            # do (SI 2002/1792 reg 15(4)(g); SI 2006/214 reg 29(4)(g)). Until
            # a ruling settles it, this formula counts the amount before the
            # reduction, as it did before the model applied the reduction.
            "carer_support_payment_pre_overlap",
            "esa_contrib",
            "jsa_contrib",
            "state_pension",
            "maternity_allowance",
            # Statutory sick, maternity and paternity pay are earnings: SI
            # 2012/2885 Sch 1 para 18(1)(h) to (j) and the default scheme, SI
            # 2012/2886 Sch paras 41(1)(h) and (i) and 51(1)(j); WSI 2013/3029
            # Sch 1 para 12(1)(h) and (i) and Sch 6 para 14(1)(j); SSI
            # 2012/319 reg 32(1)(h) and (i); SSI 2021/249 regs 49(4)(a) to
            # (c) and 50(2)(j). The income tax and National Insurance
            # deducted below include the tax on them (employment_benefits,
            # ni_class_1_income).
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "statutory_paternity_pay",
            "ssmg",
        ]
        # Every scheme the model runs counts these three benefits. At pension
        # age they are social security benefits that the income lists do not
        # except: SI 2012/2885 Sch 1 para 16(1)(j), the default scheme SI
        # 2012/2886 Sch para 39(1)(j), WSI 2013/3029 Sch 1 para 10(1)(j) and
        # SSI 2012/319 reg 27(1)(j). At working age England and Wales count
        # gross income (SI 2012/2886 Sch para 54(1); WSI 2013/3029 Sch 6 para
        # 17(1)) less disregards that do not list them (their Schs 8 and 9),
        # and Scotland's closed list names them (SSI 2021/249 reg 57(1)(b)(ix)
        # to (xi)). Each scheme leaves out IIDB's constant attendance and
        # exceptionally severe disablement increases (SSCBA 1992 ss.104 and
        # 105), by name or as "attendance allowance" (Sch 8 and Sch 9 para
        # 14), but iidb is the whole reported payment and cannot separate
        # them. Only the applicant's and partner's count (Sch 1 para 11; SSI
        # 2021/249 reg 36(1)): the Council Tax Reduction applicant and partner,
        # which is the household head alone where the head applies alone, and
        # never the dependants that the wider mask above still reaches.
        applicant_and_partner_benefits = ["iidb", "sda", "incapacity_benefit"]
        applicant_and_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        # War disablement pensions, war widow's or widower's pensions and
        # Armed Forces Compensation Scheme payments (afcs, war_widows_pension).
        # Scotland counts none of them: SSI 2012/319 Sch 3 para 1 disregards
        # each in full, and SSI 2021/249 reg 57(1), a closed list, does not
        # name them. England and Wales prescribe a £10 a week disregard (SI
        # 2012/2885 Sch 5 para 1; SI 2012/2886 Sch 6 para 1 and Sch 8 para 20;
        # WSI 2013/3029 Sch 4 para 1 and Sch 9 para 20), which a council may
        # exceed: Wales makes it a minimum for war disablement and war widow's
        # or widower's pensions (WSI 2013/3029 reg 34(5)), an English scheme
        # may make provision equivalent to the council tax benefit rules (LGFA
        # 1992 Sch 1A para 2(11)), and any council may reduce council tax
        # further (s.13A(1)(c)). The model takes the full disregard, as
        # Housing Benefit does for local schemes under SSAA 1992 s.134(8)(a).
        # The councils whose schemes the model reads mostly go further:
        # Westminster's working-age and pensioner schemes disregard war
        # pensions in full, and Oxford's Appendix 5 ignores war pensions for
        # applicants without Universal Credit. Newham's scheme keeps the £10
        # (Sch 6 para 1, Sch 8 para 19), but since 2013 it adds automatically
        # the reduction a full disregard of war compensation payments would
        # give (its s.13A(1)(c) policy, para 2.1). Kingston upon Thames's
        # schedules keep the £10 (Sch 6 para 1, Sch 8 para 20) while its para
        # 36(6) speaks of "the higher amount of full disregard" of the same
        # payments. Merton's Sch 8 para 20 disregards them "in full" but
        # "subject to paragraph 40", whose £20 a week limit, read literally,
        # caps that at working age. These are approximations of the councils'
        # texts. The full disregard also over-disregards guaranteed income
        # payments in Wales, which reg 34(5) does not cover, and wherever a
        # scheme keeps the prescribed £10 without further relief; afcs does
        # not separate guaranteed income payments from war disablement
        # pensions, nor either from the constant attendance and severe
        # disablement additions that every scheme disregards in full.
        income_components = [
            "employment_income",
            "self_employment_income",
            "private_pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        # The benefit unit's awards are its claimant's and partner's.
        benefits = applicant_family * add(
            benunit, period, benunit_means_tested_benefits
        )
        country = benunit.household("country", period)
        in_great_britain = (
            (country == Country.ENGLAND)
            | (country == Country.SCOTLAND)
            | (country == Country.WALES)
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        # England Sch 1 para 16(1)(j)(vi), Wales Sch 1 para 10(1)(j)(vi)
        # and Scotland reg 27(1)(j)(vii) exclude this exact BenUnit award.
        # Remove it before the general-rules floor. SSP/SMP remain counted
        # in personal_benefits as earnings; working-age/NI income is unchanged.
        # A head who applies alone counts none of the benefit unit's awards, so
        # there is no Child Benefit to remove.
        benefits -= where(
            pensioner & in_great_britain & applicant_family,
            add_for_members(benunit, period, ["child_benefit"], members),
            0,
        )
        income = add_for_members(benunit, period, income_components, members)
        personal_benefit_income = add_for_members(
            benunit, period, personal_benefits, members
        )
        personal_benefit_income += add_for_members(
            benunit, period, applicant_and_partner_benefits, applicant_and_partner
        )
        credits = applicant_family * add(benunit, period, ["tax_credits"])
        disregards = parameters(
            period
        ).gov.local_authorities.council_tax_reduction.income_disregards
        # England's default working-age scheme Sch 8 paras 21 and 49;
        # pensioners SI 2012/2885 Sch 5 paras 7 and 20. Wales WSI 2013/3029
        # Sch 9 paras 21/49 and Sch 4 paras 7/20 (default WSI 2013/3035 Schs
        # 7 and 5). Scotland SSI 2021/249 reg 57(4), (6) and SSI 2012/319
        # Sch 3 paras 6/19. All aggregate the family's maintenance for one
        # £15 disregard. The default English and Welsh family premiums are for families
        # with a child or young person (SI 2012/2886 Sch para 26(1)(c);
        # WSI 2013/3029 Sch 1 para 1(1)(c), Sch 6 para 1(1)(c)).
        maintenance = in_great_britain * benunit.sum(
            max_(0, person("spousal_maintenance_income", period))
            * applicant_and_partner
        )
        has_child = applicant_family & benunit(
            "is_responsible_for_child_or_young_person_for_council_tax_reduction", period
        )
        maintenance_disregard = where(
            has_child,
            min_(maintenance, disregards.maintenance * WEEKS_IN_YEAR),
            0,
        )
        widowed_parents_allowance = in_great_britain * benunit.sum(
            max_(
                0,
                person("widowed_parents_allowance", period)
                - disregards.widowed_parents_allowance * WEEKS_IN_YEAR,
            )
            * applicant_and_partner
        )
        increased_income = (
            income
            + personal_benefit_income
            + credits
            + benefits
            + maintenance
            - maintenance_disregard
            + widowed_parents_allowance
        )
        # Rent the applicant and partner receive for letting part of the home
        # counts under the schemes' own income rules, less the sub-tenant
        # disregard (SI 2012/2885 Sch 1 paras 11 and 16(1)(v), Sch 5 para 10),
        # and so does rent from boarders and lodgers paid to an applicant or
        # partner who heads the household, less the board and lodging and
        # lodger disregards (Sch 1 para 16(1)(p), Sch 5 paras 9 and 10). Two
        # exceptions:
        # - A working-age applicant with an award of Universal Credit: the
        #   schemes use the Secretary of State's assessment of income for the
        #   award (SI 2012/2886 Sch para 37(1); WSI 2013/3029 Sch 6 para 9(1);
        #   SSI 2012/303 reg 26(1)), which does not count it (UC Regs 2013
        #   reg 66), and Oxford's Appendix 3 disregards it.
        # - The Scottish scheme for people under pension age from 1 April 2022
        #   (SSI 2021/249, whose reg 57(1) list has no head for it). That
        #   scheme applies under reg 3(1) to everyone the pension-age scheme
        #   does not cover (council_tax_reduction_pensioner). An award held
        #   only by people over pensionable age does not count (reg 3(2)); the
        #   selector stands this in by requiring a younger applicant or
        #   partner, as Universal Credit itself does (UC Regs 2013 reg
        #   3(2)(a)). The model cannot represent reg 3(2)'s other statuses or
        #   a claim awaiting determination (reg 3(1)(b)(ii), from April 2023).
        universal_credit_route = ~pensioner & benunit(
            "council_tax_reduction_universal_credit_award", period
        )
        scottish_working_age_scheme = is_scotland_scheme(country) & ~pensioner
        p_scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.means_test
        counts_home_letting = ~universal_credit_route & (
            ~scottish_working_age_scheme
            | p_scotland.working_age_counts_home_letting_income
        )
        increased_income += where(
            counts_home_letting,
            benunit("council_tax_reduction_home_letting_income", period),
            0,
        )

        if not bi.interactions.include_in_means_tests:
            increased_income -= add_for_members(
                benunit, period, ["basic_income"], members
            )

        # The scheme's own share of pension contributions (one-half in each:
        # SI 2012/2885 Sch 1 para 19(2)(b)-(c), WSI 2013/3029 Sch 1 para 13
        # and Sch 6 para 15, SSI 2012/319 reg 33 and SSI 2021/249 reg 50(3),
        # and the councils' schemes).
        pension_contributions = add_for_members(
            benunit, period, ["pension_contributions"], members
        ) * benunit("council_tax_reduction_pension_contribution_deduction_rate", period)
        # The income tax and National Insurance each scheme allows: on earnings
        # only in Scotland's working-age scheme, on income taken into account
        # in the pensioner schemes, and in the other schemes what the legacy
        # means tests deduct (council_tax_reduction_tax_deduction).
        tax = benunit("council_tax_reduction_tax_deduction", period)
        # SI 2012/2885 Sch 1 para 17(9) and Sch 4; WSI 2013/3029 Sch 1 para
        # 11(9) and Sch 3; SSI 2012/319 reg 31(8) and Sch 2: the pensioner
        # earnings disregards, capped at net earnings. Zero for working-age
        # families.
        earnings_disregard = benunit(
            "council_tax_reduction_pensioner_earnings_disregard", period
        )
        # The national schemes also treat capital as yielding a tariff income
        # (council_tax_reduction_tariff_income); the English local schemes for
        # people under pension age add their own.
        income_under_general_rules = max_(
            0, increased_income - tax - pension_contributions - earnings_disregard
        ) + benunit("council_tax_reduction_tariff_income", period)
        # SI 2012/2885 Sch 1 para 13, WSI 2013/3029 Sch 1 para 7 and SSI
        # 2012/319 reg 24: a guarantee credit recipient's whole income is
        # disregarded. Para 14, para 8 and reg 25: in savings-credit-only cases
        # the Secretary of State's assessment of net income is used, adjusted
        # to take account of the savings credit payable. The Pension Credit
        # paid on a savings-credit-only award is that savings credit (under the
        # Pension Credit freeze, the frozen amount).
        # The benefit unit's Pension Credit is its claimant's and partner's.
        in_receipt_of_guarantee_credit = applicant_family & benunit(
            "in_receipt_of_guarantee_credit", period
        )
        has_savings_credit_only_award = applicant_family & benunit(
            "in_receipt_of_savings_credit_only", period
        )
        # The general route counts no war pension (as Housing Benefit, a full
        # disregard), so the war pension income in the Secretary of State's
        # assessment is taken out here too.
        savings_credit_only_income = max_(
            0,
            benunit("pension_credit_income", period)
            - benunit("pension_credit_war_pension_income", period)
            # PC already counts maintenance in full: apply only CTR's
            # extra disregard (England Sch 1 para 14(2)(c)(ii); Wales Sch 1
            # para 8(2)(c)(ii); Scotland reg 25(2)(c)(ii)).
            - maintenance_disregard,
        ) + benunit("pension_credit", period)
        return select(
            [in_receipt_of_guarantee_credit, has_savings_credit_only_award],
            [0, savings_credit_only_income],
            default=income_under_general_rules,
        )

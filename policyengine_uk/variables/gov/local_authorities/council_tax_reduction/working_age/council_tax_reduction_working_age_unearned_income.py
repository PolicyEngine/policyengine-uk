from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
    applicant_family,
    working_age_child,
)


class council_tax_reduction_working_age_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction unearned income"
    documentation = (
        "Annual unearned income of the applicant and partner counted in a "
        "working-age council tax reduction claim in Scotland or Wales, other "
        "than Universal Credit and tariff income from capital. Retirement "
        "pensions, contributory Jobseeker's Allowance and Employment and "
        "Support Allowance, carer's allowance, carer support payment (the "
        "Carer Support Payment component after any overlapping-benefit "
        "reduction; the Scottish Carer Supplement is a separate variable "
        "that does not count), "
        "maternity allowance, industrial injuries benefit, incapacity benefit, "
        "severe disablement allowance, Part 5 miscellaneous income and "
        "working and child tax credits count. Spousal maintenance counts, less "
        "a single £15 weekly disregard where the applicant's family includes "
        "a child or young person, and so does Widowed Parent's Allowance, "
        "less £15 weekly for each recipient. From April 2022 Scotland counts "
        "the allowance in full here and takes the £15 from total unearned "
        "income (council_tax_reduction_working_age_applicable_income). Child "
        "Benefit, the "
        "income-related benefits, disability benefits, Housing Benefit and "
        "child maintenance do not. Actual savings interest, dividends and rent "
        "are treated as capital, which yields tariff income instead. Scotland "
        "counts a closed list (SSI 2021/249 reg 57(1)). Before April 2022 its "
        "scheme (SSI 2012/303), and the Welsh one, count gross income other "
        "than earnings less their disregards for applicants without Universal "
        "Credit (SSI 2012/303 reg 39 and Sch 4; WSI 2013/3029 Sch 6 paras 9 "
        "and 17 and Sch 9), of which the model counts the sources above. "
        "Before April 2022 the model also uses these rules for Scottish "
        "Universal Credit claims, which SSI 2012/303 reg 26 assessed "
        "separately, mainly from the Secretary of State's income figure plus "
        "all or part of the award. The model does not apply SSI 2012/303 "
        "Sch 4 para 3, which disregards tax paid on income counted under "
        "reg 39."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
        "https://www.legislation.gov.uk/asp/2018/9/section/24",
        "https://www.socialsecurity.gov.scot/publications/2017/07/carer-support-payment-decision-making-guide/pages/payment-of-carer-support-payment/effect-on-other-benefits-for-carer-support-payment-clients",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/36",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26/made",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26/2022-03-31",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/39/2022-03-31",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/4/paragraph/3/2022-03-31",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/4/paragraph/20/2022-03-31",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/4/paragraph/40/2022-03-31",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/4/paragraph/48/2022-03-31",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/17",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/21",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/40",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/49",
        "https://www.legislation.gov.uk/wsi/2012/3144/schedule/9/made",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/39A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        members = working_age_applicant_or_partner(person, period)
        income = add_for_members(
            benunit,
            period,
            [
                "state_pension",
                "private_pension_income",
                "jsa_contrib",
                "esa_contrib",
                "carers_allowance",
                # Carer Support Payment after the CSP Regs (SSI 2023/302) reg
                # 16(2) overlapping-benefit reduction. Reg 57(1)(b) counts
                # benefits "to which the applicant is entitled". We read that
                # as the CSP the carer "is entitled to be given under a
                # determination" (Social Security (Scotland) Act 2018 s. 24),
                # the amount reg 16(2) reduces. Social Security Scotland's
                # guidance also takes the CSP a carer receives into account.
                "carer_support_payment",
                "maternity_allowance",
                "iidb",
                "incapacity_benefit",
                "sda",
                # Part 5 miscellaneous income (SSI 2021/249 reg 57(1)(o); in
                # Wales, gross income other than earnings, Sch 6 para 17).
                "taxable_miscellaneous_income",
            ],
            members,
        )
        # Tax credits are the benefit unit's claimant's and partner's.
        tax_credits = applicant_family(benunit, period) * add(
            benunit, period, ["working_tax_credit", "child_tax_credit"]
        )
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        basic_income = (
            add_for_members(benunit, period, ["basic_income"], members)
            if bi.interactions.include_in_means_tests
            else 0
        )
        disregards = parameters(
            period
        ).gov.local_authorities.council_tax_reduction.income_disregards
        # Spousal maintenance counts: SSI 2021/249 reg 57(1)(d); before April
        # 2022, SSI 2012/303 reg 39(1) (gross income); WSI 2013/3029 Sch 6
        # para 17 (Sch 9 para 19(2)(a) keeps payments from a former partner
        # out of the voluntary-payment disregard). Each scheme aggregates the
        # family's maintenance for one £15 weekly disregard where the family
        # includes a child or young person: reg 57(6) ("Where an applicant's
        # family includes at least one child or young person"), SSI 2012/303
        # Sch 4 para 48 (the same words, as substituted from 1 May 2016 by SSI
        # 2016/81; before then the family premium condition, which the same
        # families met for the ordinary applicable amount without Universal
        # Credit) and WSI 2013/3029 Sch 9 para 49 (where the applicable
        # amount includes the family premium, which Sch 6 para 1(1)(c) gives a
        # family with at least one child or young person; WSI 2012/3144 Sch 9
        # para 49 in 2013-14).
        # The model treats the whole spousal_maintenance_income input as
        # qualifying. Reg 57(1)(d) counts maintenance under a court order or
        # an agreement, and Wales and Scotland before April 2022 give the
        # disregard for payments by a former partner. The input pools current
        # and former spouses' or civil partners' payments, voluntary ones
        # included, and leaves out former unmarried partners.
        # The child test (working_age_child) uses the model's Council Tax
        # Reduction child flag
        # (is_child_or_young_person_for_council_tax_reduction) and benefit-unit
        # membership as a proxy for the statutory family. The flag excludes
        # every child the model identifies as looked after through
        # is_looked_after_child. Scotland's reg 7(8) is narrower: from April
        # 2022 it left out a looked-after child unless placed with or living
        # with a parent, a person with parental responsibility or an approved
        # kinship carer, and from 31 October 2024 (SSI 2024/230) it leaves out
        # only a child placed with a foster carer.
        # So the model can deny the disregard where reg 7 counts a looked-after
        # child. The flag also omits the run-on after a child's death and the
        # Welsh and pre-April 2022 Scottish leaving-care exclusions
        # (#2935). A household head who applies alone has no children
        # in the assessment, so gets no disregard.
        maintenance = benunit.sum(
            max_(0, person("spousal_maintenance_income", period)) * members
        )
        has_child = benunit.any(working_age_child(person, period))
        maintenance_disregard = where(
            has_child,
            min_(maintenance, disregards.maintenance * WEEKS_IN_YEAR),
            0,
        )
        # Widowed Parent's Allowance counts: SSI 2021/249 reg 57(1)(b)(vi);
        # before April 2022, SSI 2012/303 reg 39(1); WSI 2013/3029 Sch 6 para
        # 17. Wales and Scotland before April 2022 disregard £15 weekly "of"
        # the allowance (WSI 2013/3029 Sch 9 para 21; WSI 2012/3144 Sch 9 para
        # 21; SSI 2012/303 Sch 4 para 20), so it counts less £15 weekly, never
        # below nil, for each recipient. From April 2022 Scotland disregards
        # £15 weekly "from the applicant's weekly unearned income" where the
        # applicant receives the allowance (reg 57(4)), so it counts in full
        # here and council_tax_reduction_working_age_applicable_income takes
        # the £15 from total unearned income. Reg 36(1) reads "any reference
        # to the 'applicant' in this Part" as including the partner and,
        # unlike reg 57(6), reg 57(4) does not aggregate payments, so the
        # model gives each recipient a disregard.
        # Neither £20 cap is applied. SSI 2012/303 Sch 4 para 40 capped its
        # para 20 disregard and some student income disregards together at
        # £20 a week. WSI 2013/3029 Sch 9 para 40 also covers its para 20 (£10
        # of a war disablement or war widow's pension and some other
        # pensions). SSI 2021/249 has no cap. A cap can bind where a recipient
        # also has a listed student disregard or, in Wales, a para 20
        # disregard, or where two members of one family each get the allowance
        # disregard, which a lawful award rules out (the allowance ends on
        # remarriage or a new civil or cohabiting partnership, and is not paid
        # while the recipient lives with someone as a couple: SSCBA 1992
        # s.39A(4) to (5)). This route models no student income and, like
        # housing_benefit_widowed_parents_allowance_income, counts no war
        # pension, so only synthetic couples reach a cap. WSI 2013/3029 reg
        # 34(5) makes only the para 20(a) and (b) amounts minima.
        p_scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.means_test
        disregard_from_unearned_income = (
            is_scotland_scheme(benunit.household("country", period))
            & p_scotland.working_age_widowed_parents_allowance_disregard_from_unearned_income
        )
        allowance = max_(0, person("widowed_parents_allowance", period))
        allowance_after_disregard = max_(
            0, allowance - disregards.widowed_parents_allowance * WEEKS_IN_YEAR
        )
        widowed_parents_allowance = where(
            disregard_from_unearned_income,
            benunit.sum(allowance * members),
            benunit.sum(allowance_after_disregard * members),
        )
        return (
            income
            + tax_credits
            + basic_income
            + maintenance
            - maintenance_disregard
            + widowed_parents_allowance
        )

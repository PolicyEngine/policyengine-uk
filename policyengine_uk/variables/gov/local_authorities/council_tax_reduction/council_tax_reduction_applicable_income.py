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
        "Income taken into account in the Council Tax Reduction means test. The "
        "pensioner schemes disregard the whole income of an applicant who, or "
        "whose partner, is in receipt of Pension Credit guarantee credit, and "
        "use the Secretary of State's Pension Credit assessment of income, plus "
        "the savings credit payable, where the award is savings credit only. "
        "Otherwise a pension-age family's net earnings are reduced by the "
        "pensioner earnings disregards. Great Britain's pensioner schemes "
        "also exclude Child Benefit from general-rule income; statutory sick "
        "and maternity pay remain counted as earnings. The other adjustments those "
        "provisions allow (childcare charges, the £20 earnings disregards, "
        "maintenance disregards and the rest) are not modelled. "
        "The income counted is the Council Tax Reduction applicant's and "
        "partner's (is_council_tax_reduction_applicant_or_partner), with, as "
        "the model did before, the income of the family's children or young "
        "persons. Where the household head applies alone "
        "(council_tax_reduction_head_applies_alone), the benefit unit's own "
        "awards (Child Benefit, Income Support, income-based JSA, "
        "income-related ESA, Universal Credit, tax credits, Pension Credit) "
        "and its children belong to its claimant and partner, not to the "
        "head, so none of them counts. "
        "No scheme "
        "counts income derived from capital, such as rent from property, "
        "interest and dividends, as income, so it is not listed and tax on it "
        "is not deducted (legacy_means_test_income_tax). The pensioner schemes "
        "disregard any actual income from capital; the Welsh working-age "
        "scheme and the English default scheme treat it as capital; the "
        "Scottish working-age scheme counts only the unearned income it "
        "lists, which includes the assumed yield from capital but not actual "
        "rent, interest or dividends. Instead, the national schemes (England "
        "for pensioners, Wales and Scotland) count the tariff income they "
        "treat capital as yielding (council_tax_reduction_tariff_income); the "
        "English local schemes for people under pension age add their own. "
        "Rent for letting part of the home counts, less the sub-tenant "
        "disregard, on the schemes' own income rules. It does not count "
        "where a working-age applicant has an award of Universal Credit, "
        "whose income the schemes take from the Secretary of State's "
        "Universal Credit assessment (which does not count it), or in the "
        "Scottish scheme for people under pension age from April 2022, which "
        "does not list it."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/16",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/10",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
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
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/21",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/36",
    ]

    def formula(benunit, period, parameters):
        # Members whose income counts: the applicant and partner and, as the model
        # did before, the programme's own children or young persons. The regulations
        # count only the applicant's and partner's (CTR (Prescribed Requirements)
        # (England) Regs 2012 Sch 1 para 11; SSI 2012/319 reg 21 and SSI 2021/249
        # reg 36, which also exclude a child's); dropping dependants' own income is
        # a follow-up. Anyone else in the benefit unit does not count. A household
        # head who applies alone is the applicant, whatever else the benefit unit
        # reads her as, and the benefit unit's children are its claimant's.
        person = benunit.members
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        applicant_family = ~head_applies_alone
        members = person("is_council_tax_reduction_applicant_or_partner", period) | (
            person("is_child_or_young_person_for_council_tax_reduction", period)
            & benunit.project(applicant_family)
        )
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
            # Whether CTR counts CSP before or after the CSP Regs reg 16(2)
            # overlapping-benefit reduction is unsettled: SSI 2012/319 reg
            # 27(3) grosses up deductions other than the reg 27(5)
            # adjustments, which do not list reg 16(2), while SSI 2021/249 reg
            # 57(1)(b) counts the amount the applicant is entitled to. Until
            # that is decided, the amount before the reduction is counted, as
            # it was before the reduction was modelled.
            "carer_support_payment_pre_overlap",
            "esa_contrib",
            "jsa_contrib",
            "state_pension",
            "maternity_allowance",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
        ]
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
        credits = applicant_family * add(benunit, period, ["tax_credits"])
        increased_income = income + personal_benefit_income + credits + benefits
        # Rent for letting part of the home counts under the schemes' own
        # income rules, less the sub-tenant disregard. Two exceptions:
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
            benunit("legacy_benefits_home_letting_income", period),
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
        tax = add_for_members(
            benunit,
            period,
            ["legacy_means_test_income_tax", "national_insurance"],
            members,
        )
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
            - benunit("pension_credit_war_pension_income", period),
        ) + benunit("pension_credit", period)
        return select(
            [in_receipt_of_guarantee_credit, has_savings_credit_only_award],
            [0, savings_credit_only_income],
            default=income_under_general_rules,
        )

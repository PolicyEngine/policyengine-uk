from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_kingston_upon_thames_working_age,
    is_newham_working_age,
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
        "maintenance disregards and the rest) are not modelled. Industrial "
        "injuries disablement benefit, severe disablement allowance and "
        "incapacity benefit count in every scheme. War pensions and Armed "
        "Forces Compensation Scheme payments count, less £10 a week each, "
        "only under the Kingston upon Thames and Newham working-age schemes: "
        "Scotland disregards or omits them, and elsewhere in England and "
        "Wales councils may disregard them beyond the prescribed £10 a week, "
        "so the model takes the full disregard."
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
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/39",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/54",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/34",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/17",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3/paragraph/1",
        "https://www.legislation.gov.uk/ukpga/1992/14/schedule/1A/paragraph/2",
        "https://www.kingston.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%202026%20-%202027.pdf#page=136",
        "https://www.newham.gov.uk/downloads/file/10753/council-tax-reduction-scheme-2026#page=292",
    ]

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (CTR (Prescribed Requirements) (England)
        # Regs 2012 Sch 1 para 11); dropping dependants' own income is a follow-up.
        # Anyone else in the benefit unit does not count.
        person = benunit.members
        # A household head who applies alone
        # (council_tax_reduction_head_applies_alone) is not the benefit unit's
        # claimant, so this mask has reached them only as a Child Benefit young
        # person. The applicant's own income always counts (SSI 2021/249 reg
        # 36(1)), so they stay counted where Scotland's working-age scheme no
        # longer reads them as a young person.
        applicant_counted_as_young_person = person(
            "is_council_tax_reduction_applicant_or_partner", period
        ) & person("is_child_or_young_person_for_legacy_benefits", period)
        members = (
            person("is_claimant_or_partner", period)
            | person("is_child_or_young_person_for_council_tax_reduction", period)
            | applicant_counted_as_young_person
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
            # Every scheme the model runs counts these three benefits. At
            # pension age they are social security benefits that the income
            # lists do not except: SI 2012/2885 Sch 1 para 16(1)(j), the
            # default scheme SI 2012/2886 Sch para 39(1)(j), WSI 2013/3029
            # Sch 1 para 10(1)(j) and SSI 2012/319 reg 27(1)(j). At working
            # age England and Wales count gross income (SI 2012/2886 Sch para
            # 54(1); WSI 2013/3029 Sch 6 para 17(1)) less disregards that do
            # not list them (their Schs 8 and 9), and Scotland's closed list
            # names them (SSI 2021/249 reg 57(1)(b)(ix) to (xi)). Each scheme
            # leaves out IIDB's constant attendance and exceptionally severe
            # disablement increases (SSCBA 1992 ss.104 and 105), by name or as
            # "attendance allowance" (Sch 8 and Sch 9 para 14), but iidb is
            # the whole reported payment and cannot separate them.
            "iidb",
            "sda",
            "incapacity_benefit",
        ]
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
        # further (s.13A(1)(c)). Where the model cannot see the council's
        # choice it takes the full disregard, as Housing Benefit does for local
        # schemes under SSAA 1992 s.134(8)(a). Reg 34(5) does not cover
        # guaranteed income payments, so in Wales that over-disregards them,
        # but afcs does not separate them from war disablement pensions.
        # Of the English working-age schemes the model runs, Westminster's,
        # Oxford's and Merton's disregard war pensions in full. Kingston upon
        # Thames (Sch 8 para 20) and Newham (Sch 8 para 19) disregard £10 a
        # week of each payment, the reading Pension Credit's identically
        # worded disregard takes, and Kingston limits the family's total to
        # £20 a week (Sch 8 para 40). Newham's limit (its para 39) names its
        # paras 20 and 21, not the war pension para 19, so it does not apply.
        income_components = [
            "employment_income",
            "self_employment_income",
            "property_income_after_finance_costs",
            "private_pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        benefits = add_for_members(
            benunit, period, benunit_means_tested_benefits, members
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
        benefits -= where(
            pensioner & in_great_britain,
            add_for_members(benunit, period, ["child_benefit"], members),
            0,
        )
        income = add_for_members(benunit, period, income_components, members)
        personal_benefit_income = add_for_members(
            benunit, period, personal_benefits, members
        )
        credits = add_for_members(benunit, period, ["tax_credits"], members)
        increased_income = income + personal_benefit_income + credits + benefits

        local_authority = benunit.household("local_authority", period)
        kingston = is_kingston_upon_thames_working_age(
            local_authority, country, pensioner
        )
        newham = is_newham_working_age(local_authority, country, pensioner)
        local_authorities = parameters(period).gov.local_authorities
        kingston_test = (
            local_authorities.kingston_upon_thames.council_tax_reduction.means_test
        )
        newham_test = local_authorities.newham.council_tax_reduction.means_test
        payment_disregard = WEEKS_IN_YEAR * where(
            kingston,
            kingston_test.war_pension_disregard,
            newham_test.war_pension_disregard,
        )
        war_pensions = 0
        war_pension_disregards = 0
        for payment in ["afcs", "war_widows_pension"]:
            amount = person(payment, period) * members
            war_pensions += benunit.sum(amount)
            war_pension_disregards += benunit.sum(
                min_(amount, benunit.project(payment_disregard))
            )
        war_pension_disregards = where(
            kingston,
            min_(
                war_pension_disregards,
                kingston_test.war_pension_disregard_limit * WEEKS_IN_YEAR,
            ),
            war_pension_disregards,
        )
        increased_income += where(
            kingston | newham, war_pensions - war_pension_disregards, 0
        )

        if not bi.interactions.include_in_means_tests:
            increased_income -= add_for_members(
                benunit, period, ["basic_income"], members
            )

        pension_contributions = (
            add_for_members(benunit, period, ["pension_contributions"], members) * 0.5
        )
        tax = add_for_members(
            benunit, period, ["income_tax", "national_insurance"], members
        )
        # SI 2012/2885 Sch 1 para 17(9) and Sch 4; WSI 2013/3029 Sch 1 para
        # 11(9) and Sch 3; SSI 2012/319 reg 31(8) and Sch 2: the pensioner
        # earnings disregards, capped at net earnings. Zero for working-age
        # families.
        earnings_disregard = benunit(
            "council_tax_reduction_pensioner_earnings_disregard", period
        )
        income_under_general_rules = max_(
            0, increased_income - tax - pension_contributions - earnings_disregard
        )
        # SI 2012/2885 Sch 1 para 13, WSI 2013/3029 Sch 1 para 7 and SSI
        # 2012/319 reg 24: a guarantee credit recipient's whole income is
        # disregarded. Para 14, para 8 and reg 25: in savings-credit-only cases
        # the Secretary of State's assessment of net income is used, adjusted
        # to take account of the savings credit payable. The Pension Credit
        # paid on a savings-credit-only award is that savings credit (under the
        # Pension Credit freeze, the frozen amount).
        in_receipt_of_guarantee_credit = benunit(
            "in_receipt_of_guarantee_credit", period
        )
        has_savings_credit_only_award = benunit(
            "in_receipt_of_savings_credit_only", period
        )
        savings_credit_only_income = benunit("pension_credit_income", period) + benunit(
            "pension_credit", period
        )
        return select(
            [in_receipt_of_guarantee_credit, has_savings_credit_only_award],
            [0, savings_credit_only_income],
            default=income_under_general_rules,
        )

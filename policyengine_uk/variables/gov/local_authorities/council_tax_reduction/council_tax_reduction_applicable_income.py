from policyengine_uk.model_api import *
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
        "maintenance disregards and the rest) are not modelled."
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
        ]
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
            ["income_tax_before_winter_fuel_payment_charge", "national_insurance"],
            members,
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

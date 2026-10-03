from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
    is_wales_scheme,
)


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
        "The other adjustments those provisions allow (childcare charges, lone "
        "parent and maintenance disregards, and the rest) are not modelled. "
        "No scheme counts income derived from capital, such as rent from property, interest and "
        "dividends, as income, so it is not listed and tax on it is not "
        "deducted. The pensioner schemes disregard any actual income from "
        "capital; the Welsh working-age scheme and the English default scheme "
        "treat it as capital; the Scottish working-age scheme counts only the "
        "unearned income it lists, which includes the assumed yield from "
        "capital but not actual rent, interest or dividends. Rent for letting "
        "part of the home counts, less the sub-tenant disregard, except in the "
        "Scottish scheme for people under pension age from April 2022, which "
        "does not list it."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/64",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/4",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
    ]

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (CTR (Prescribed Requirements) (England)
        # Regs 2012 Sch 1 para 11); dropping dependants' own income is a follow-up.
        # Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_young_person_for_legacy_benefits", period
        )
        benunit_means_tested_benefits = [
            "child_benefit",
            "income_support",
            "jsa_income",
            "esa_income",
            "universal_credit",
        ]
        personal_benefits = [
            "carers_allowance",
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
        benefits = add_for_members(
            benunit, period, benunit_means_tested_benefits, members
        )
        income = add_for_members(benunit, period, income_components, members)
        personal_benefit_income = add_for_members(
            benunit, period, personal_benefits, members
        )
        credits = add_for_members(benunit, period, ["tax_credits"], members)
        increased_income = income + personal_benefit_income + credits + benefits
        # Rent for letting part of the home counts in every scheme except the
        # Scottish one for people under pension age from 1 April 2022 (SSI
        # 2021/249, whose reg 57(1) list has no head for it). That scheme
        # applies under reg 3(1) to an applicant under pensionable age, or over
        # it where the applicant or partner has an award of universal credit or
        # a qualifying income-related benefit.
        claimant_or_partner_over_pension_age = benunit.any(
            person("is_SP_age", period) & person("is_claimant_or_partner", period)
        )
        on_uc_or_income_related_benefit = (
            add(
                benunit,
                period,
                ["universal_credit", "income_support", "jsa_income", "esa_income"],
            )
            > 0
        )
        scotland = is_scotland_scheme(benunit.household("country", period))
        scottish_working_age_scheme = scotland & (
            ~claimant_or_partner_over_pension_age | on_uc_or_income_related_benefit
        )
        p_scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.means_test
        # Wales: for an applicant with an award of universal credit (who is
        # never a pensioner, WSI 2013/3029 reg 3), income is the Secretary of
        # State's universal credit assessment (Sch 6 para 9), which has no
        # rent from part of the home. That route is otherwise not modelled
        # here (#1966); this keeps such rent out of it.
        wales_universal_credit_route = is_wales_scheme(
            benunit.household("country", period)
        ) & (add(benunit, period, ["universal_credit"]) > 0)
        counts_home_letting = (
            ~scottish_working_age_scheme
            | p_scotland.working_age_counts_home_letting_income
        ) & ~wales_universal_credit_route
        increased_income += where(
            counts_home_letting,
            benunit("legacy_benefits_home_letting_income", period),
            0,
        )

        if not bi.interactions.include_in_means_tests:
            increased_income -= add_for_members(
                benunit, period, ["basic_income"], members
            )

        pension_contributions = (
            add_for_members(benunit, period, ["pension_contributions"], members) * 0.5
        )
        tax = add_for_members(
            benunit,
            period,
            ["legacy_means_test_income_tax", "national_insurance"],
            members,
        )
        # Where the rent is not counted, neither is the tax on it.
        tax -= where(
            counts_home_letting,
            0,
            add_for_members(
                benunit, period, ["rent_a_room_income_tax_after_reductions"], members
            ),
        )
        income_under_general_rules = max_(
            0, increased_income - tax - pension_contributions
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

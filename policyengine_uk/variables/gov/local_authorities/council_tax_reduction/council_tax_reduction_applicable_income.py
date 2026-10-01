from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
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
        "Scottish working-age scheme, which does not list it."
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
        benefits = add(benunit, period, benunit_means_tested_benefits)
        income = add(benunit, period, income_components)
        personal_benefit_income = add(benunit, period, personal_benefits)
        credits = add(benunit, period, ["tax_credits"])
        increased_income = income + personal_benefit_income + credits + benefits
        scotland_working_age = is_scotland_scheme(
            benunit.household("country", period)
        ) & ~benunit.household("council_tax_reduction_household_has_pensioner", period)
        increased_income += where(
            scotland_working_age,
            0,
            benunit("legacy_benefits_home_letting_income", period),
        )

        if not bi.interactions.include_in_means_tests:
            increased_income -= add(benunit, period, ["basic_income"])

        pension_contributions = add(benunit, period, ["pension_contributions"]) * 0.5
        tax = add(
            benunit, period, ["legacy_means_test_income_tax", "national_insurance"]
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

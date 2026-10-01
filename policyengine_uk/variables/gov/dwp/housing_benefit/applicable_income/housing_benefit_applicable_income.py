from policyengine_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Housing Benefit means test"
    documentation = (
        "Income taken into account for Housing Benefit. Income derived from "
        "capital, such as rent from property, interest and dividends, is not "
        "income: for working-age claimants regulation 46(4) treats it as "
        "capital and Schedule 5 paragraph 17 disregards it, and for claimants "
        "over the qualifying age for State Pension Credit Schedule 5 paragraph "
        "22 of the pension-age regulations disregards any actual income from "
        "capital. The capital counts through the capital limit and tariff "
        "income. Tax on that income is not deducted. Rent for letting part of "
        "the home stays income, less the sub-tenant disregard. Rent from other "
        "premises whose value is disregarded also stays income, but the model "
        "cannot identify those premises."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/46",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5",
    ]

    def formula(benunit, period, parameters):
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "child_benefit",
            "income_support",
            "jsa_income",
            "esa_income",
        ]
        PERSONAL_BENEFITS = [
            "carers_allowance",
            "carer_support_payment",
            "esa_contrib",
            "jsa_contrib",
            "state_pension",
            "maternity_allowance",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
        ]
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "private_pension_income",
            "legacy_benefits_home_letting_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        # Add personal benefits, credits and total benefits to income
        benefits = add(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS)
        income = add(benunit, period, INCOME_COMPONENTS)
        personal_benefits = add(benunit, period, PERSONAL_BENEFITS)
        credits = add(benunit, period, ["tax_credits"])
        increased_income = income + personal_benefits + credits + benefits

        if not bi.interactions.include_in_means_tests:
            # Basic income is already in personal benefits, deduct if needed
            increased_income -= add(benunit, period, ["basic_income"])
        # Reduce increased income by pension contributions and tax
        pension_contributions = add(benunit, period, ["pension_contributions"]) * 0.5
        TAX_COMPONENTS = ["legacy_means_test_income_tax", "national_insurance"]
        tax = add(benunit, period, TAX_COMPONENTS)
        increased_income_reduced_by_tax_and_pensions = (
            increased_income - tax - pension_contributions
        )
        tariff_income = benunit("housing_benefit_tariff_income", period)
        disregard = benunit("housing_benefit_applicable_income_disregard", period)
        childcare_element = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        applicable_income = max_(
            0,
            increased_income_reduced_by_tax_and_pensions
            + tariff_income
            - disregard
            - childcare_element,
        )
        guarantee_credit = any_over_SP_age & (benunit("guarantee_credit", period) > 0)
        return where(guarantee_credit, 0, applicable_income)

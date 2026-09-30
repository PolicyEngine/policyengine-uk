from policyengine_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Housing Benefit means test"
    documentation = (
        "Income taken into account in the Housing Benefit means test. It is "
        "zero where anyone in the family is over State Pension age and the "
        "family's guarantee credit is positive (the guarantee credit "
        "passport). Where the Pension Credit award is savings credit only, it "
        "is the Secretary of State's assessment of income plus the savings "
        "credit payable, less childcare charges and the earnings disregards. "
        "Otherwise it is the family's income under the Housing Benefit rules."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/26",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/24",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
    )

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
            "property_income",
            "private_pension_income",
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
        TAX_COMPONENTS = ["income_tax", "national_insurance"]
        tax = add(benunit, period, TAX_COMPONENTS)
        increased_income_reduced_by_tax_and_pensions = (
            increased_income - tax - pension_contributions
        )
        tariff_income = benunit("housing_benefit_tariff_income", period)
        disregard = benunit("housing_benefit_applicable_income_disregard", period)
        childcare_element = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        income_under_general_rules = max_(
            0,
            increased_income_reduced_by_tax_and_pensions
            + tariff_income
            - disregard
            - childcare_element,
        )
        # SI 2006/214 reg 27 (NI: SR 2006/406 reg 25): where the award of
        # Pension Credit is savings credit only, the Secretary of State's
        # assessment of income is used instead, plus the savings credit.
        savings_credit_only = benunit("in_receipt_of_savings_credit_only", period)
        applicable_income = where(
            savings_credit_only,
            benunit("housing_benefit_savings_credit_only_income", period),
            income_under_general_rules,
        )
        guarantee_credit = any_over_SP_age & (benunit("guarantee_credit", period) > 0)
        return where(guarantee_credit, 0, applicable_income)

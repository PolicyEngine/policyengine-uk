from policyengine_uk.model_api import *


def create_basic_income_interactions() -> Reform:
    """
    Reform that modifies how basic income interacts with existing benefits.

    This reform checks the contrib parameters within each formula to allow
    individual control over each interaction:
    1. withdraw_cb - Withdraws Child Benefit from basic income recipients
    2. include_in_taxable_income - Includes basic income in taxable income
    3. include_in_means_tests - Includes basic income in means tests
    """

    class child_benefit_respective_amount(Variable):
        label = "Child Benefit (respective amount)"
        documentation = "The amount of this benefit unit's Child Benefit which is in respect of this person"
        entity = Person
        definition_period = MONTH
        value_type = float
        unit = GBP
        reference = (
            "https://www.legislation.gov.uk/ukpga/1992/4/part/IX",
            "https://www.legislation.gov.uk/uksi/2006/965/regulation/2",
        )
        defined_for = "is_child_or_QYP"

        def formula(person, period, parameters):
            eligible = True
            bi = parameters(period).gov.contrib.ubi_center.basic_income
            if bi.interactions.withdraw_cb:
                eligible = (
                    person.benunit.sum(
                        person("basic_income", period.this_year)
                    )
                    == 0
                )
            is_eldest = person("is_eldest_child", period.this_year)
            child_benefit = parameters(period).gov.hmrc.child_benefit.amount
            amount = where(
                is_eldest, child_benefit.eldest, child_benefit.additional
            )
            return eligible * amount * WEEKS_IN_YEAR / MONTHS_IN_YEAR

    class adjusted_net_income(Variable):
        value_type = float
        entity = Person
        label = "Taxable income after tax reliefs and before allowances"
        definition_period = YEAR
        reference = dict(
            title="Income Tax Act 2007, s. 23",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        )
        unit = GBP

        def formula(person, period, parameters):
            adjusted_net_income_components = parameters(
                period
            ).gov.hmrc.income_tax.adjusted_net_income_components

            # Find adjusted net income
            ani = add(person, period, adjusted_net_income_components)

            # Add basic income if parameter is set
            bi = parameters(period).gov.contrib.ubi_center.basic_income
            if bi.interactions.include_in_taxable_income:
                ani += person("basic_income", period)

            return max_(0, ani)

    class tax_credits_applicable_income(Variable):
        value_type = float
        entity = BenUnit
        label = "Applicable income for Tax Credits"
        definition_period = YEAR
        unit = GBP
        reference = "The Tax Credits (Definition and Calculation of Income) Regulations 2002 s. 3"

        def formula(benunit, period, parameters):
            TC = parameters(period).gov.dwp.tax_credits
            STEP_1_COMPONENTS = [
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
                "property_income",
            ]
            income = add(benunit, period, STEP_1_COMPONENTS)
            income = max_(income - TC.means_test.non_earned_disregard, 0)
            STEP_2_COMPONENTS = [
                "employment_income",
                "self_employment_income",
                "social_security_income",
                "miscellaneous_income",
            ]
            bi = parameters(period).gov.contrib.ubi_center.basic_income
            if bi.interactions.include_in_means_tests:
                STEP_2_COMPONENTS.append("basic_income")
            income += add(benunit, period, STEP_2_COMPONENTS)
            EXEMPT_BENEFITS = ["income_support", "esa_income", "jsa_income"]
            on_exempt_benefits = add(benunit, period, EXEMPT_BENEFITS) > 0
            return income * ~on_exempt_benefits

    class pension_credit_income(Variable):
        label = "Income for Pension Credit"
        entity = BenUnit
        definition_period = YEAR
        value_type = float
        unit = GBP
        reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/15"

        def formula(benunit, period, parameters):
            pc = parameters(period).gov.dwp.pension_credit
            sources = pc.guarantee_credit.income
            total = add(benunit, period, sources)
            bi = parameters(period).gov.contrib.ubi_center.basic_income
            if bi.interactions.include_in_means_tests:
                total += add(benunit, period, ["basic_income"])
            pension_contributions = add(
                benunit, period, ["pension_contributions"]
            )
            tax = add(benunit, period, ["income_tax", "national_insurance"])
            pen_con_deduction_rate = pc.income.pension_contributions_deduction
            deductions = tax + pension_contributions * pen_con_deduction_rate
            return max_(0, total - deductions)

    class income_support_applicable_income(Variable):
        value_type = float
        entity = BenUnit
        label = "Relevant income for Income Support means test"
        definition_period = YEAR
        unit = GBP

        def formula(benunit, period, parameters):
            IS = parameters(period).gov.dwp.income_support
            INCOME_COMPONENTS = [
                "employment_income",
                "self_employment_income",
                "property_income",
                "private_pension_income",
            ]
            bi = parameters(period).gov.contrib.ubi_center.basic_income
            if bi.interactions.include_in_means_tests:
                INCOME_COMPONENTS.append("basic_income")
            income = add(benunit, period, INCOME_COMPONENTS)
            tax = add(
                benunit,
                period,
                ["income_tax", "national_insurance"],
            )
            income += add(benunit, period, ["social_security_income"])
            income -= tax
            income -= add(benunit, period, ["pension_contributions"]) * 0.5
            family_type = benunit("family_type", period)
            families = family_type.possible_values
            # Calculate income disregards for each family type.
            mt = IS.means_test
            single = family_type == families.SINGLE
            income_disregard_single = single * mt.income_disregard_single
            single = family_type == families.SINGLE
            income_disregard_couple = (
                benunit("is_couple", period) * mt.income_disregard_couple
            )
            lone_parent = family_type == families.LONE_PARENT
            income_disregard_lone_parent = (
                lone_parent * mt.income_disregard_lone_parent
            )
            income_disregard = (
                income_disregard_single
                + income_disregard_couple
                + income_disregard_lone_parent
            ) * WEEKS_IN_YEAR
            return max_(0, income - income_disregard)

    class housing_benefit_applicable_income(Variable):
        value_type = float
        entity = BenUnit
        label = "relevant income for Housing Benefit means test"
        definition_period = YEAR
        unit = GBP

        def formula(benunit, period, parameters):
            BENUNIT_MEANS_TESTED_BENEFITS = [
                "child_benefit",
                "income_support",
                "jsa_income",
                "esa_income",
            ]
            PERSONAL_BENEFITS = [
                "carers_allowance",
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
                # Exclude basic income from means tests
                increased_income -= add(benunit, period, ["basic_income"])

            # Reduce increased income by pension contributions and tax
            pension_contributions = (
                add(benunit, period, ["pension_contributions"]) * 0.5
            )
            TAX_COMPONENTS = ["income_tax", "national_insurance"]
            tax = add(benunit, period, TAX_COMPONENTS)
            increased_income_reduced_by_tax_and_pensions = (
                increased_income - tax - pension_contributions
            )
            disregard = benunit(
                "housing_benefit_applicable_income_disregard", period
            )
            childcare_element = benunit(
                "housing_benefit_applicable_income_childcare_element", period
            )
            return max_(
                0,
                increased_income_reduced_by_tax_and_pensions
                - disregard
                - childcare_element,
            )

    class uc_mif_capped_earned_income(Variable):
        value_type = float
        entity = Person
        label = "Universal Credit gross earned income (incl. MIF)"
        documentation = (
            "Gross earned income for UC, with MIF applied where applicable"
        )
        definition_period = YEAR
        unit = GBP

        def formula(person, period, parameters):
            INCOME_COMPONENTS = [
                "employment_income",
                "self_employment_income",
                "miscellaneous_income",
            ]
            bi = parameters(period).gov.contrib.ubi_center.basic_income
            if bi.interactions.include_in_means_tests:
                INCOME_COMPONENTS.append("basic_income")
            personal_gross_earned_income = add(
                person, period, INCOME_COMPONENTS
            )
            floor = where(
                person("uc_mif_applies", period),
                person("uc_minimum_income_floor", period),
                -inf,
            )
            return max_(personal_gross_earned_income, floor)

    class gov_spending(Variable):
        label = "government spending"
        documentation = (
            "Government spending impact in respect of this household."
        )
        entity = Household
        definition_period = YEAR
        value_type = float
        unit = GBP
        adds = [
            "child_benefit",
            "esa_income",
            "esa_contrib",
            "housing_benefit",
            "income_support",
            "jsa_income",
            "jsa_contrib",
            "pension_credit",
            "universal_credit",
            "working_tax_credit",
            "child_tax_credit",
            "attendance_allowance",
            "afcs",
            "bsp",
            "carers_allowance",
            "dla",
            "iidb",
            "incapacity_benefit",
            "pip",
            "sda",
            "state_pension",
            "maternity_allowance",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
            "basic_income",  # Added via this reform
            "epg_subsidy",
            "cost_of_living_support_payment",
            "energy_bills_rebate",
            "winter_fuel_allowance",
            "pawhp",
            "other_public_spending_budget_change",
            "tax_free_childcare",
            "extended_childcare_entitlement",
            "universal_childcare_entitlement",
            "targeted_childcare_entitlement",
            "care_to_learn",
            "dfe_education_spending",
            "dft_subsidy_spending",
            "nhs_spending",
        ]

    class reform(Reform):
        def apply(self):
            self.update_variable(child_benefit_respective_amount)
            self.update_variable(adjusted_net_income)
            self.update_variable(tax_credits_applicable_income)
            self.update_variable(pension_credit_income)
            self.update_variable(income_support_applicable_income)
            self.update_variable(housing_benefit_applicable_income)
            self.update_variable(uc_mif_capped_earned_income)
            self.update_variable(gov_spending)

    return reform


def create_basic_income_interactions_reform(
    parameters, period, bypass: bool = False
):
    """
    Creates the basic income interactions reform.

    This reform is ALWAYS applied because the formulas check parameters at
    calculation time. This allows dynamic parameter setting (e.g., in YAML tests
    or API calls) to work correctly.

    Args:
        parameters: The parameter tree (unused, kept for API consistency)
        period: The period (unused, kept for API consistency)
        bypass: If True, return the reform unconditionally (always True here)

    Returns:
        Reform class
    """
    # Always apply this reform - the formulas check parameters internally
    # This matches the US pattern where reforms are always active but
    # their effect depends on parameter values at calculation time
    return create_basic_income_interactions()


# For direct import
basic_income_interactions_reform = create_basic_income_interactions()

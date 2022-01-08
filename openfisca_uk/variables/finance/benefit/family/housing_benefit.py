from openfisca_uk.model_api import *


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit (reported amount)"
    definition_period = YEAR
    unit = "currency-GBP"


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        social = benunit.any(benunit.members("in_social_housing", period))
        return social + benunit("LHA_eligible", period)


class would_claim_HB(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Housing Benefit"
    documentation = (
        "Whether this family would claim Housing Benefit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        would_randomly_take_up = (
            random(benunit) < parameters(period).benefit.housing_benefit.takeup
        )
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        return would_randomly_take_up | claims_all_entitled_benefits


class claims_HB(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Housing Benefit"
    documentation = (
        "Whether this family would claim Housing Benefit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        would_claim_HB = benunit("would_claim_HB", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim_HB & claims_legacy_benefits


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for Housing Benefit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        HB = parameters(period).benefit.housing_benefit
        PA = HB.allowances
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        eldest_age = benunit("eldest_adult_age", period)
        u_18 = eldest_age < 18
        u_25 = eldest_age < 25
        o_25 = (eldest_age >= 25) & ~any_over_SP_age
        o_18 = (eldest_age >= 18) * ~any_over_SP_age
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        single_personal_allowance = (
            u_25 * PA.single.under_25
            + o_25 * PA.single.over_25
            + any_over_SP_age * PA.single.SP_age
        )
        couple_personal_allowance = (
            u_18 * PA.couple.both_under_18
            + o_18 * PA.couple.over_18
            + any_over_SP_age * PA.couple.SP_age
        )
        lone_parent_personal_allowance = (
            u_18 * PA.lone_parent.under_18
            + o_18 * PA.lone_parent.over_18
            + any_over_SP_age * PA.lone_parent.SP_age
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        housing_benefit_eligible = benunit("housing_benefit_eligible", period)
        return (personal_allowance + premiums) * housing_benefit_eligible


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Housing Benefit means test"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        means_test = parameters(period).benefit.housing_benefit.means_test
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "child_benefit",
            "income_support",
            "JSA_income",
            "ESA_income",
        ]
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "pension_income",
        ]
        TAX_COMPONENTS = ["income_tax", "national_insurance"]
        benefits = add(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS)
        income = aggr(benunit, period, INCOME_COMPONENTS)
        tax = aggr(benunit, period, TAX_COMPONENTS)
        income += aggr(benunit, period, ["personal_benefits"])
        income += add(benunit, period, ["tax_credits"])
        income -= tax
        income -= aggr(benunit, period, ["pension_contributions"]) * 0.5
        income += benefits
        num_children = benunit.nb_persons(BenUnit.CHILD)
        childcare_amount_1 = (num_children == 1) * WTC.elements.childcare_1
        childcare_amount_2 = (num_children > 1) * WTC.elements.childcare_2
        max_weekly_childcare_amount = childcare_amount_1 + childcare_amount_2
        max_childcare_amount = max_weekly_childcare_amount * WEEKS_IN_YEAR
        childcare_element = min_(
            max_childcare_amount,
            aggr(benunit, period, ["childcare_expenses"]),
        )
        hours = aggr(benunit, period, ["weekly_hours"])
        # Calculate single, couple, lone parent, and worker disregards.
        single = benunit("is_single_person", period)
        single_disregard = single * means_test.income_disregard_single
        couple = benunit("is_couple", period)
        couple_disregard = couple * means_test.income_disregard_couple
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_disregard = (
            lone_parent * means_test.income_disregard_lone_parent
        )
        hour_requirement = where(
            lone_parent, WTC.min_hours.lower, means_test.worker_hours
        )
        worker = hours > hour_requirement
        worker_disregard = worker * means_test.worker_income_disregard
        weekly_disregard = (
            single_disregard
            + couple_disregard
            + lone_parent_disregard
            + worker_disregard
        )
        disregard = weekly_disregard * WEEKS_IN_YEAR
        return max_(0, income - disregard - childcare_element)


class HB_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Non-dependent deduction (individual)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("benunit_rent", period) == 0
        over_21 = person("age", period) >= 21
        deduction_scale = parameters(
            period
        ).benefit.housing_benefit.deductions.non_dep_deduction
        weekly_income = person("total_income", period)
        deduction = deduction_scale.calc(weekly_income)
        return deduction * over_21 * not_rent_liable * MONTHS_IN_YEAR


class HB_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Non-dependent deductions"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(
                benunit.members("HB_individual_non_dep_deduction", period)
            )
        )
        non_dep_deductions_in_bu = aggr(
            benunit, period, ["HB_individual_non_dep_deduction"]
        )
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        LHA = benunit("LHA_eligible", period.this_year)
        applicable_amount = benunit(
            "housing_benefit_applicable_amount", period
        )
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).benefit.housing_benefit.means_test.withdrawal_rate
        final_amount = max_(
            0, rent - max_(0, income - applicable_amount) * withdrawal_rate
        )
        amount = where(
            LHA, min_(final_amount, benunit("LHA_cap", period)), final_amount
        )
        CAPPED_BENUNIT_BENEFITS = [
            "child_benefit",
            "child_tax_credit",
            "JSA_income",
            "income_support",
            "ESA_income",
        ]
        capped_benunit_benefits = add(benunit, period, CAPPED_BENUNIT_BENEFITS)
        CAPPED_PERSONAL_BENEFITS = [
            "JSA_contrib",
            "incapacity_benefit",
            "ESA_contrib",
            "SDA",
        ]
        capped_personal_benefits = aggr(
            benunit, period, CAPPED_PERSONAL_BENEFITS
        )
        other_capped_benefits = (
            capped_benunit_benefits + capped_personal_benefits
        )
        amount = max_(0, amount - benunit("HB_non_dep_deductions", period))
        final_amount = min_(
            amount * benunit("claims_HB", period),
            benunit("benefit_cap", period) - other_capped_benefits,
        )
        return max_(0, final_amount)

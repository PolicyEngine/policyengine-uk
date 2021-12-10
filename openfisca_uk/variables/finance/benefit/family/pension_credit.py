from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class pension_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Pension Credit"
    definition_period = YEAR


class would_claim_PC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Would claim Pension Credit"
    documentation = (
        "Whether this family would claim Pension Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(period).benefit.pension_credit.takeup
        return (random(benunit) < takeup_rate) + benunit(
            "claims_all_entitled_benefits", period
        )


class claims_PC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim Pension Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("would_claim_PC", period)


class pension_credit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Eligible for Pension Credit"
    definition_period = YEAR

    def formula(benunit, period):
        all_SP_age = benunit.min(benunit.members("is_SP_age", period))
        one_SP_age = benunit.max(benunit.members("is_SP_age", period))
        claiming_HB = benunit("housing_benefit", period) > 0
        return all_SP_age + (one_SP_age * claiming_HB)


class pension_credit_MG(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Minimum Guarantee) amount per week"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        PC = parameters(period).benefit.pension_credit
        personal_allowance = (
            PC.minimum_guarantee[benunit("relation_type", period)]
            * WEEKS_IN_YEAR
        )
        premiums = benunit("severe_disability_premium", period) + benunit(
            "carer_premium", period
        )
        applicable_amount = personal_allowance + premiums
        return (
            applicable_amount
            * benunit("pension_credit_eligible", period)
            * benunit("claims_PC", period)
        )


class guarantee_credit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable income for Pension Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        INCOME_COMPONENTS = [
            "personal_benefits",
            "pension_income",
            "maintenance_income",
            "employment_income",
            "self_employment_income",
            "property_income",
            "savings_interest_income",
            "dividend_income",
        ]
        income = aggr(benunit, period, INCOME_COMPONENTS)
        tax = aggr(
            benunit,
            period,
            ["tax"],
        )
        benefits = add(
            benunit,
            period,
            [
                "child_benefit",
                "child_tax_credit",
                "working_tax_credit",
                "housing_benefit",
            ],
        )
        return amount_over(income + benefits - tax, 0)


class pension_credit_GC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Guarantee Credit) amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        income = benunit("guarantee_credit_applicable_income", period)
        return (
            benunit("pension_credit_eligible", period)
            * benunit("claims_PC", period)
            * max_(0, benunit("pension_credit_MG", period) - income)
        )


class savings_credit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable income for Savings Credit"
    definition_period = YEAR
    reference = "https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others#working-out-income-for-savings-credit"

    def formula(benunit, period, parameters):
        GC_income = benunit("guarantee_credit_applicable_income", period)
        exempted_personal_benefits = aggr(
            benunit,
            period,
            [
                "incapacity_benefit",
                "JSA_contrib",
                "ESA_contrib",
                "SDA",
                "maintenance_income",
            ],
        )
        exempted_family_benefits = add(
            benunit,
            period,
            [
                "working_tax_credit",
            ],
        )
        return amount_over(
            GC_income - exempted_personal_benefits - exempted_family_benefits,
            0,
        )


class pension_credit_SC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Savings Credit) amount per week"
    definition_period = YEAR
    reference = "https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others#legislation-60-return"

    def formula(benunit, period, parameters):
        PC = parameters(period).benefit.pension_credit
        SC = PC.savings_credit
        income = benunit("savings_credit_applicable_income", period)
        appropriate_amount = benunit("pension_credit_MG", period)
        threshold = (
            SC.income_threshold[benunit("relation_type", period)]
            * WEEKS_IN_YEAR
        )
        maximum_amount = (1 - SC.withdrawal_rate) * max_(
            appropriate_amount - threshold, 0
        )

        amount_A = min_(
            (1 - SC.withdrawal_rate) * max_(income - threshold, 0),
            maximum_amount,
        )
        amount_B = (
            amount_over(income - appropriate_amount, 0) * SC.withdrawal_rate
        )
        amount = max_(amount_A - amount_B, 0)

        return (
            amount
            * benunit("pension_credit_eligible", period)
            * benunit("claims_PC", period)
        )


class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        COMPONENTS = ["pension_credit_GC", "pension_credit_SC"]
        amount = add(benunit, period, COMPONENTS)
        return amount

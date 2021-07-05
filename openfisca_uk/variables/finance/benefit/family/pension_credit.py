from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class pension_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Pension Credit"
    definition_period = YEAR


class claims_PC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim Pension Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        already_claiming = (
            aggr(benunit, period, ["pension_credit_reported"]) > 0
        )
        takeup_rate = parameters(period).benefit.pension_credit.takeup
        return already_claiming + (random(benunit) < takeup_rate)


class pension_credit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for Pension Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        both_SP_age = benunit.min(benunit.members("is_SP_age", period))
        one_SP_age = benunit.max(benunit.members("is_SP_age", period))
        claiming_HB = benunit("housing_benefit", period) > 0
        return both_SP_age + (one_SP_age * claiming_HB)


class pension_credit_MG(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Minimum Guarantee) amount per week"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        PC = parameters(period).benefit.pension_credit
        personal_allowance = (
            benunit("is_single", period) * PC.min_guarantee.single
            + benunit("is_couple", period) * PC.min_guarantee.couple
        ) * WEEKS_IN_YEAR
        premiums = benunit("severe_disability_premium", period) + benunit(
            "carer_premium", period
        )
        applicable_amount = personal_allowance + premiums
        return (
            applicable_amount
            * benunit("pension_credit_eligible", period)
            * benunit("claims_PC", period)
        )


class pension_credit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable income for Pension Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        INCOME_COMPONENTS = [
            "employment_income",
            "trading_income",
            "property_income",
            "pension_income",
            "savings_interest_income",
            "dividend_income",
        ]
        income = aggr(benunit, period, INCOME_COMPONENTS)
        tax = aggr(
            benunit,
            period,
            ["income_tax", "national_insurance"],
        )
        income += aggr(benunit, period, ["personal_benefits"])
        income += add(benunit, period, ["child_benefit"])
        income -= tax
        income = amount_over(income, 0)
        return income


class pension_credit_GC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Guarantee Credit) amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_applicable_income", period)
        return (
            benunit("pension_credit_eligible", period)
            * benunit("claims_PC", period)
            * max_(0, benunit("pension_credit_MG", period) - income)
        )


class pension_credit_SC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Savings Credit) amount per week"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        PC = parameters(period).benefit.pension_credit
        income = benunit("pension_credit_applicable_income", period)
        MG_amount = benunit("pension_credit_MG", period)
        threshold = (
            PC.savings_credit.single_threshold
            * benunit("is_single", period)
            * WEEKS_IN_YEAR
            + PC.savings_credit.couple_threshold
            * benunit("is_couple", period)
            * WEEKS_IN_YEAR
        )
        maximum_amount = (
            PC.savings_credit.max_single
            * benunit("is_single", period)
            * WEEKS_IN_YEAR
            + PC.savings_credit.max_single
            * benunit("is_couple", period)
            * WEEKS_IN_YEAR
        )
        income_above_threshold = max_(0, income - threshold)
        income_above_MG = max_(0, income - MG_amount)
        SC_amount = min_(
            income_above_threshold * (1 - PC.savings_credit.withdrawal_rate),
            maximum_amount,
        )
        deduction = income_above_MG * PC.savings_credit.withdrawal_rate
        SC_final_amount = max_(0, SC_amount - deduction)
        return (
            max_(0, SC_final_amount)
            * benunit("pension_credit_eligible", period)
            * benunit("claims_PC", period)
        )


class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension credit amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        COMPONENTS = ["pension_credit_GC", "pension_credit_SC"]
        amount = add(benunit, period, COMPONENTS)
        return amount

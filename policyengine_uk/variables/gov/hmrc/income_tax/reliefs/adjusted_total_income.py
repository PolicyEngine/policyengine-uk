from policyengine_uk.model_api import *


class adjusted_total_income(Variable):
    value_type = float
    entity = Person
    label = "Adjusted total income"
    documentation = (
        "The base of the cap on reliefs against general income (ITA 2007 "
        "s.24A(8)). Step 1 is total income (s.23 Step 1, "
        "total_income_charged_to_tax), which is already after employee "
        "contributions under a net pay arrangement (FA 2004 s.193(2)). "
        "Steps 3 and 4 deduct the other pension contributions given relief "
        "(ss.192-194). Together these are the person's own contributions "
        "up to relevant UK earnings (s.189(2): taxable employment income, "
        "including benefits and statutory pay, and trading profits). The "
        "basic amount can increase that limit only through relief at source "
        "(ss.190(3), 191(7)), which the model represents with gross personal "
        "pension contributions; employee contributions represent net pay. "
        "None is relieved from "
        "age 75 (s.188(3)(a)). The annual allowance limits tax-relieved "
        "saving through a charge, not the relief itself, so it is not applied "
        "here. Step 2 adds back payroll giving, which the model does not have."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax Act 2007 s. 24A(8)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/24A",
        ),
        dict(
            title="Finance Act 2004 ss. 188-190",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/190",
        ),
        dict(
            title="Finance Act 2004 s. 191(7)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/191",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc
        profits = person("self_employment_income", period)
        other_deductions = [
            deduction
            for deduction in p.income_tax.bases.taxable_self_employment_income_deductions
            if deduction != "loss_relief"
        ]
        profits_before_carry_forward = max_(
            0, profits - add(person, period, other_deductions)
        )
        total_income = person("total_income_charged_to_tax", period)
        # Relevant UK earnings (FA 2004 s.189(2)): employment income chargeable
        # to tax, including taxable benefits and statutory payments, and
        # trading profits chargeable to tax.
        relevant_earnings = (
            person("taxable_employment_income", period) + profits_before_carry_forward
        )
        # FA 2004 ss.190(3),191(7): only actual relief-at-source contributions
        # can use the basic-amount increase above relevant UK earnings.
        basic_amount_increase = min_(
            max_(
                0,
                p.income_tax.reliefs.pension_contribution.basic_amount
                - relevant_earnings,
            ),
            person("personal_pension_contributions", period),
        )
        relief_limit = relevant_earnings + basic_amount_increase
        under_age_limit = (
            person("age", period) < p.pensions.pension_contributions_relief_age_limit
        )
        relieved_contributions = (
            min_(person("pension_contributions", period), relief_limit)
            * under_age_limit
        )
        # Net pay contributions already came off total income at Step 1. With
        # contributions of zero or more they never exceed the contributions
        # relieved here (employee contributions up to taxable employment
        # income, which is part of relevant earnings). Either way the add-back
        # cancels the deduction: this is total income before them less every
        # relieved contribution, up to float32 rounding of a few pence on
        # incomes near £1m.
        not_yet_deducted = relieved_contributions - person(
            "net_pay_pension_relief", period
        )
        return max_(0, total_income - not_yet_deducted)

from policyengine_uk.model_api import *


class adjusted_total_income(Variable):
    value_type = float
    entity = Person
    label = "Adjusted total income"
    documentation = (
        "The base of the cap on reliefs against general income (ITA 2007 "
        "s.24A(8)). Step 1 is total income (s.23 Step 1): the taxable income "
        "components, with losses brought forward (loss_relief, a Step 2 "
        "relief the model deducts from trading profits) added back. Steps 3 "
        "and 4 deduct the pension contributions given relief (FA 2004 "
        "ss.192-194): the person's own contributions up to the greater of "
        "their relevant UK earnings and the basic amount (s.190), none from "
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
        losses_brought_forward_deducted = profits_before_carry_forward - person(
            "taxable_self_employment_income", period
        )
        total_income = (
            person("net_income_before_trade_loss_relief", period)
            + losses_brought_forward_deducted
        )
        relevant_earnings = max_(
            0, add(person, period, ["employment_income", "self_employment_income"])
        )
        relief_limit = max_(
            p.income_tax.reliefs.pension_contribution.basic_amount, relevant_earnings
        )
        under_age_limit = (
            person("age", period) < p.pensions.pension_contributions_relief_age_limit
        )
        relieved_contributions = (
            min_(person("pension_contributions", period), relief_limit)
            * under_age_limit
        )
        return max_(0, total_income - relieved_contributions)

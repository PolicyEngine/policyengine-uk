from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import (
    pension_contributions_relief_amount,
    relevant_uk_earnings,
)


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
        "up to relevant UK earnings (s.189(2): employment income, including "
        "statutory pay, less allowable expenses but before pension "
        "deductions, and trading profits before losses). The basic amount "
        "can increase that limit only through relief at source (ss.190(3), "
        "191(7)), which the model represents with gross personal pension "
        "contributions; employee contributions represent net pay. "
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
        hmrc = parameters(period).gov.hmrc
        total_income = person("total_income_charged_to_tax", period)
        # The same relief as pension_contributions_relief, on the same
        # relevant UK earnings (FA 2004 ss.189-191).
        relieved_contributions = pension_contributions_relief_amount(
            person("pension_contributions", period),
            relevant_uk_earnings(person, period, hmrc),
            person("personal_pension_contributions", period),
            person("age", period),
            hmrc,
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

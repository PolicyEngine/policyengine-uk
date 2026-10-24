from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import (
    pension_contributions_relief_amount,
    relevant_uk_earnings,
    trading_profits_before_losses,
)


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
        "ss.192-194): the person's own contributions up to relevant UK "
        "earnings (s.189(2): employment income, including statutory pay, "
        "less allowable expenses but before pension deductions, and trading "
        "profits before losses). The basic amount can "
        "increase that limit only through relief at source (ss.190(3), "
        "191(7)), which the model represents with gross personal pension "
        "contributions; employee contributions represent net pay. None is relieved from "
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
        losses_brought_forward_deducted = trading_profits_before_losses(
            person, period, hmrc
        ) - person("taxable_self_employment_income", period)
        total_income = (
            person("net_income_before_trade_loss_relief", period)
            + losses_brought_forward_deducted
        )
        # The same relief as pension_contributions_relief, on the same
        # relevant UK earnings (FA 2004 ss.189-191).
        relieved_contributions = pension_contributions_relief_amount(
            person("pension_contributions", period),
            relevant_uk_earnings(person, period, hmrc),
            person("personal_pension_contributions", period),
            person("age", period),
            hmrc,
        )
        return max_(0, total_income - relieved_contributions)

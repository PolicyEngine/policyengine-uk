from policyengine_uk.model_api import *


class property_finance_costs_relieved(Variable):
    value_type = float
    entity = Person
    label = "residential property finance costs relieved"
    documentation = (
        "The finance costs on which the tax reduction is given this year: the "
        "lowest of the relievable amount, the property profits, and adjusted "
        "total income (net income other than savings and dividend income, "
        "less the personal and blind person's allowances). Nil where the "
        "person uses the property allowance, since the allowance replaces the "
        "expenses and cannot be had with the reduction."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 274AA(2), (3) and (6)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BL",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BL",
        ),
    ]

    def formula(person, period, parameters):
        # Property profits for the year; s. 118 ITA 2007 loss relief, which
        # would come off them first, is not modelled.
        profits = person("taxable_property_income", period)
        # Adjusted total income (s. 274AA(6)): net income (after the Step 2
        # reliefs, such as gifts of shares to charity), less savings and
        # dividend income, less the allowances deducted at Step 3 of ITA 2007
        # s. 23, which are the personal and blind person's allowances. Gift
        # Aid, covenanted payments and pension contributions relieved at
        # source extend the basic rate band instead of reducing net income,
        # so they do not come off; pension_contributions_relief does not
        # separate contributions under net pay arrangements, which would.
        step_2_reliefs = add(
            person, period, ["charitable_investment_gifts", "other_deductions"]
        )
        step_3_allowances = add(
            person, period, ["personal_allowance", "blind_persons_allowance"]
        )
        adjusted_total_income = max_(
            0,
            person("adjusted_net_income", period)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
            - step_2_reliefs
            - step_3_allowances,
        )
        relieved = min_(
            person("property_finance_costs_relievable", period),
            min_(profits, adjusted_total_income),
        )
        return where(person("uses_property_allowance", period), 0, max_(relieved, 0))

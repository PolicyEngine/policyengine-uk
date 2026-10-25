from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


class trade_loss_relief_against_general_income(Variable):
    value_type = float
    entity = Person
    label = "Trade loss relief against general income"
    documentation = (
        "The part of the year's trading loss deducted in calculating net income "
        "for the loss-making year (ITA 2007 s.64(2)(a)): the whole loss, "
        "'limited in accordance with sections 24A and 25(4) and (5)' (s.65(1)), "
        "so to the s.24A cap and to the net income there is to deduct it from. "
        "Nothing lets a claim be restricted to keep the Personal Allowance in "
        "use. The model assumes the trade is commercial (s.66), that the person "
        "claims, and that the claim is for the loss-making year rather than "
        "the year before (s.64(2)(b)); the part it cannot use enters the "
        "opening loss_relief stock in later years under the model's "
        "same-trade carry-forward claim convention (s.83). Only a loss "
        "explicitly supplied for this year is a current loss. "
        "A current loss is recognised only under ordinary expense treatment; "
        "the trading allowance election compares the raw loss supplied for "
        "the tax year, before net-income and relief-cap limits, with the "
        "allowance's effective saving for all relevant trades together. "
        "Ordinary expenses win when the raw loss is larger; ties take the "
        "allowance. Comparing the raw loss can preserve an unused "
        "carry-forward when both choices give nil current net income "
        "(ITTOIA 2005 ss.783AF and 783AL; HMRC BIM86076)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax Act 2007 s. 64",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/64",
        ),
        dict(
            title="Income Tax Act 2007 s. 24A",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/24A",
        ),
    ]

    def formula(person, period, parameters):
        # Ordinary net-pay contributions already reduce Step 1 employment
        # income. That income cannot also consume a Step 2 trading loss.
        net_income = max_(
            0,
            person("net_income_before_trade_loss_relief", period)
            - person("net_pay_pension_relief", period),
        )
        current_loss = supplied_input(person, "trading_loss", period)
        if current_loss is None:
            current_loss = person.empty_array()
        # Allowance treatment cannot retain a current expense-generated loss
        # on another trade in the same individual's tax year.
        loss = where(
            person("trading_allowance_deduction", period) > 0,
            0,
            max_(0, current_loss),
        )
        return min_(
            loss,
            min_(person("income_tax_relief_cap", period), net_income),
        )

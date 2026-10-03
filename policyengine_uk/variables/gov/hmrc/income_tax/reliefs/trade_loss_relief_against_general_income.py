from policyengine_uk.model_api import *


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
        "the year before (s.64(2)(b)); the part it cannot use is carried "
        "forward only by entering it in loss_relief in later years (s.83)."
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
        net_income = max_(0, person("net_income_before_trade_loss_relief", period))
        return min_(
            person("trading_loss", period),
            min_(person("income_tax_relief_cap", period), net_income),
        )

from policyengine_uk.model_api import *


class ni_class_4_profits_before_losses(Variable):
    value_type = float
    entity = Person
    label = "Trade profits chargeable under ITTOIA 2005 Part 2 Chapter 2"
    documentation = (
        "Self-employment profit after capital allowances and the trading "
        "allowance, before loss relief: the profits chargeable to income tax "
        "under Chapter 2 of Part 2 of ITTOIA 2005 on which Class 4 NICs are "
        "charged. Capital allowances are a trade expense (CAA 2001 s. 247). "
        "The trading allowance recomputes the trade's profits (ITTOIA 2005 "
        "ss. 783AF and 783AI), so no Class 4 NICs are due on income it covers "
        "(HMRC BIM86052). Allowances in excess of profit do not create a loss "
        "here; supply any such loss through trading_loss."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992, s. 15(1)(b)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/15",
        ),
        dict(
            title="Capital Allowances Act 2001, s. 247",
            href="https://www.legislation.gov.uk/ukpga/2001/2/section/247",
        ),
        dict(
            title="HMRC Business Income Manual BIM86052",
            href="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim86052",
        ),
    ]

    def formula(person, period, parameters):
        profit = person("self_employment_income", period)
        capital_allowances = person("capital_allowances", period)
        # trading_allowance_deduction is the allowance's relief beyond actual
        # expenses and capital allowances, so the two do not stack.
        trading_allowance = person("trading_allowance_deduction", period)
        return max_(profit - capital_allowances - trading_allowance, 0)

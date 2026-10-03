from policyengine_uk.model_api import *


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    unit = GBP

    def formula(person, period, parameters):
        # Net income after trade loss relief against general income
        # (ITA 2007 s.24(1), s.64), which reduces it before the Personal
        # Allowance taper and every other adjusted net income test. Includes
        # basic income where a reform makes it taxable.
        return max_(
            0,
            person("net_income_before_trade_loss_relief", period)
            - person("trade_loss_relief_against_general_income", period),
        )

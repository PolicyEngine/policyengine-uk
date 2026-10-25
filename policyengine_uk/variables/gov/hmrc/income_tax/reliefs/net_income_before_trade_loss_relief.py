from policyengine_uk.model_api import *


class net_income_before_trade_loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Net income before trade loss relief against general income"
    documentation = (
        "The components of income left after the Step 2 reliefs the model "
        "deducts inside them (ITA 2007 s.23), before trade loss relief against "
        "general income: the income that relief can be deducted from "
        "(s.25(4)). Includes basic income where a reform makes it taxable."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )

    def formula(person, period, parameters):
        p = parameters(period)
        income = add(
            person, period, p.gov.hmrc.income_tax.adjusted_net_income_components
        )
        if p.gov.contrib.ubi_center.basic_income.interactions.include_in_taxable_income:
            income += person("basic_income", period)
        return income

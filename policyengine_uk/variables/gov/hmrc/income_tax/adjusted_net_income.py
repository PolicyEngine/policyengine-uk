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
        adjusted_net_income_components = parameters(
            period
        ).gov.hmrc.income_tax.adjusted_net_income_components

        # Find adjusted net income: net income, after trade loss relief
        # against general income (ITA 2007 s.24(1), s.64), which reduces it
        # before the Personal Allowance taper and every other ANI test.
        ani = add(person, period, adjusted_net_income_components) - person(
            "trade_loss_relief_against_general_income", period
        )

        # For basic income contributions, add basic income
        # Modifying param list directly is mutative, hence two-step process
        if parameters(
            period
        ).gov.contrib.ubi_center.basic_income.interactions.include_in_taxable_income:
            ani += person("basic_income", period)

        return max_(0, ani)

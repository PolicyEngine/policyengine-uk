from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import net_income_from_adjusted_net_income
from policyengine_uk.utils.supplied_inputs import supplied_input


class net_income(Variable):
    value_type = float
    entity = Person
    label = "Income before allowances and Gift Aid adjustments"
    documentation = (
        "The model's taxable income components after trade loss relief "
        "against general income and before pension relief, personal "
        "allowances and the Gift Aid adjustment to adjusted net income. "
        "Pension relief is deducted through allowances. Gift Aid extends rate limits and reduces "
        "adjusted net income, but does not reduce the income charged to tax."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, ss. 23 and 58",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/58",
    )
    unit = GBP

    def formula(person, period, parameters):
        # An explicitly supplied ANI already includes the s.58 adjustment.
        # Restore Gift Aid and pension relief for the pre-allowance base.
        # Ordinary cases compute the base directly to avoid subtracting and
        # re-adding relief through a float32 ANI cache.
        supplied_ani = supplied_input(person, "adjusted_net_income", period)
        if supplied_ani is not None:
            return net_income_from_adjusted_net_income(person, period, supplied_ani)
        # ITA 2007 ss.23 and 64 deduct trade loss relief at Step 2, before
        # personal allowances, Gift Aid's ANI adjustment and tax rate limits.
        return max_(
            0,
            person("net_income_before_trade_loss_relief", period)
            - person("trade_loss_relief_against_general_income", period),
        )

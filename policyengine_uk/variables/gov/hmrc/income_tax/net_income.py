from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


class net_income(Variable):
    value_type = float
    entity = Person
    label = "Income before personal allowances and Gift Aid adjustments"
    documentation = (
        "The model's taxable income components after trade loss relief "
        "against general income and before the Gift Aid adjustment "
        "to adjusted net income. Gift Aid extends rate limits and reduces "
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
        # Restore it for the taxable base, preserving direct ANI inputs at
        # zero Gift Aid. Ordinary cases compute the base directly to avoid
        # subtracting and re-adding a large gift through a float32 ANI cache.
        supplied_ani = supplied_input(person, "adjusted_net_income", period)
        if supplied_ani is not None:
            return supplied_ani + person("gift_aid_grossed_up", period)
        # ITA 2007 ss.23 and 64 deduct trade loss relief at Step 2, before
        # personal allowances, Gift Aid's ANI adjustment and tax rate limits.
        return max_(
            0,
            person("net_income_before_trade_loss_relief", period)
            - person("trade_loss_relief_against_general_income", period),
        )

from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


class net_income(Variable):
    value_type = float
    entity = Person
    label = "Income before personal allowances and Gift Aid adjustments"
    documentation = (
        "The model's taxable income components before the Gift Aid adjustment "
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
        components = parameters(
            period
        ).gov.hmrc.income_tax.adjusted_net_income_components
        income = add(person, period, components)
        if parameters(
            period
        ).gov.contrib.ubi_center.basic_income.interactions.include_in_taxable_income:
            income += person("basic_income", period)
        return max_(0, income)

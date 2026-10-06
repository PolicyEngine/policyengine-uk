from policyengine_uk.model_api import *


class deductible_property_finance_costs(Variable):
    value_type = float
    entity = Person
    label = "deductible residential property finance costs"
    documentation = (
        "The part of property_finance_costs still deducted in calculating "
        "property profits: all of it before 2017-18, then 75%, 50% and 25%, "
        "and none from 2020-21. The rest is relieved as a tax reduction."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 272A",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/272A",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.reliefs.property_finance_costs
        return (1 - p.disallowed_share) * person("property_finance_costs", period)
